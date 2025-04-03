
import logging
from typing import Dict, List
from langchain_core.prompts import PromptTemplate
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_openai import OpenAIEmbeddings, ChatOpenAI 
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import Chroma
from vector_store import VectorStore
from models import ChatHistory

class RAGEngine:
    def __init__(self):
        self.vector_store = VectorStore()
        self.logger = logging.getLogger(__name__)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=512
        )

    def process_query(self, query: str, user_id: int, session_id: str, 
                     chat_context: List[Dict] = None) -> Dict:
        """Process user query using RAG approach"""
        if not query or not user_id:
            return {
                "answer": "I apologize, but I couldn't process your request. Please try again.",
                "metadata": {"error": "Invalid input parameters"}
            }
            
        try:
            # Get Chroma collection
            collection_name = f"user_{user_id}_docs"
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.vector_store.persist_directory
            )

            # Prepare conversation memory
            memory = ConversationBufferMemory(
                memory_key="chat_history",
                output_key="answer",
                return_messages=True
            )

            if chat_context:
                for msg in chat_context[-5:]:  # Last 5 messages
                    memory.chat_memory.add_user_message(msg["content"]) \
                        if msg["is_user"] else \
                        memory.chat_memory.add_ai_message(msg["content"])

            # Create QA chain
            qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=vectorstore.as_retriever(),
                memory=memory,
                return_source_documents=True
            )

            # Get response
            response = qa_chain.invoke({"question": query})

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

            prompt = PromptTemplate.from_template(
                """Please provide a concise summary of this conversation, focusing on:
                - Main topics discussed
                - Key questions asked
                - Important information provided
                - Any decisions or conclusions reached

                Conversation:
                {messages}

                Keep the summary to 2-3 sentences."""
            )

            formatted_prompt = prompt.format(messages="\n".join(messages))
            response = self.llm.predict(formatted_prompt)
            return response.strip()

        except Exception as e:
            self.logger.error(f"Error generating session summary: {str(e)}", exc_info=True)
            return "Unable to generate session summary due to an error."
