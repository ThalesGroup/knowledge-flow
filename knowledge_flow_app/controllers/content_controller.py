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
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# --- Response Models ---
class DocumentContent(BaseModel):
    """
    Model representing a document's content and metadata.
    """

    uid: str
    file_name: str
    title: str = ""
    content: Any = None
    has_binary_content: bool = False
    content_type: str = "application/octet-stream"
    file_url: str = None
    modified: str = ""
    metadata: Dict[str, Any] = {}


class MarkdownContentResponse(BaseModel):
    content: str


class ContentController:
    """
    FastAPI controller for managing document content operations.
    """

    def __init__(self, router: APIRouter):
        """
        Initialize the controller with a FastAPI router and content service.
        """
        from knowledge_flow_app.services.content_service import ContentService

        self.service = ContentService()
        self._register_routes(router)

    def _register_routes(self, router: APIRouter):
        """
        Register all content-related routes with the provided router.
        """

        @router.get(
            "/markdown/{document_uid}",
            tags=["Content"],
            summary="Get a preview of the complete document in markdown format",
            description="Fetch complete document including content using its unique UID.",
            response_model=MarkdownContentResponse,
        )
        async def get_markdown_preview(document_uid: str):
            """
            Endpoint to retrieve a complete document including its content.
            """
            try:
                logger.info(f"Retrieving full document: {document_uid}")
                content = await self.service.get_markdown_preview(document_uid)
                return {"content": content}
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except FileNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception:
                logger.exception("Unexpected error in get_document_preview")
                raise HTTPException(status_code=500, detail="Internal server error")

        @router.get(
            "/raw_content/{document_uid}", tags=["Content"], summary="Download the original document content", description="Serves the raw file associated with the given UID as a downloadable stream."
        )
        async def download_document(document_uid: str):
            try:
                stream, file_name, content_type = await self.service.get_original_content(document_uid)

                return StreamingResponse(content=stream, media_type=content_type, headers={"Content-Disposition": f'attachment; filename="{file_name}"'})
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except FileNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except Exception:
                logger.exception("Unexpected error in download_document")
                raise HTTPException(status_code=500, detail="Internal server error")
