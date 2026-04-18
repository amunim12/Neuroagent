import uuid

from pinecone import Pinecone

from app.agent.memory.embedder import embed_text
from app.config import settings


class LongTermMemory:
    """Persistent vector memory backed by Pinecone for semantic retrieval."""

    def __init__(self):
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = pc.Index(settings.PINECONE_INDEX_NAME)

    async def upsert(self, text: str, namespace: str, metadata: dict) -> None:
        """Store a document in the vector index."""
        vector = await embed_text(text)
        self.index.upsert(
            vectors=[{"id": str(uuid.uuid4()), "values": vector, "metadata": {**metadata, "text": text}}],
            namespace=namespace,
        )

    async def search(self, query: str, namespace: str, top_k: int = 5) -> list[str]:
        """Retrieve semantically similar documents."""
        vector = await embed_text(query)
        results = self.index.query(vector=vector, top_k=top_k, namespace=namespace, include_metadata=True)
        return [match["metadata"]["text"] for match in results.get("matches", [])]
