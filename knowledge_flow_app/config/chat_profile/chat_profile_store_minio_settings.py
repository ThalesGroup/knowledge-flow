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


from pydantic_settings import BaseSettings
from pydantic import Field


class ChatProfileMinioSettings(BaseSettings):
    minio_endpoint: str = Field(..., validation_alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(..., validation_alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(..., validation_alias="MINIO_SECRET_KEY")
    minio_chat_profile_bucket_name: str = Field(..., validation_alias="MINIO_CHAT_PROFILE_BUCKET_NAME")
    minio_secure: bool = Field(False, validation_alias="MINIO_SECURE")

    model_config = {"extra": "ignore"}
