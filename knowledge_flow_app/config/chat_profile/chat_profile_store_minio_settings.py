
from pydantic_settings import BaseSettings
from pydantic import Field

class ChatProfileMinioSettings(BaseSettings):
    minio_endpoint: str = Field(..., validation_alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(..., validation_alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(..., validation_alias="MINIO_SECRET_KEY")
    minio_chat_profile_bucket_name: str = Field(..., validation_alias="MINIO_CHAT_PROFILE_BUCKET_NAME")
    minio_secure: bool = Field(False, validation_alias="MINIO_SECURE")

    model_config = {
        "extra": "ignore"
    }