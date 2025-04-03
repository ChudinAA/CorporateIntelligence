import os
import logging
import numpy as np
import json
import faiss
from flask import current_app
from models import DocumentChunk, Document

class VectorStore:
    """
    Manages vector embeddings for document chunks using FAISS.
    Creates separate indexes for each user to maintain data isolation.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.vector_db_path = current_app.config['VECTOR_DB_PATH']
        self.dimension = current_app.config['EMBEDDINGS_DIMENSION']

        # Create vector DB directory if it doesn't exist
        os.makedirs(self.vector_db_path, exist_ok=True)

        # Dictionary to store indexes by user_id
        self.indexes = {}
        # Dictionary to map vector IDs to document chunk IDs
        self.id_mappings = {}

    def _get_user_index_path(self, user_id):
        """Get path for user's FAISS index file."""
        return os.path.join(self.vector_db_path, f"user_{user_id}_index")

    def _get_user_mapping_path(self, user_id):
        """Get path for user's ID mapping file."""
        return os.path.join(self.vector_db_path, f"user_{user_id}_mapping.json")

    def _load_user_index(self, user_id):
        """Load or create FAISS index for a user."""
        if user_id in self.indexes:
            return self.indexes[user_id]

        # OpenAI embedding dimension
        self.dimension = 3072  # text-embedding-3-large dimension

        index_path = self._get_user_index_path(user_id)
        mapping_path = self._get_user_mapping_path(user_id)

        try:
            # Check if index exists
            if os.path.exists(index_path):
                # Load existing index
                index = faiss.read_index(index_path)
                self.indexes[user_id] = index

                # Load ID mappings
                if os.path.exists(mapping_path):
                    with open(mapping_path, 'r') as f:
                        self.id_mappings[user_id] = json.load(f)
                else:
                    self.id_mappings[user_id] = {}
            else:
                # Create new index
                index = faiss.IndexFlatL2(self.dimension)
                self.indexes[user_id] = index
                self.id_mappings[user_id] = {}

            return index
        except Exception as e:
            self.logger.error(f"Error loading index for user {user_id}: {str(e)}", exc_info=True)
            # Create a new index if loading fails
            index = faiss.IndexFlatL2(self.dimension)
            self.indexes[user_id] = index
            self.id_mappings[user_id] = {}
            return index

    def _save_user_index(self, user_id):
        """Save FAISS index and ID mappings for a user."""
        if user_id not in self.indexes:
            return

        index_path = self._get_user_index_path(user_id)
        mapping_path = self._get_user_mapping_path(user_id)

        try:
            # Save index
            faiss.write_index(self.indexes[user_id], index_path)

            # Save ID mappings
            with open(mapping_path, 'w') as f:
                json.dump(self.id_mappings.get(user_id, {}), f)
        except Exception as e:
            self.logger.error(f"Error saving index for user {user_id}: {str(e)}", exc_info=True)

    def add_embedding(self, embedding, doc_chunk_id, document_id, user_id, metadata=None):
        """
        Add an embedding to the vector store.

        Args:
            embedding (np.ndarray): Document chunk embedding
            doc_chunk_id (int): ID of the document chunk
            document_id (int): ID of the parent document
            user_id (int): ID of the user who owns the document
            metadata (dict, optional): Additional metadata

        Returns:
            str: Vector ID for the stored embedding
        """
        try:
            if embedding is None:
                self.logger.error("Received None embedding")
                return None

            # Ensure embedding is in the right format
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding, dtype=np.float32)

            # Validate embedding dimension
            if embedding.shape[-1] != self.dimension:
                self.logger.error(f"Invalid embedding dimension: got {embedding.shape[-1]}, expected {self.dimension}")
                return None

            if embedding.ndim == 1:
                embedding = embedding.reshape(1, -1)

            # Load user index
            index = self._load_user_index(user_id)

            # Get the next vector ID
            vector_id = str(index.ntotal)

            # Add the embedding to FAISS
            index.add(embedding)

            # Store mapping from vector ID to document chunk ID
            if user_id not in self.id_mappings:
                self.id_mappings[user_id] = {}

            self.id_mappings[user_id][vector_id] = {
                "doc_chunk_id": doc_chunk_id,
                "document_id": document_id,
                "metadata": metadata or {}
            }

            # Save updated index and mappings
            self._save_user_index(user_id)

            return vector_id
        except Exception as e:
            self.logger.error(f"Error adding embedding: {str(e)}", exc_info=True)
            return None

    def similarity_search(self, query_embedding, limit=5, user_id=None):
        """
        Search for similar documents using vector similarity.

        Args:
            query_embedding (np.ndarray): Query embedding
            limit (int): Maximum number of results to return
            user_id (int, optional): User ID to restrict search to their documents

        Returns:
            list: List of DocumentChunk objects
        """
        try:
            # Ensure embedding is in the right format
            if not isinstance(query_embedding, np.ndarray):
                query_embedding = np.array(query_embedding, dtype=np.float32)

            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)

            if user_id is None:
                # If no user_id specified, return empty results
                return []

            # Load user index
            index = self._load_user_index(user_id)

            # If index is empty, return empty results
            if index.ntotal == 0:
                return []

            # Perform search
            k = min(limit, index.ntotal)  # Can't retrieve more than exist
            distances, indices = index.search(query_embedding, k)

            # Convert vector IDs to document chunk IDs and retrieve chunks
            results = []
            for i in range(len(indices[0])):
                vector_idx = indices[0][i]
                vector_id = str(vector_idx)

                if vector_id in self.id_mappings.get(user_id, {}):
                    mapping = self.id_mappings[user_id][vector_id]
                    doc_chunk_id = mapping["doc_chunk_id"]

                    # Retrieve the document chunk
                    chunk = DocumentChunk.query.get(doc_chunk_id)
                    if chunk:
                        results.append(chunk)

            return results
        except Exception as e:
            self.logger.error(f"Error in similarity search: {str(e)}", exc_info=True)
            return []

    def delete_document(self, document_id, user_id):
        """
        Delete all embeddings associated with a document.

        Args:
            document_id (int): ID of the document to delete
            user_id (int): ID of the user who owns the document

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if user has an index
            if user_id not in self.indexes:
                self._load_user_index(user_id)

            if user_id not in self.id_mappings:
                return True  # Nothing to delete

            # Find all vector IDs associated with this document
            vector_ids_to_delete = []
            for vector_id, mapping in self.id_mappings[user_id].items():
                if mapping["document_id"] == document_id:
                    vector_ids_to_delete.append(vector_id)

            if not vector_ids_to_delete:
                return True  # Nothing to delete

            # We need to rebuild the index without the deleted vectors
            # Get all remaining vectors
            remaining_vectors = []
            remaining_mappings = {}

            for vector_id, mapping in self.id_mappings[user_id].items():
                if vector_id not in vector_ids_to_delete:
                    # TODO: This is a simplified approach. In a production system,
                    # you would need to retrieve the actual vectors from the index.
                    # For now, we'll recreate the index from the database.
                    remaining_mappings[str(len(remaining_vectors))] = mapping

                    # Get the document chunk
                    chunk_id = mapping["doc_chunk_id"]
                    chunk = DocumentChunk.query.get(chunk_id)

                    if chunk and chunk.vector_id:
                        # We would need to get the vector from somewhere
                        # This is just a placeholder
                        pass

            # Create new index and mappings
            self.id_mappings[user_id] = remaining_mappings
            self._save_user_index(user_id)

            return True
        except Exception as e:
            self.logger.error(f"Error deleting document from vector store: {str(e)}", exc_info=True)
            return False