# Copyright Thales 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
from typing import Generator, List, Optional
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from knowledge_flow_app.application_context import ApplicationContext
from knowledge_flow_app.common.structures import Status
from knowledge_flow_app.services.output_processor_service import OutputProcessorService
from knowledge_flow_app.services.ingestion_service import IngestionService
from knowledge_flow_app.services.input_processor_service import InputProcessorService
from knowledge_flow_app.stores.content.content_storage_factory import get_content_store
from knowledge_flow_app.stores.metadata.metadata_storage_factory import get_metadata_store

logger = logging.getLogger(__name__)


class ProcessingProgress(BaseModel):
    """
    Represents the progress of a file processing operation. It is used to report in
    real-time the status of the processing pipeline to the REST remote client.
    Attributes:
        step (str): The current step in the processing pipeline.
        filename (str): The name of the file being processed.
        status (str): The status of the processing operation.
        document_uid (Optional[str]): A unique identifier for the document, if available.
    """

    step: str
    filename: str
    status: Status
    error: Optional[str] = None
    document_uid: Optional[str] = None


class StatusAwareStreamingResponse(StreamingResponse):
    """
    A custom StreamingResponse that allows for setting the HTTP status code
    based on the success of the content processing.
    This is useful for streaming responses where the final status may not be known
    until the generator has completed.
    """

    def __init__(self, content: Generator, all_success_flag: list, **kwargs):
        super().__init__(content, media_type="application/x-ndjson", **kwargs)
        self.all_success_flag = all_success_flag

    async def listen_for_close(self):
        await super().listen_for_close()
        # Set final HTTP status based on content
        if not self.all_success_flag[0]:
            self.status_code = 422  # or 207 if you prefer partial success


class IngestionController:
    """
    Controller responsible for uploading documents, executing the ingestion pipeline,
    and if all goes well, storing the documents in the configured backend storage.
    It also handles the metadata extraction and storage.
    """

    def __init__(self, router: APIRouter):
        self.context = ApplicationContext.get_instance()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ingestion_service = IngestionService()
        self.metadata_store = get_metadata_store()
        self.content_store = get_content_store()
        self.input_processor_service = InputProcessorService()
        self.output_processor_service = OutputProcessorService()

        # self.vectorization_pipeline = VectorizationPipeline()
        logger.info("IngestionController initialized.")

        @router.post("/process-files", tags=["Ingestion"])
        def stream_process(
            files: List[UploadFile] = File(...),
            metadata_json: str = Form(...),
        ) -> StreamingResponse:
            input_metadata = json.loads(metadata_json)
            # ✅ Preload: Call save_file_to_temp on all files before the generator runs
            # This is to ensure that the files are saved to temp storage before processing
            # and to avoid blocking the generator with file I/O operations.
            preloaded_files = []
            for file in files:
                input_temp_file = self.ingestion_service.save_file_to_temp(file)
                logger.info(f"File {file.filename} saved to temp storage at {input_temp_file}")
                preloaded_files.append((file.filename, input_temp_file))
            all_success_flag = [False]  # Track success across all files

            def event_generator() -> Generator[str, None, None]:
                for filename, input_temp_file in preloaded_files:
                    current_step = "metadata extraction"

                    try:
                        output_temp_dir = input_temp_file.parent.parent

                        # Step 2: Metadata extraction
                        metadata = self.input_processor_service.extract_metadata(input_temp_file, input_metadata)
                        logger.info(f"Metadata extracted for {filename}: {metadata}")
                        yield ProcessingProgress(step=current_step, status=Status.SUCCESS, document_uid=metadata["document_uid"], filename=filename).model_dump_json() + "\n"

                        # check if metadata is already known if so delete it to replace it and process the
                        # document again
                        if self.metadata_store.get_metadata_by_uid(metadata["document_uid"]):
                            logger.info(f"Metadata already exists for {filename}: {metadata}")
                            self.metadata_store.delete_metadata(metadata)
                            self.content_store.delete_content(metadata["document_uid"])

                        # Step 3: Processing
                        current_step = "document knowledge extraction"
                        self.input_processor_service.process(output_temp_dir, input_temp_file, metadata)
                        logger.info(f"Document processed for {filename}: {metadata}")
                        yield ProcessingProgress(step=current_step, status=Status.SUCCESS, document_uid=metadata["document_uid"], filename=filename).model_dump_json() + "\n"

                        # Step 4: Post-processing (optional)
                        current_step = "knowledge post processing"
                        vectorization_response = self.output_processor_service.process(output_temp_dir, input_temp_file, metadata)
                        logger.info(f"Post-processing completed for {filename}: {metadata} with chunks {vectorization_response.chunks}")
                        yield ProcessingProgress(step=current_step, status=vectorization_response.status, document_uid=metadata["document_uid"], filename=filename).model_dump_json() + "\n"

                        # Step 5: Metadata saving
                        current_step = "metadata saving"
                        self.metadata_store.save_metadata(metadata=metadata)
                        logger.info(f"Metadata saved for {filename}: {metadata}")
                        yield ProcessingProgress(step=current_step, status=Status.SUCCESS, document_uid=metadata["document_uid"], filename=filename).model_dump_json() + "\n"
                        # Step 6: Uploading to backend storage
                        current_step = "raw content saving"
                        self.content_store.save_content(metadata.get("document_uid"), output_temp_dir)
                        yield ProcessingProgress(step=current_step, status=Status.SUCCESS, document_uid=metadata["document_uid"], filename=filename).model_dump_json() + "\n"
                        # ✅ At least one file succeeded
                        all_success_flag[0] = True
                    except Exception as e:
                        logger.exception(f"Failed to process {file.filename}")
                        # Send detailed error message (safe for frontend)
                        error_message = f"{type(e).__name__}: {str(e).strip() or 'No error message'}"
                        yield ProcessingProgress(step=current_step, status=Status.ERROR, error=error_message, filename=file.filename).model_dump_json() + "\n"
                yield json.dumps({"step": "done", "status": Status.SUCCESS if all_success_flag[0] else "error"}) + "\n"

            return StatusAwareStreamingResponse(event_generator(), all_success_flag=all_success_flag)
