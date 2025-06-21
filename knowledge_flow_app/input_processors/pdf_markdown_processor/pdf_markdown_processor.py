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
from pathlib import Path
import pypdf
from pypdf.errors import PdfReadError
import requests
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling_core.types.doc import ImageRefMode
from knowledge_flow_app.input_processors.common.base_image_describer import BaseImageDescriber
from knowledge_flow_app.input_processors.common.base_input_processor import BaseMarkdownProcessor


logger = logging.getLogger(__name__)


class PdfMarkdownProcessor(BaseMarkdownProcessor):

    def __init__(self, image_describer: BaseImageDescriber | None = None):
        super().__init__()
        self.image_describer = image_describer
        
    def check_file_validity(self, file_path: Path) -> bool:
        """Checks if the PDF is readable and contains at least one page."""
        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                if len(reader.pages) == 0:
                    logger.warning(f"The PDF file {file_path} is empty.")
                    return False
                return True
        except PdfReadError as e:
            logger.error(f"Corrupted PDF file: {file_path} - {e}")
        except Exception as e:
            logger.error(f"Unexpected error while validating {file_path}: {e}")
        return False


    def extract_file_metadata(self, file_path: Path) -> dict:
        """Extracts metadata from the PDF file."""
        metadata = {"document_name": file_path.name}
        try:
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                info = reader.metadata or {}

                metadata.update({
                    "title": info.title.strip() if info.title else "Unknown",
                    "author": info.author.strip() if info.author else "Unknown",
                    "subject": info.subject.strip() if info.subject else "Unknown",
                    "num_pages": len(reader.pages),
                })
        except Exception as e:
            logger.error(f"Error extracting metadata from PDF: {e}")
            metadata["error"] = str(e)
        return metadata

    def convert_file_to_markdown(self, input_doc_path: Path, output_dir: Path) -> dict:

        output_markdown_path = output_dir / "output.md"
        try:
            # Initialize the DocumentConverter with PDF format options
            pipeline_options = PdfPipelineOptions()
            
            pipeline_options.images_scale = 2.0
            pipeline_options.generate_picture_images = True
            pipeline_options.generate_page_images=True
            # Prevent deprecated/empty behavior by disabling table image generation
            pipeline_options.generate_table_images = False
            # pipeline_options.do_picture_classification = True
            # pipeline_options.do_picture_description = True

            converter = DocumentConverter(
                format_options = {
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options
                    )
                }
            )

            # Convert the PDF document to a Document object
            result = converter.convert(input_doc_path)
            doc = result.document

            # Extract the pictures descriptions from the document
            pictures_desc = []
            if not doc.pictures:
                logger.info("No pictures found in document.")
            else: 
                for pic in doc.pictures:
                    base64 = pic.image.uri.path.split(',')[1]  # Extract base64 part from the data URI
                    if self.image_describer:
                        try:
                            description = self.image_describer.describe(base64)
                        except Exception as e:
                            logger.warning(f"Image description failed: {e}")
                            description = "Image could not be described."
                    else:
                        description = "Image description not available."
                    pictures_desc.append(description)

            # Generate the markdown file with placeholders for images
            doc.save_as_markdown(
                output_markdown_path,
                image_mode=ImageRefMode.PLACEHOLDER,
                image_placeholder="%%ANNOTATION%%"
            )

            # Replace placeholders with picture descriptions in the markdown file
            with open(output_markdown_path, "r", encoding="utf-8") as f:
                md_content = f.read()

            for desc in pictures_desc:
                md_content = md_content.replace("%%ANNOTATION%%", desc, 1)

            with open(output_markdown_path, "w", encoding="utf-8") as f:
                f.write(md_content)

        except Exception as fallback_error:
            logger.error(f"Fallback text extraction also failed: {fallback_error}")
            return {
                "doc_dir": str(output_dir),
                "md_file": None,
                "status": "error",
                "message": str(fallback_error),
            }

        return {
            "doc_dir": str(output_dir),
            "md_file": str(output_markdown_path),
            "status": "fallback_to_text",
            "message": "Conversion to plain text fallback succeeded.",
        }
