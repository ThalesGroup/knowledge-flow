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

from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from langchain.schema.document import Document
from pydantic import Field
from knowledge_flow_app.services.vector_search_service import VectorSearchService

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10


class DocumentSource(BaseModel):
    content: str
    file_path: str
    file_name: str
    page: Optional[int]
    uid: str
    agent_name: Optional[str] = None
    modified: Optional[str] = None

    # Required for frontend
    title: str
    author: str
    created: str
    type: str

    # Metrics & evaluation
    score: float = Field(..., description="Similarity score returned by the vector store (e.g., cosine distance).")
    rank: Optional[int] = Field(None, description="Rank of the document among the retrieved results.")
    embedding_model: Optional[str] = Field(None, description="Identifier of the embedding model used.")
    vector_index: Optional[str] = Field(None, description="Name of the vector index used for retrieval.")
    token_count: Optional[int] = Field(None, description="Approximate token count of the content.")

    # Optional usage tracking or provenance
    retrieved_at: Optional[str] = Field(None, description="Timestamp when the document was retrieved.")
    retrieval_session_id: Optional[str] = Field(None, description="Session or trace ID for auditability.")


class SearchResponseDocument(BaseModel):
    content: str
    metadata: dict


class VectorSearchController:
    """
    Controller responsible for handling vectorization and search requests.
    """

    def __init__(self, router: APIRouter):
        self.service = VectorSearchService()

        @router.post(
            "/vector/search",
            tags=["Vector Search"],
            summary="Search documents using vectorization",
            description="Search documents using vectorization. Returns a list of documents that match the query.",
            response_model=List[DocumentSource],
            operation_id="search_documents_using_vectorization",
        )
        def vector_search(request: SearchRequest):
            results = self.service.similarity_search_with_score(request.query, k=request.top_k)
            return [self._to_document_source(doc, score, rank) for rank, (doc, score) in enumerate(results, start=1)]

    def _to_document_source(self, doc: Document, score: float, rank: int) -> DocumentSource:
        metadata = doc.metadata
        return DocumentSource(
            content=doc.page_content,
            file_path=metadata.get("source", "Unknown"),
            file_name=metadata.get("document_name", "Unknown"),
            page=metadata.get("page", None),
            uid=metadata.get("document_uid", "Unknown"),
            agent_name=metadata.get("front_metadata", {}).get("agent_name", "Unknown agent"),
            modified=metadata.get("modified", "Unknown"),
            title=metadata.get("title", "Unknown"),
            author=metadata.get("author", "Unknown"),
            created=metadata.get("created", "Unknown"),
            type=metadata.get("category", "document"),
            score=score,
            rank=rank,
            embedding_model=str(metadata.get("embedding_model", "unknown_model")),
            vector_index=metadata.get("vector_index", "unknown_index"),
            token_count=metadata.get("token_count", None),
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            retrieval_session_id=metadata.get("retrieval_session_id"),
        )
