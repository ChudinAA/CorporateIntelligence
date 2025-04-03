import chromadb
import logging
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings
from flask import current_app

class VectorStore:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=current_app.config['VECTOR_DB_PATH'],
            settings=Settings(allow_reset=True)
        )

    def add_document_chunks(self, chunks, metadata_list, user_id):
        """Add document chunks to vector store"""
        try:
            # Get or create collection for user
            collection_name = f"user_{user_id}_docs"
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"user_id": user_id}
            )

            # Generate embeddings and add to collection
            texts = [chunk.chunk_text for chunk in chunks]
            embeddings = self.embeddings.embed_documents(texts)

            # Add to ChromaDB
            collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadata_list,
                ids=[f"chunk_{chunk.id}" for chunk in chunks]
            )

            return True

        except Exception as e:
            self.logger.error(f"Error adding chunks to vector store: {str(e)}")
            return False

    def similarity_search(self, query, user_id, limit=5):
        """Search for similar documents"""
        try:
            # Get user's collection
            collection_name = f"user_{user_id}_docs"
            collection = self.client.get_collection(collection_name)

            # Get query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit
            )

            return results

        except Exception as e:
            self.logger.error(f"Error in similarity search: {str(e)}")
            return None

    def delete_document(self, document_id, user_id):
        """Delete document chunks from store"""
        try:
            collection_name = f"user_{user_id}_docs"
            collection = self.client.get_collection(collection_name)

            # Delete chunks by document_id in metadata
            collection.delete(
                where={"document_id": document_id}
            )

            return True

        except Exception as e:
            self.logger.error(f"Error deleting document: {str(e)}")
            return False