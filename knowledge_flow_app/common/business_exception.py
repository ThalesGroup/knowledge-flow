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


class BusinessException(Exception):
    """Base class for business-related errors."""

    pass


class ChatProfileError(Exception):
    """Base class for chat profile errors."""

    pass


class TokenLimitExceeded(ChatProfileError):
    pass


class DocumentProcessingError(ChatProfileError):
    def __init__(self, filename: str):
        super().__init__(f"Failed to process file '{filename}'")
        self.filename = filename


class ProfileNotFound(ChatProfileError):
    def __init__(self, profile_id: str):
        super().__init__(f"Profile '{profile_id}' not found")
        self.profile_id = profile_id


class ProfileDeletionError(ChatProfileError):
    pass


class DocumentDeletionError(ChatProfileError):
    pass


class DocumentNotFound(ChatProfileError):
    pass
