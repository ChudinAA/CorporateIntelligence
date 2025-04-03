import os
import numpy as np
import logging
from flask import current_app
from vector_store import VectorStore
# Import both LLM services for flexibility
from llm_integration import LLMService
from openai_integration import OpenAIService
from models import Document, DocumentChunk, ChatHistory
from extensions import db

class RAGEngine:
    """Retrieval-Augmented Generation engine for knowledge search and response generation."""
    
    def __init__(self, app=None):
        self.vector_store = None
        self.llm_service = None
        self.logger = logging.getLogger(__name__)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.vector_store = VectorStore(app)
        # By user request, use local Llama model instead of OpenAI
        self.llm_service = LLMService()
        self.logger.info("Using local Llama model for LLM capabilities")
    
    def process_query(self, query, user_id, session_id, chat_context=None):
        """
        Process a user query using RAG approach.
        
        Args:
            query (str): User's question
            user_id (int): ID of the current user
            session_id (str): Current chat session ID
            chat_context (list, optional): Previous chat messages for context
            
        Returns:
            dict: Response with answer and metadata
        """
        try:
            # Get query embedding
            query_embedding = self.llm_service.get_embedding(query)
            
            # Retrieve relevant documents from vector store
            relevant_chunks = self.vector_store.similarity_search(
                query_embedding, 
                limit=5,
                user_id=user_id
            )
            
            # Prepare context from retrieved documents
            context_text = self._prepare_context(relevant_chunks)
            
            # Get chat history for context if available
            chat_history_text = ""
            if chat_context and len(chat_context) > 0:
                # Format last few messages as context
                chat_history_text = "\n".join([
                    f"{'User' if msg['is_user'] else 'Assistant'}: {msg['content']}"
                    for msg in chat_context[-5:]  # Use last 5 messages
                ])
            
            # Generate response with LLM
            # If using OpenAI, use the specialized RAG method
            if isinstance(self.llm_service, OpenAIService):
                # Format chat history for OpenAI format
                formatted_history = []
                if chat_context and len(chat_context) > 0:
                    for msg in chat_context[-5:]:  # Use last 5 messages
                        formatted_history.append({
                            'content': msg['content'],
                            'is_user': msg['is_user']
                        })
                
                response = self.llm_service.rag_prompt_with_context(
                    user_query=query, 
                    context=context_text,
                    chat_history=formatted_history
                )
            else:
                # Fall back to standard prompt method
                prompt = self._create_rag_prompt(query, context_text, chat_history_text)
                response = self.llm_service.generate_response(prompt)
            
            # Create metadata for response
            metadata = {
                "sources": [
                    {
                        "document_id": chunk.document_id,
                        "document_name": chunk.document.original_filename if chunk.document else "Unknown Document",
                        "chunk_id": chunk.id
                    } for chunk in relevant_chunks
                ]
            }
            
            return {
                "answer": response,
                "metadata": metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error in RAG processing: {str(e)}", exc_info=True)
            return {
                "answer": "I'm sorry, I encountered an error while processing your query. Please try again.",
                "metadata": {"error": str(e)}
            }
    
    def _prepare_context(self, document_chunks):
        """Prepare context text from retrieved document chunks."""
        if not document_chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(document_chunks, 1):
            doc_name = chunk.document.original_filename if chunk.document else "Unknown Document"
            context_parts.append(f"[Document {i}: {doc_name}]\n{chunk.chunk_text}\n")
        
        return "\n".join(context_parts)
    
    def _create_rag_prompt(self, query, context, chat_history=""):
        """Create a prompt for the LLM using retrieved context."""
        prompt = """You are an AI assistant for a company knowledge base search. Answer the question based on the provided context.
If you don't know the answer, simply say that you don't know, don't try to make up an answer.
Use a professional, helpful tone and format your answer clearly.

"""
        if chat_history:
            prompt += f"Chat History:\n{chat_history}\n\n"
        
        prompt += f"Context:\n{context}\n\n"
        prompt += f"Question: {query}\n"
        prompt += "Answer: "
        
        return prompt
    
    def generate_session_summary(self, session_id):
        """Generate a summary of the chat session."""
        try:
            # Fetch chat history
            chat_history = ChatHistory.query.filter_by(session_id=session_id).first()
            if not chat_history:
                return "No chat history found to summarize."
            
            messages = chat_history.messages.order_by('timestamp').all()
            if not messages or len(messages) < 2:  # Need at least one exchange
                return "Not enough conversation to summarize."
            
            # If using OpenAI, use specialized method
            if isinstance(self.llm_service, OpenAIService):
                # Format messages for OpenAI
                formatted_messages = []
                for msg in messages:
                    formatted_messages.append({
                        'content': msg.content,
                        'is_user': msg.is_user
                    })
                
                # Generate summary with OpenAI
                summary = self.llm_service.summarize_chat(formatted_messages)
            else:
                # Format messages for standard LLM
                conversation = "\n".join([
                    f"{'User' if msg.is_user else 'Assistant'}: {msg.content}"
                    for msg in messages
                ])
                
                # Create summarization prompt
                prompt = """Generate a concise summary of the following conversation between a user and an AI assistant.
Focus on the main topics discussed, key questions asked, and important information provided.
The summary should be around 2-3 sentences, highlighting the most important points.

Conversation:
"""
                prompt += conversation
                prompt += "\n\nSummary: "
                
                # Generate summary with LLM
                summary = self.llm_service.generate_response(prompt)
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating session summary: {str(e)}", exc_info=True)
            return "Unable to generate session summary due to an error."
