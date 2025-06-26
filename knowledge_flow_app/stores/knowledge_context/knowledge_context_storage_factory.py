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

from knowledge_flow_app.application_context import ApplicationContext
from .local_knowledge_context_store import LocalKnowledgeContextStore
from .base_knowledge_context_store import BaseKnowledgeContextStore
from pathlib import Path


def get_knowledge_context_store() -> BaseKnowledgeContextStore:
    config = ApplicationContext.get_instance().get_config()
    backend_type = config.knowledge_context_storage.type

    if backend_type == "local":
        return LocalKnowledgeContextStore(Path(config.knowledge_context_storage.settings.local_path).expanduser())
    else:
        raise ValueError(f"Unsupported backend for chat profile: {backend_type}")
