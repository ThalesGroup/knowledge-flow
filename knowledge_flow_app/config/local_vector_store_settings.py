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

# settings_minio.py

from pathlib import Path
import os


class LocalVectorStoreSettings:
    """
    Local vector store settings class.
    This class is responsible for managing the local vector store settings.
    The defauls is "~/.fred/knowledge/vectore-store".
    The path can be overridden by setting the "LOCAL_VECTOR_STORAGE_PATH" environment variable.
    """

    def __init__(self):
        env_value = os.getenv("LOCAL_VECTOR_STORAGE_PATH")
        if env_value:
            self.root_path = Path(env_value)
        else:
            self.root_path = Path.home() / ".fred" / "knowledge" / "vectore-store"

        # Ensure parent folder exists
        self.root_path.parent.mkdir(parents=True, exist_ok=True)
