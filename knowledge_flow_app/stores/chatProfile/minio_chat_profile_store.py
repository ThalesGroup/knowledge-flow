import json
import logging
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, List

from minio import Minio
from minio.error import S3Error

from knowledge_flow_app.common.business_exception import ProfileDeletionError

from .base_chat_profile_store import BaseChatProfileStore

logger = logging.getLogger(__name__)

class MinioChatProfileStore(BaseChatProfileStore):
    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket_name: str, secure: bool):
        self.bucket_name = bucket_name
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )

        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' created.")

    def save_profile(self, profile_id: str, directory: Path) -> None:
        """
        Uploads the entire chat profile folder (including profile.json and files/) to MinIO.
        """
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                object_name = f"{profile_id}/{file_path.relative_to(directory)}"
                try:
                    self.client.fput_object(
                        self.bucket_name,
                        object_name,
                        str(file_path)
                    )
                    logger.info(f"Uploaded '{object_name}' to bucket '{self.bucket_name}'.")
                except S3Error as e:
                    logger.error(f"Failed to upload '{file_path}': {e}")
                    raise ValueError(f"Failed to upload '{file_path}': {e}")

    def delete_profile(self, profile_id: str) -> None:
        """
        Deletes all files under a chat profile ID from the bucket.
        """
        try:
            objects_to_delete = self.client.list_objects(self.bucket_name, prefix=f"{profile_id}/", recursive=True)
            for obj in objects_to_delete:
                self.client.remove_object(self.bucket_name, obj.object_name)
                logger.info(f"Deleted '{obj.object_name}' from bucket '{self.bucket_name}'.")
        except S3Error as e:
            logger.error(f"Failed to delete profile {profile_id}: {e}")
            raise ProfileDeletionError(f"Could not delete profile {profile_id}: {e}")

    def get_profile_description(self, profile_id: str) -> dict:
        """
        Retrieves the profile.json metadata from MinIO.
        """
        object_name = f"{profile_id}/profile.json"
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return json.loads(response.read().decode("utf-8"))
        except S3Error as e:
            logger.error(f"Failed to fetch profile.json for {profile_id}: {e}")
            raise FileNotFoundError(f"Metadata not found for chat profile: {profile_id}")

    def get_document(self, profile_id: str, document_name: str) -> BinaryIO:
        """
        Fetches a single markdown document from the files/ folder inside a profile.
        """
        object_name = f"{profile_id}/files/{document_name}"
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return BytesIO(response.read())
        except S3Error as e:
            logger.error(f"Failed to fetch document '{document_name}' for {profile_id}: {e}")
            raise FileNotFoundError(f"Document '{document_name}' not found in chat profile: {profile_id}")

    def list_markdown_files(self, profile_id: str) -> list[tuple[str, str]]:
        result = []
        prefix = f"{profile_id}/files/"
        try:
            for obj in self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True):
                if obj.object_name.endswith(".md"):
                    response = self.client.get_object(self.bucket_name, obj.object_name)
                    content = response.read().decode("utf-8")
                    filename = obj.object_name.split("/")[-1]
                    result.append((filename, content))
        except S3Error as e:
            logger.error(f"Error listing markdowns for profile {profile_id}: {e}")
        return result


    def list_profiles(self) -> List[dict]:
        """
        Liste les profils disponibles dans le bucket MinIO.
        Chaque profil doit avoir un fichier profile.json à la racine de son dossier.
        """
        profiles = []

        try:
            # Récupère les objets profile.json à la racine de chaque dossier de profil
            objects = self.client.list_objects(self.bucket_name, recursive=True)

            profile_json_paths = [
                obj.object_name for obj in objects
                if obj.object_name.endswith("profile.json") and obj.object_name.count("/") == 1
            ]

            for obj_path in profile_json_paths:
                try:
                    response = self.client.get_object(self.bucket_name, obj_path)
                    profile_data = json.loads(response.read().decode("utf-8"))
                    profiles.append(profile_data)
                except Exception as e:
                    logger.error(f"Erreur lors de la lecture de {obj_path} : {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Erreur lors de la liste des profils MinIO : {e}", exc_info=True)

        return profiles
    
    def delete_markdown_file(self, profile_id: str, document_id: str) -> None:
        key = f"{profile_id}/files/{document_id}.md"
        try:
            self.client.remove_object(self.bucket_name, key)
            logger.info(f"Deleted markdown file {key} from MinIO bucket {self.bucket_name}")
        except Exception as e:
            logger.warning(f"Could not delete markdown file {key}: {e}")