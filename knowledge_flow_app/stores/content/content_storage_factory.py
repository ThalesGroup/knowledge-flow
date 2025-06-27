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
from knowledge_flow_app.common.utils import validate_settings_or_exit
from knowledge_flow_app.config.content_store_local_settings import ContentStoreLocalSettings
from knowledge_flow_app.config.content_store_minio_settings import ContentStoreMinioSettings
from pathlib import Path

from knowledge_flow_app.stores.content.base_content_store import BaseContentStore
from knowledge_flow_app.stores.content.local_content_store import LocalStorageBackend
from knowledge_flow_app.stores.content.minio_content_store import MinioContentStore


def get_content_store() -> BaseContentStore:
    """
    Factory function to get the appropriate storage backend based on configuration.
    Returns:
        StorageBackend: An instance of the storage backend.
    """
    # Get the singleton application context and configuration
    config = ApplicationContext.get_instance().get_config()
    backend_type = config.content_storage.type

    if backend_type == "minio":
        settings = validate_settings_or_exit(ContentStoreMinioSettings, "MinIO Settings")
        return MinioContentStore(
            endpoint=settings.minio_endpoint, access_key=settings.minio_access_key, secret_key=settings.minio_secret_key, bucket_name=settings.minio_bucket_name, secure=settings.minio_secure
        )
    elif backend_type == "local":
        settings = ContentStoreLocalSettings()
        return LocalStorageBackend(Path(settings.root_path).expanduser())
    else:
        raise ValueError(f"Unsupported storage backend: {backend_type}")
