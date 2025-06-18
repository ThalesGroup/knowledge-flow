from datetime import datetime
import shutil
from typing import List
from uuid import uuid4
from pathlib import Path
import tempfile
import json

from fastapi import HTTPException, UploadFile
import tiktoken
import logging

from knowledge_flow_app.common.structures import ChatProfile, ChatProfileDocument
from knowledge_flow_app.services.input_processor_service import InputProcessorService
from knowledge_flow_app.stores.chatProfile.chat_profile_storage_factory import get_chat_profile_store
from knowledge_flow_app.application_context import ApplicationContext

logger = logging.getLogger(__name__)

MAX_TOKENS_PER_PROFILE = 40000

def count_tokens_from_markdown(md_path: Path) -> int:
    embedder = ApplicationContext.get_instance().get_embedder()

    try:
        model_name = embedder.embedding.model_name
        encoding = tiktoken.encoding_for_model(model_name)
    except (AttributeError, KeyError):
        encoding = tiktoken.get_encoding("cl100k_base")

    text = md_path.read_text(encoding="utf-8")
    return len(encoding.encode(text))

class ChatProfileService:
    def __init__(self):
        self.store = get_chat_profile_store()
        self.processor = InputProcessorService()

    async def list_profiles(self):
        raw_profiles = self.store.list_profiles()
        all_profiles = []

        for profile_data in raw_profiles:
            try:
                profile_data["created_at"] = profile_data.get("created_at", datetime.now().isoformat())
                profile_data["updated_at"] = profile_data.get("updated_at", datetime.now().isoformat())
                profile_data["user_id"] = profile_data.get("user_id", "local")
                profile_data["tokens"] = profile_data.get("tokens", 0)
                profile_data["creator"] = profile_data.get("creator", "system")

                documents = []
                if "documents" in profile_data:
                    documents = [ChatProfileDocument(**doc) for doc in profile_data["documents"]]

                profile = ChatProfile(
                    id=profile_data["id"],
                    title=profile_data.get("title", ""),
                    description=profile_data.get("description", ""),
                    created_at=profile_data["created_at"],
                    updated_at=profile_data["updated_at"],
                    creator=profile_data["creator"],
                    user_id=profile_data["user_id"],
                    tokens=profile_data["tokens"],
                    documents=documents
                )

                all_profiles.append(profile)
            except Exception as e:
                logger.error(f"Failed to parse profile: {e}", exc_info=True)

        return all_profiles

    async def create_profile(self, title: str, description: str, files_dir: Path) -> ChatProfile:
        profile_id = str(uuid4())

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            profile_dir = tmp_path / profile_id
            files_subdir = profile_dir / "files"
            files_subdir.mkdir(parents=True, exist_ok=True)

            documents = []
            total_tokens = 0

            for file in files_dir.iterdir():
                if file.is_file():
                    try:
                        processing_dir = tmp_path / f"{file.stem}_processing"
                        processing_dir.mkdir(parents=True, exist_ok=True)

                        input_metadata = {
                            "source_file": file.name,
                            "document_uid": file.stem
                        }

                        temp_input_file = processing_dir / file.name
                        shutil.copy(file, temp_input_file)

                        self.processor.process(
                            output_dir=processing_dir,
                            input_file=file.name,
                            input_file_metadata=input_metadata
                        )

                        output_md = next((processing_dir / "output").glob("*.md"), None)
                        if not output_md:
                            raise FileNotFoundError(f"No .md output found for {file.name}")

                        new_md_name = f"{file.stem}.md"
                        dest_path = files_subdir / new_md_name
                        shutil.move(str(output_md), dest_path)

                        token_count = count_tokens_from_markdown(dest_path)
                        total_tokens += token_count

                        if total_tokens > MAX_TOKENS_PER_PROFILE:
                            raise ValueError(f"Profile exceeds the {MAX_TOKENS_PER_PROFILE} token limit.")

                        documents.append(ChatProfileDocument(
                            id=file.stem,
                            document_name=file.name,
                            document_type=file.suffix[1:],
                            size=file.stat().st_size,
                            tokens=token_count
                        ))

                    except Exception as e:
                        logger.error(f"Failed to process file '{file.name}': {e}", exc_info=True)

            now = datetime.utcnow().isoformat()
            metadata = {
                "id": profile_id,
                "title": title,
                "description": description,
                "created_at": now,
                "updated_at": now,
                "creator": "system",
                "documents": [doc.model_dump() for doc in documents],
                "tokens": total_tokens,
                "user_id": "local"
            }

            (profile_dir / "profile.json").write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
            )

            self.store.save_profile(profile_id, profile_dir)

        return ChatProfile(**metadata)

    async def delete_profile(self, profile_id: str):
        self.store.delete_profile(profile_id)
        return {"success": True}
    
    async def get_profile_with_markdown(self, profile_id: str) -> dict:
        """
        Load profile metadata and associated markdown content.
        """
        try:
            profile_data = self.store.get_profile_description(profile_id)

            markdown = ""
            if hasattr(self.store, "list_markdown_files"):
                md_files = self.store.list_markdown_files(profile_id)
                for filename, content in md_files:
                    markdown += f"\n\n# {filename}\n\n{content}"

            return {
                "id": profile_data["id"],
                "title": profile_data.get("title", ""),
                "description": profile_data.get("description", ""),
                "markdown": markdown.strip()
            }

        except Exception as e:
            logger.error(f"Error loading profile with markdown: {e}")
            raise

    async def update_profile(self, profile_id: str, title: str, description: str, files: list[UploadFile]) -> ChatProfile:
        try:
            # Load and update base metadata
            metadata = self.store.get_profile_description(profile_id)
            metadata["title"] = title
            metadata["description"] = description
            metadata["updated_at"] = datetime.utcnow().isoformat()
            print(files)

            # Merge existing documents
            existing_documents = {doc["id"]: doc for doc in metadata.get("documents", [])}
            total_tokens = sum(doc.get("tokens", 0) for doc in existing_documents.values())

            processed_documents = []

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)

                for upload in files:
                    file_path = tmp_path / upload.filename
                    with open(file_path, "wb") as f:
                        f.write(await upload.read())

                    try:
                        # Process file
                        processing_dir = tmp_path / f"{file_path.stem}_processing"
                        processing_dir.mkdir(parents=True, exist_ok=True)

                        shutil.copy(file_path, processing_dir / file_path.name)

                        self.processor.process(
                            output_dir=processing_dir,
                            input_file=file_path.name,
                            input_file_metadata={
                                "source_file": file_path.name,
                                "document_uid": file_path.stem
                            }
                        )

                        md_output = next((processing_dir / "output").glob("*.md"), None)
                        if not md_output:
                            raise FileNotFoundError(f"No markdown generated for {file_path.name}")

                        token_count = count_tokens_from_markdown(md_output)
                        total_tokens += token_count

                        if total_tokens > MAX_TOKENS_PER_PROFILE:
                            raise ValueError("Token limit exceeded")

                        # Build doc object
                        doc = ChatProfileDocument(
                            id=file_path.stem,
                            document_name=file_path.name,
                            document_type=file_path.suffix[1:],
                            size=file_path.stat().st_size,
                            tokens=token_count
                        )

                        existing_documents[doc.id] = doc.model_dump()
                        processed_documents.append((doc.id, md_output))

                    except Exception as e:
                        logger.error(f"Failed to process {upload.filename}: {e}", exc_info=True)

                # Final metadata
                metadata["tokens"] = total_tokens
                metadata["documents"] = list(existing_documents.values())

                # Prepare full profile structure
                profile_dir = tmp_path / profile_id
                files_dir = profile_dir / "files"
                files_dir.mkdir(parents=True, exist_ok=True)

                # Copy existing md files (except overwritten ones)
                existing_filenames = [f"{doc_id}.md" for doc_id, _ in processed_documents]
                for filename, content in self.store.list_markdown_files(profile_id):
                    if filename not in existing_filenames:
                        (files_dir / filename).write_text(content, encoding="utf-8")

                # Add new md files
                for doc_id, md_file in processed_documents:
                    shutil.copy(md_file, files_dir / f"{doc_id}.md")

                # Write profile.json
                (profile_dir / "profile.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

                # Save using store
                self.store.save_profile(profile_id, profile_dir)

            return ChatProfile(**metadata)

        except Exception as e:
            logger.error(f"Failed to update profile {profile_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to update profile")

    async def delete_document(self, profile_id: str, document_id: str):
        try:
            # Load the current profile metadata
            metadata = self.store.get_profile_description(profile_id)

            # Remove the document from metadata
            updated_documents = [doc for doc in metadata.get("documents", []) if doc["id"] != document_id]
            metadata["documents"] = updated_documents
            metadata["updated_at"] = datetime.utcnow().isoformat()

            # Recalculate tokens
            total_tokens = 0
            for doc in updated_documents:
                try:
                    markdown_file = f"{doc['id']}.md"
                    with self.store.get_document(profile_id, markdown_file) as f:
                        content = f.read().decode("utf-8")
                        tokens = len(tiktoken.get_encoding("cl100k_base").encode(content))
                        doc["tokens"] = tokens
                        total_tokens += tokens
                except Exception as e:
                    logger.warning(f"Could not read markdown for token count: {e}")

            metadata["tokens"] = total_tokens

            # Delete markdown files
            if hasattr(self.store, "delete_markdown_file"):
                try:
                    self.store.delete_markdown_file(profile_id, document_id)
                except Exception as e:
                    logger.warning(f"Failed to delete markdown file for {document_id}: {e}")

            # Recreate profile directory
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir)
                profile_dir = tmp_path / profile_id
                files_dir = profile_dir / "files"
                files_dir.mkdir(parents=True, exist_ok=True)

                for doc in updated_documents:
                    filename = f"{doc['id']}.md"
                    try:
                        with self.store.get_document(profile_id, filename) as f:
                            content = f.read().decode("utf-8")
                            (files_dir / filename).write_text(content, encoding="utf-8")
                    except Exception as e:
                        logger.warning(f"Could not copy remaining file {filename}: {e}")

                # Write updated profile.json
                profile_path = profile_dir / "profile.json"
                profile_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

                # Save everything
                self.store.save_profile(profile_id, profile_dir)

            return {"success": True}

        except Exception as e:
            logger.error(f"Error deleting document '{document_id}' from profile '{profile_id}': {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to delete document '{document_id}'")
