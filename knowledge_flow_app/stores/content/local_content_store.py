import logging
import shutil
from pathlib import Path
from typing import BinaryIO

from knowledge_flow_app.stores.content.base_content_store import BaseContentStore
logger = logging.getLogger(__name__)

class LocalStorageBackend(BaseContentStore):
    def __init__(self, destination_root: Path):
        self.destination_root = destination_root

    def save_content(self, document_uid: str, document_dir: Path) -> None:
        destination = self.destination_root / document_uid

        # 🧹 1. Clean old destination if it exists
        if destination.exists():
            shutil.rmtree(destination)

        # 🏗️ 2. Create destination
        destination.mkdir(parents=True, exist_ok=True)

        logger.info(f"📂 Created destination folder: {destination}")

        # 📦 3. Copy all contents
        for item in document_dir.iterdir():
            target = destination / item.name
            if item.is_dir():
                shutil.copytree(item, target)
                logger.info(f"📁 Copied directory: {item} -> {target}")
            else:
                shutil.copy2(item, target)
                logger.info(f"📄 Copied file: {item} -> {target}")

        logger.info(f"✅ Successfully saved document {document_uid} to {destination}")

    def delete_content(self, document_uid: str) -> None:
        """
        Deletes the content directory for the given document UID.
        """
        destination = self.destination_root / document_uid

        if destination.exists() and destination.is_dir():
            shutil.rmtree(destination)
            logger.info(f"🗑️ Deleted content for document {document_uid} at {destination}")
        else:
            logger.warning(f"⚠️ Tried to delete content for document {document_uid}, but it does not exist at {destination}")


    def get_content(self, document_uid: str) -> BinaryIO:
        """
        Returns a file stream (BinaryIO) for the first file in the `input` subfolder.
        """
        input_dir = self.destination_root / document_uid / "input"
        if not input_dir.exists():
            raise FileNotFoundError(f"No input folder for document: {document_uid}")

        files = list(input_dir.glob("*"))
        if not files:
            raise FileNotFoundError(f"No file found in input folder for document: {document_uid}")

        return open(files[0], "rb")

    def get_markdown(self, document_uid: str) -> str:
        """
        Returns the content of the `output/output.md` file as a UTF-8 string.
        """
        md_path = self.destination_root / document_uid / "output" / "output.md"
        if not md_path.exists():
            raise FileNotFoundError(f"Markdown not found for document: {document_uid}")

        try:
            return md_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading markdown file for {document_uid}: {e}")
            raise

