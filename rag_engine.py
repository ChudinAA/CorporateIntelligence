import logging
from typing import Dict, List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain.chains import ConversationalRetrievalQA
from langchain.memory import ConversationBufferMemory
from vector_store import VectorStore
from models import ChatHistory

class RAGEngine:
    def __init__(self):
        self.vector_store = VectorStore()
        self.logger = logging.getLogger(__name__)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.llm = OpenAI(model="gpt-4-turbo-preview", temperature=0.7)

    def process_query(self, query: str, user_id: int, session_id: str, 
                     chat_context: List[Dict] = None) -> Dict:
        """Process user query using RAG approach"""
        try:
            # Search for relevant documents
            search_results = self.vector_store.similarity_search(
                query=query,
                user_id=user_id,
                limit=5
            )

            if not search_results:
                return self._handle_no_results(query)

            # Prepare conversation memory
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

            if chat_context:
                for msg in chat_context[-5:]:  # Last 5 messages
                    memory.chat_memory.add_user_message(msg["content"]) \
                        if msg["is_user"] else \
                        memory.chat_memory.add_ai_message(msg["content"])

            # Create QA chain
            qa_chain = ConversationalRetrievalQA.from_llm(
                llm=self.llm,
                retriever=search_results,
                memory=memory,
                return_source_documents=True
            )

            # Get response
            response = qa_chain({"question": query})

            return {
                "answer": response["answer"],
                "metadata": {
                    "sources": [
                        {
                            "document_id": doc.metadata["document_id"],
                            "chunk_id": doc.metadata["chunk_id"]
                        } for doc in response["source_documents"]
                    ]
                }
            }

        except Exception as e:
            self.logger.error(f"Error in RAG processing: {str(e)}", exc_info=True)
            return {
                "answer": "I apologize, but I encountered an error while processing your query. Please try again.",
                "metadata": {"error": str(e)}
            }

    def _handle_no_results(self, query: str) -> Dict:
        """Handle case when no relevant documents are found"""
        return {
            "answer": "I couldn't find any relevant information in the available documents to answer your question. "
                     "Please try rephrasing your query or ensure relevant documents have been uploaded.",
            "metadata": {"sources": []}
        }

    def generate_session_summary(self, session_id: str) -> str:
        """Generate a summary of the chat session"""
        try:
            chat_history = ChatHistory.query.filter_by(session_id=session_id).first()
            if not chat_history or not chat_history.messages:
                return "No chat history found to summarize."

            messages = [
                f"{'User' if msg.is_user else 'Assistant'}: {msg.content}"
                for msg in chat_history.messages
            ]

            if len(messages) < 2:
                return "Not enough conversation to summarize."

            prompt = f"""Please provide a concise summary of this conversation, focusing on:
- Main topics discussed
- Key questions asked
- Important information provided
- Any decisions or conclusions reached

Conversation:
{messages}

Keep the summary to 2-3 sentences."""

            response = self.llm.predict(prompt)
            return response.strip()

        except Exception as e:
            self.logger.error(f"Error generating session summary: {str(e)}", exc_info=True)
            return "Unable to generate session summary due to an error."