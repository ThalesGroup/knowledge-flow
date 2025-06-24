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

from typing import List
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


"""
This module defines the top level data structures used by controllers, processors
unit tests. It helps to decouple the different components of the application and allows 
to define clear workflows and data structures.
"""

class Status(str, Enum):
    SUCCESS = "success"
    IGNORED = "ignored"
    ERROR = "error"

class VectorizationResponse(BaseModel):
    """
    Represents the response of a vectorization operation. It is used to report
    the status of the vectorization process to the REST remote client.
    Attributes:
        filename (str): The name of the file being processed.
        status (str): The status of the vectorization operation.
        document_uid (str): A unique identifier for the document.
        chunks (int): The number of chunks embedded in the vector store.
        reason (Optional[str]): An optional reason for failure, if applicable.
    """
    status: Status
    chunks: int


class ProcessorConfig(BaseModel):
    """
    Configuration structure for a file processor. 
    Attributes:
        name (str): The name of the processor.
        prefix (str): The file extension this processor handles (e.g., '.pdf').
        class_path (str): Dotted import path of the processor class.
    """
    prefix: str = Field(..., description="The file extension this processor handles (e.g., '.pdf')")
    class_path: str = Field(..., description="Dotted import path of the processor class")

class Security(BaseModel):
    enabled: bool = True
    keycloak_url: str = "http://localhost:9080/realms/knowledge-flow"
    client_id: str = "knowledge-flow"
    authorized_origins: List[str] = ["http://localhost:5173"]

class ContentStorageConfig(BaseModel):
    type: str = Field(..., description="The storage backend to use (e.g., 'local', 'minio')")

class MetadataStorageConfig(BaseModel):
    type: str = Field(..., description="The storage backend to use (e.g., 'local', 'opensearch')")

class VectorStorageConfig(BaseModel):
    type: str = Field(..., description="The vector backend to use (e.g., 'opensearch', 'chromadb')")

class EmbeddingConfig(BaseModel):
    type: str = Field(..., description="The embedding backend to use (e.g., 'openai', 'azureopenai')")

class KnowledgeContextStorageConfig(BaseModel):
    type: str = Field(..., description="The storage backend to use (e.g., 'local', 'minio')")

class Configuration(BaseModel):
    security: Security
    input_processors: List[ProcessorConfig]
    output_processors: Optional[List[ProcessorConfig]] = None 
    content_storage: ContentStorageConfig = Field(..., description="Content Storage configuration")
    metadata_storage: MetadataStorageConfig = Field(..., description="Metadata storage configuration")
    vector_storage: VectorStorageConfig = Field(..., description="Vector storage configuration")
    embedding: EmbeddingConfig = Field(..., description="Embedding configuration")  
    knowledge_context_storage: KnowledgeContextStorageConfig = Field(...,description="Knowledge context storage configuration")
    knowledge_context_max_tokens: int = 50000
class KnowledgeContextDocument(BaseModel):
    id: str
    document_name: str
    document_type: str
    size: Optional[int] = None
    tokens: Optional[int] = Field(default=0)
class KnowledgeContext(BaseModel):
    id: str
    title: str
    description: str
    created_at: str
    updated_at: str
    documents: List[KnowledgeContextDocument]
    creator: str
    tokens: Optional[int] = Field(default=0)
