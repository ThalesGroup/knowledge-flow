from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, List

class BaseChatProfileStore(ABC):
    @abstractmethod
    def save_profile(self, profile_id: str, directory: Path) -> None:
        """
        Upload the full directory contents representing a chat profile.
        """
        pass

    @abstractmethod
    def delete_profile(self, profile_id: str) -> None:
        """
        Delete the stored chat profile data.
        """
        pass

    @abstractmethod
    def get_profile_description(self, profile_id: str) -> dict:
        """
        Retrieve the metadata (title/description) of the profile.
        """
        pass

    @abstractmethod
    def get_document(self, profile_id: str, document_name: str) -> BinaryIO:
        """
        Fetch a specific markdown document related to the profile.
        """
        pass
    
    @abstractmethod
    def list_markdown_files(self, profile_id: str) -> list[tuple[str, str]]:
        """
        Returns a list of tuples (filename, content) of all .md files for a profile.
        """
        pass

    @abstractmethod
    def list_profiles(self) -> List[dict]:
        pass