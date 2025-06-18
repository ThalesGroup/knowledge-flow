import json
import logging
import shutil
from pathlib import Path
from typing import BinaryIO, List
from .base_chat_profile_store import BaseChatProfileStore
logger = logging.getLogger(__name__)


class LocalChatProfileStore(BaseChatProfileStore):
    def __init__(self, root_path: Path):
        self.root_path = root_path

    def save_profile(self, profile_id: str, directory: Path) -> None:
        destination = self.root_path / profile_id
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(directory, destination)

    def delete_profile(self, profile_id: str) -> None:
        profile_dir = self.root_path / profile_id
        if profile_dir.exists():
            shutil.rmtree(profile_dir)

    def get_profile_description(self, profile_id: str) -> dict:
        desc_path = self.root_path / profile_id / "profile.json"
        if not desc_path.exists():
            raise FileNotFoundError("Chat profile description not found")
        return json.loads(desc_path.read_text(encoding="utf-8"))

    def get_document(self, profile_id: str, document_name: str) -> BinaryIO:
        doc_path = self.root_path / profile_id / "files" / document_name
        if not doc_path.exists():
            raise FileNotFoundError("Document not found in chat profile")
        return open(doc_path, "rb")
    
    def list_profiles(self) -> List[dict]:
        profiles = []
        for dir_path in self.root_path.iterdir():
            if dir_path.is_dir():
                profile_path = dir_path / "profile.json"
                if profile_path.exists():
                    try:
                        with open(profile_path, encoding="utf-8") as f:
                            profile_data = json.load(f)
                            profiles.append(profile_data)
                    except Exception as e:
                        logger.error(f"Failed to load profile at {profile_path}: {e}", exc_info=True)
        return profiles


    def list_markdown_files(self, profile_id: str) -> list[tuple[str, str]]:
        """
        Returns a list of (filename, content) tuples for all markdown files in the profile's 'files' directory.
        """
        result = []
        files_path = self.root_path / profile_id / "files"
        if not files_path.exists():
            return result

        for file_path in files_path.glob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8")
                result.append((file_path.name, content))
            except Exception as e:
                logger.error(f"Failed to read markdown file {file_path}: {e}", exc_info=True)

        return result

    def delete_markdown_file(self, profile_id: str, document_id: str) -> None:
        file_path = self.root_path / profile_id / "files" / f"{document_id}.md"
        if file_path.exists():
            file_path.unlink()
