from datetime import datetime, timezone
import logging
from typing import List, Tuple
from langchain_core.vectorstores import InMemoryVectorStore

from langchain.embeddings.base import Embeddings
from langchain.schema.document import Document

from knowledge_flow_app.common.utils import get_embedding_model_name
from knowledge_flow_app.output_processors.vectorization_processor.interfaces import BaseVectoreStore

logger = logging.getLogger(__name__)
class InMemoryLangchainVectorStore(BaseVectoreStore):
    """
    In-Memory langchain Vector Store.
    -------------------
    A simple and minimalistic in-memory vector store.
    It uses the langchain_community FAISS class.
    """
    def __init__(self, embedding_model: Embeddings):
        """
        Args:
            embedding_model (Embeddings): The embedding model to use for vectorization.
        """
        self.embedding_model = embedding_model
        self.vectorstore = InMemoryVectorStore(embedding=embedding_model)

    def add_documents(self, documents: List[Document]) -> None:
        """
        Add raw documents to the in-memory vector store.
        Embeddings will be computed internally by LangChain using the configured embedding model.
        Args:
            documents (List[Document]): List of documents to embed and store.
        """
        self.vectorstore.add_documents(documents)
        logger.info("✅ Documents added successfully to in memory store.")
        top_n = 3
        for index, (id, doc) in enumerate(self.vectorstore.store.items()):
            if index < top_n:
                # docs have keys 'id', 'vector', 'text', 'metadata'
                logger.debug(f"{id}: {doc['text']}")
            else:
                break

    def similarity_search_with_score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        return self.vectorstore.similarity_search_with_score(query, k=k)
        

    def similarity_search_with_score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        enriched = []

        for rank, (doc, score) in enumerate(results):
            doc.metadata["score"] = score
            doc.metadata["rank"] = rank
            doc.metadata["retrieved_at"] = datetime.now(timezone.utc).isoformat()
            doc.metadata["embedding_model"] = get_embedding_model_name(self.embedding_model)
            doc.metadata["vector_index"] = "in-memory"
            doc.metadata["token_count"] = len(doc.page_content.split())  # crude estimate
            enriched.append((doc, score))

        return enriched

