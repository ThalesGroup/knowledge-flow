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
