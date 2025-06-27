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
from fastapi import HTTPException

from knowledge_flow_app.common.structures import Status
from knowledge_flow_app.stores.metadata.metadata_storage_factory import get_metadata_store

logger = logging.getLogger(__name__)


class MetadataService:
    """
    Service for managing metadata operations.
    ---------------------------------------
    This service is responsible for retrieving, deleting, and updating metadata from the configured metadata store.

    It also handles the retrieval of documents based on filters and the update of document retrievability.
    """

    def __init__(self):
        self.metadata_store = get_metadata_store()

    def get_documents_metadata(self, filters_dict: dict) -> dict:
        """
        Retrieves documents metadata based on the provided filters.
        The filters_dict can contain various keys to filter the documents.
        """
        documents = self.metadata_store.get_all_metadata(filters_dict)
        logger.info(f"Documents metadata retrieved fore {filters_dict} : {documents}")
        return {"status": Status.SUCCESS, "documents": documents}

    def delete_document_metadata(self, document_uid: str) -> None:
        """
        Deletes the metadata for a specific document based on its UID.
        Raises a ValueError if the document UID is not found.
        """
        metadata = self.metadata_store.get_metadata_by_uid(document_uid)
        if not metadata:
            raise ValueError(f"No document found with UID {document_uid}")
        self.metadata_store.delete_metadata(metadata)

    def get_document_metadata(self, document_uid: str):
        """
        Retrieves metadata for a specific document based on its UID.
        Raises a ValueError if the document UID is not found.
        """
        if not document_uid:
            raise ValueError("Document UID cannot be empty")
        try:
            metadata = self.metadata_store.get_metadata_by_uid(document_uid)
            return {"status": Status.SUCCESS, "metadata": metadata}
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métadonnées: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def update_document_retrievable(self, document_uid: str, update):
        """
        Updates the 'retrievable' field of a document's metadata.
        This field indicates whether the document can be queried or retrieved in downstream services.
        """
        if not document_uid:
            raise ValueError("Document UID cannot be empty")
        try:
            response = self.metadata_store.update_metadata_field(document_uid=document_uid, field="retrievable", value=update.retrievable)
            return {"status": Status.SUCCESS, "response": response}
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour: {e}")
            raise HTTPException(status_code=500, detail=str(e))
