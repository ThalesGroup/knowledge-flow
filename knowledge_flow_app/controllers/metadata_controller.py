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

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from knowledge_flow_app.common.structures import Status
from knowledge_flow_app.services.metadata_service import MetadataService
from knowledge_flow_app.stores.content.content_storage_factory import get_content_store
from threading import Lock

logger = logging.getLogger(__name__)

lock = Lock()


class GetDocumentsMetadataResponse(BaseModel):
    """
    Response model for the endpoint that returns several documents' metadata.

    The 'documents' field is a list of flexible dictionaries,
    allowing for various document metadata structures.
    """

    status: str
    documents: List[Dict[str, Any]]


class DeleteDocumentMetadataResponse(BaseModel):
    """
    Response model for deleting a document's metadata.
    """

    status: str
    message: str


class GetDocumentMetadataResponse(BaseModel):
    """
    Response model for retrieving metadata for a single document.

    The 'metadata' field is a dictionary with arbitrary structure.
    """

    status: str
    metadata: Dict[str, Any]


class UpdateRetrievableRequest(BaseModel):
    """
    Request model used to update the 'retrievable' field of a document.
    """

    retrievable: bool


class UpdateDocumentRetrievableResponse(BaseModel):
    """
    Response model for updating the 'retrievable' field of a document.
    """

    status: str
    response: Any  # Can be a more specific type if needed


class MetadataController:
    """
    FastAPI controller for managing document metadata.

    Provides endpoints to:
    - List document metadata with optional filters
    - Retrieve metadata for a specific document
    - Update specific metadata fields (e.g., 'retrievable')

    This controller delegates all core logic to the MetadataService.
    """

    def __init__(self, router: APIRouter):
        self.service = MetadataService()
        self.content_store = get_content_store()

        @router.post(
            "/documents/metadata",
            tags=["Metadata"],
            summary="List document metadata, with optional filters. All documents if no filters are given.",
            description=(
                "Fetch metadata for documents.\n"
                "Provide an optional JSON body with filters.\n"
                "Example:\n"
                "{\n"
                '   "front_metadata": {"GBU": "SIX"},\n'
                '   "retrievable": true\n'
                "}\n"
                "If no filters are given, all documents are returned."
            ),
            response_model=GetDocumentsMetadataResponse,
        )
        def get_documents_metadata(filters: Dict[str, Any] = Body(default={})):
            """
            POST endpoint to retrieve metadata for all documents, with optional filters.

            Body:
            - Optional JSON filters.

            Returns:
            - **status**: "success"
            - **documents**: List of matching documents
            """
            try:
                result = self.service.get_documents_metadata(filters)
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch document metadata. Reason: {str(e)}")

        @router.get(
            "/document/{document_uid}",
            tags=["Metadata"],
            summary="Get metadata for a specific document",
            description=("Fetch metadata for a single document using its unique UID.\n\nThe returned metadata dictionary may contain any fields."),
            response_model=GetDocumentMetadataResponse,
        )
        def get_document_metadata(document_uid: str):
            """
            Endpoint to retrieve metadata for a single document.

            Path Parameters:
            - **document_uid**: The unique identifier for the document

            Returns:
            - **status**: "success" or "error"
            - **metadata**: A dictionary containing the document's metadata
            """
            return self.service.get_document_metadata(document_uid)

        @router.put(
            "/document/{document_uid}",
            tags=["Metadata"],
            summary="Update 'retrievable' field of a document",
            description=("Set the 'retrievable' flag in a document's metadata. This flag indicates whether the document can be queried or retrieved in downstream services."),
            response_model=UpdateDocumentRetrievableResponse,
        )
        def update_document_retrievable(document_uid: str, update: UpdateRetrievableRequest):
            """
            Endpoint to update the 'retrievable' field of a document.

            Path Parameters:
            - **document_uid**: The unique identifier for the document

            Body:
            - **retrievable** (bool): True or False

            Returns:
            - **status**: "success" or "error"
            - **response**: Raw response from the metadata store or service
            """
            return self.service.update_document_retrievable(document_uid, update)

        @router.delete(
            "/document/{document_uid}",
            tags=["Metadata"],
            summary="Delete document metadata",
            description=("Deletes the metadata associated with the given document UID. This operation is permanent and cannot be undone."),
            response_model=DeleteDocumentMetadataResponse,
        )
        def delete_document_metadata(document_uid: str):
            """
            Endpoint to delete metadata for a specific document.

            Path Parameters:
            - **document_uid**: The unique identifier for the document
            Returns:
            - **status**: "success" or "error"
            - **message**: Confirmation message
            """
            try:
                # Acquire the lock to ensure thread safety
                with lock:
                    # Check if the document exists in the metadata store

                    # Delete the document metadata and content
                    self.service.delete_document_metadata(document_uid)
                    self.content_store.delete_content(document_uid)
                    return DeleteDocumentMetadataResponse(status=Status.SUCCESS, message=f"Metadata for document {document_uid} has been deleted.")
            except Exception as e:
                logger.error(f"Failed to delete document metadata: {e}")
                logger.exception(e)
                raise HTTPException(status_code=500, detail=f"Failed to delete document metadata: {str(e)}")
