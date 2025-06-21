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

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from knowledge_flow_app.common.business_exception import BusinessException, ChatProfileError, DocumentDeletionError, DocumentNotFound, DocumentProcessingError, ProfileDeletionError, ProfileNotFound, TokenLimitExceeded
from knowledge_flow_app.common.utils import log_exception
from knowledge_flow_app.services.chat_profile_service import ChatProfileService
import tempfile
from pathlib import Path


class UpdateChatProfileRequest(BaseModel):
    title: str
    description: str
class ChatProfileController:
    def __init__(self, router: APIRouter):
        self.service = ChatProfileService()
        self._register_routes(router)

    def _register_routes(self, router: APIRouter):
        
        @router.get("/chatProfiles/maxTokens")
        async def get_max_tokens():
            from knowledge_flow_app.application_context import ApplicationContext
            context = ApplicationContext.get_instance()
            return {"max_tokens": context.get_chat_profile_max_tokens()}

        @router.get("/chatProfiles")
        async def list_profiles():
            return await self.service.list_profiles()

        @router.get("/chatProfiles/{chatProfile_id}")
        async def get_profile(chatProfile_id: str):
            try:
                return await self.service.get_profile_with_markdown(chatProfile_id)
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="Profile not found")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to load profile: {str(e)}")

        @router.post("/chatProfiles")
        async def create_profile(
            title: str = Form(...),
            description: str = Form(...),
            files: list[UploadFile] = File(default=[])
        ):
            try:
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_path = Path(tmp_dir)
                    for f in files:
                        dest = tmp_path / f.filename
                        with open(dest, "wb") as out_file:
                            content = await f.read()
                            out_file.write(content)

                    profile = await self.service.create_profile(title, description, tmp_path)
                    return profile
            except TokenLimitExceeded:
                raise HTTPException(status_code=400, detail="Token limit exceeded")
            except DocumentProcessingError as e:
                raise HTTPException(status_code=500, detail=f"Could not process file: {e.filename}")
            except BusinessException as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                log_exception(e, "Unexpected error during profile creation")
                raise HTTPException(status_code=500, detail="Internal Server Error")

        @router.put("/chatProfiles/{chatProfile_id}")
        async def update_profile(
            chatProfile_id: str,
            title: str = Form(...),
            description: str = Form(...),
            files: list[UploadFile] = File(default=[])
        ):
            try:
                return await self.service.update_profile(chatProfile_id, title, description, files)
            except ProfileNotFound as e:
                raise HTTPException(status_code=404, detail=str(e))
            except TokenLimitExceeded as e:
                raise HTTPException(status_code=400, detail=str(e))
            except DocumentProcessingError as e:
                raise HTTPException(status_code=500, detail=f"Failed to process one or more documents: {e}")
            except Exception as e:
                log_exception(e, f"Unexpected error while updating profile {chatProfile_id}")
                raise HTTPException(status_code=500, detail="Unexpected server error during profile update.")

        @router.delete("/chatProfiles/{chatProfile_id}")
        async def delete_profile(chatProfile_id: str):
            try:
                return await self.service.delete_profile(chatProfile_id)
            except ProfileNotFound as e:
                raise HTTPException(status_code=404, detail=str(e))
            except ProfileDeletionError as e:
                raise HTTPException(status_code=500, detail=str(e))
            except ChatProfileError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                log_exception(e, f"Unexpected error while deleting chat profile {chatProfile_id}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @router.delete("/chatProfiles/{chatProfile_id}/documents/{document_id}")
        async def delete_document(chatProfile_id: str, document_id: str):
            try:
                return await self.service.delete_document(chatProfile_id, document_id)
            except ProfileNotFound as e:
                raise HTTPException(status_code=404, detail=str(e))
            except DocumentNotFound as e:
                raise HTTPException(status_code=404, detail=str(e))
            except DocumentDeletionError as e:
                raise HTTPException(status_code=500, detail=str(e))
            except Exception as e:
                log_exception(e, f"Unexpected error deleting document '{document_id}' from profile '{chatProfile_id}'")
                raise HTTPException(status_code=500, detail="Internal server error")