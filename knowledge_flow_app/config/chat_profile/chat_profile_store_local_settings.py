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

from pathlib import Path
import os


class ChatProfileLocalSettings:
    def __init__(self):
        # Default local path unless overridden by env var
        env_value = os.getenv("LOCAL_CHAT_PROFILE_STORAGE_PATH")
        if env_value:
            self.root_path = Path(env_value).expanduser()
        else:
            self.root_path = Path.home() / ".fred" / "chat-profiles"

        self.root_path.mkdir(parents=True, exist_ok=True)
