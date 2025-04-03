import json
import os
import logging
import numpy as np

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Service for interacting with OpenAI API for text generation and embeddings.
    """

    def __init__(self):
        """
        Initialize the OpenAI service with proper configuration and error handling.
        Sets up the OpenAI client and configures embedding dimensions based on the
        latest text-embedding-3-large model which has 3072 dimensions.
        """
        self.api_key = os.environ.get("OPENAI_API_KEY")

        if not self.api_key:
            logger.warning(
                "OpenAI API key not found in environment variables. Service will use fallback methods."
            )
            self.client = None
        else:
            try:
                # Initialize with timeout and proper error handling
                self.client = OpenAI(
                    api_key=self.api_key,
                    timeout=120.0,  # 120 second timeout for API calls
                    max_retries=3,  # Retry failed requests three times
                    request_timeout=60  # Request timeout in seconds
                )
                logger.info("OpenAI service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
                self.client = None

        # Update to the correct embedding dimension for text-embedding-3-large
        self.embedding_dimension = 3072  # Latest OpenAI embedding model dimension

    def generate_response(self,
                          prompt,
                          max_tokens=1024,
                          temperature=0.7,
                          system_prompt=None):
        """
        Generate a response using OpenAI's GPT-4o model.

        Args:
            prompt (str): The user prompt
            max_tokens (int): Maximum number of tokens to generate
            temperature (float): Sampling temperature (0.0-1.0)
            system_prompt (str): Optional system prompt for the model

        Returns:
            str: Generated response
        """
        try:
            # Validate parameters and client
            if not self.api_key or not self.client:
                logger.error(
                    "OpenAI API key not configured or client initialization failed"
                )
                return "Error: OpenAI service is not properly configured. Please check your API key."

            if not prompt or not isinstance(prompt, str):
                logger.warning(f"Invalid prompt type: {type(prompt)}")
                prompt = str(prompt) if prompt else "Hello"

            # Validate and sanitize parameters
            max_tokens = min(max(1, int(max_tokens)),
                             4000)  # Keep tokens in reasonable range
            temperature = min(max(0.0, float(temperature)),
                              1.0)  # Keep temperature in valid range

            # Build message array
            messages = []

            # Add system prompt if provided
            if system_prompt:
                if isinstance(system_prompt, str) and system_prompt.strip():
                    messages.append({
                        "role": "system",
                        "content": system_prompt.strip()
                    })
                else:
                    logger.warning("Invalid system prompt format, ignoring")
            else:
                # Default system prompt for general assistance
                messages.append({
                    "role":
                    "system",
                    "content":
                    "You are a helpful, professional AI assistant for a company knowledge system."
                })

            # Add user message
            messages.append({"role": "user", "content": prompt})

            # Make the API call with error handling
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Using GPT-4o mini model
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.95,
                    presence_penalty=0.0,
                    frequency_penalty=0.0)

                if not response or not response.choices or len(
                        response.choices) == 0:
                    raise ValueError("Empty response received from OpenAI API")

                return response.choices[0].message.content

            except Exception as api_error:
                logger.error(f"API call to OpenAI failed: {str(api_error)}")
                raise api_error

        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {str(e)}",
                         exc_info=True)
            return f"I'm sorry, I encountered an error while processing your request. Please try again later."

    def get_embedding(self, text):
        """
        Get embedding vector for a text using OpenAI's embeddings API.
        Uses the advanced text-embedding-3-large model for state-of-the-art semantic search.

        Args:
            text (str): Text to embed

        Returns:
            np.ndarray: Embedding vector
        """
        try:
            if not self.api_key:
                logger.warning(
                    "OpenAI API key not found, using mock embeddings")
                return self._mock_get_embedding(text)

            # Preprocess text for better embedding quality
            processed_text = self._preprocess_text_for_embedding(text)

            # Generate embedding using the most advanced model
            response = self.client.embeddings.create(
                input=processed_text,
                model=
                "text-embedding-3-large",  # Latest model with 3072 dimensions
                encoding_format="float")

            embedding = response.data[0].embedding
            return np.array(embedding, dtype=np.float32)

        except Exception as e:
            logger.error(f"Error generating embedding with OpenAI: {str(e)}",
                         exc_info=True)
            # Return a mock embedding as fallback
            return self._mock_get_embedding(text)

    def _preprocess_text_for_embedding(self, text):
        """
        Preprocess text before generating embeddings for better quality.

        Args:
            text (str): Original text

        Returns:
            str: Processed text
        """
        if not text:
            return ""

        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)

        # Basic text cleaning
        text = text.strip()

        # Replace multiple spaces with single space
        import re
        text = re.sub(r'\s+', ' ', text)

        # Limit text length if too long (OpenAI has token limits)
        max_chars = 8000  # Approximate character limit
        if len(text) > max_chars:
            text = text[:max_chars]

        return text

    def rag_prompt_with_context(self, user_query, context, chat_history=None):
        """
        Generate a response using RAG (Retrieval-Augmented Generation) approach.
        Uses OpenAI's GPT-4o to synthesize answers from retrieved document contexts.

        Args:
            user_query (str): User's question
            context (str): Retrieved context from documents
            chat_history (list, optional): List of previous messages

        Returns:
            str: Generated response
        """
        try:
            # Validate input and client
            if not self.api_key or not self.client:
                logger.error(
                    "OpenAI API key not configured or client initialization failed"
                )
                return "Error: OpenAI service is not properly configured for RAG processing."

            # Sanitize inputs
            if not user_query or not isinstance(user_query, str):
                user_query = str(
                    user_query
                ) if user_query else "Can you help me find information?"

            if not context or not isinstance(context, str):
                context = str(
                    context) if context else "No relevant documents found."

            # Prepare message array
            messages = []

            # System prompt for RAG - Enhanced for better retrieval handling
            system_prompt = """
            You are an AI assistant for a company knowledge base search system.
            Your purpose is to help users find relevant information from company documents.

            Guidelines:
            1. Answer questions based ONLY on the context provided. If information isn't in the context, say "I don't have enough information about that in the available documents."
            2. Be specific when citing information. Mention document names when referencing information.
            3. If the context contains partial or incomplete information, acknowledge this and provide what is available.
            4. Format your answers for readability when appropriate (bullet points, paragraphs).
            5. Use a professional, helpful tone appropriate for a corporate environment.
            6. For multi-part questions, address each part systematically.
            7. If the user asks about information that contradicts the context, prioritize what's in the context, but acknowledge the discrepancy.
            """

            messages.append({"role": "system", "content": system_prompt})

            # Add chat history if provided, but only if there's actual history
            if chat_history and isinstance(chat_history,
                                           list) and len(chat_history) > 0:
                # Only include recent history to avoid token limits (last 3-5 messages)
                recent_history = chat_history[-5:] if len(
                    chat_history) > 5 else chat_history

                for message in recent_history:
                    if not isinstance(message, dict):
                        continue

                    role = "user" if message.get("is_user",
                                                 False) else "assistant"
                    content = message.get("content", "")

                    if content and isinstance(content,
                                              str) and content.strip():
                        messages.append({
                            "role": role,
                            "content": content.strip()
                        })

            # Format context in a more structured way
            formatted_context = f"""
            RETRIEVED DOCUMENT INFORMATION:
            ```
            {context}
            ```

            Answer the user's question using ONLY the information in the retrieved documents above.
            If the documents don't contain the answer, acknowledge the limitations of the available information.
            """

            # Add context as a system message for better separation
            messages.append({"role": "system", "content": formatted_context})

            # Add user query as the final user message
            messages.append({"role": "user", "content": user_query})

            # Generate response with enhanced parameters and error handling
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Using GPT-4o mini model
                    messages=messages,
                    max_tokens=1024,
                    temperature=
                    0.4,  # Slightly reduced temperature for more focused answers
                    top_p=0.95,  # Added top_p for better quality
                    presence_penalty=0.1,  # Slight penalty to reduce repetition
                    frequency_penalty=0.1  # Slight penalty to reduce repetition
                )

                if not response or not response.choices or len(
                        response.choices) == 0:
                    raise ValueError("Empty response received from OpenAI API")

                return response.choices[0].message.content

            except Exception as api_error:
                logger.error(
                    f"RAG API call to OpenAI failed: {str(api_error)}")
                raise api_error

        except Exception as e:
            logger.error(f"Error processing RAG query with OpenAI: {str(e)}",
                         exc_info=True)
            return "I'm sorry, I encountered an error while processing your request. Please try again or refine your question."

    def summarize_chat(self, messages):
        """
        Generate a summary of a chat session using OpenAI's chat completions API.
        Creates a concise summary of the key points and topics discussed.

        Args:
            messages (list): List of chat messages with format [{'content': str, 'is_user': bool}, ...]

        Returns:
            str: Summary of the chat, 2-3 sentences long
        """
        try:
            # Validate inputs and client
            if not self.api_key or not self.client:
                logger.error(
                    "OpenAI API key not configured or client initialization failed"
                )
                return "Chat summary not available. Please configure the OpenAI service properly."

            # Validate message format
            if not messages or not isinstance(messages,
                                              list) or len(messages) < 2:
                logger.warning(
                    f"Invalid messages format for summarization: {type(messages)}"
                )
                return "Not enough messages to generate a meaningful summary."

            # Create a properly formatted chat history for the API with enhanced system prompt
            api_messages = [{
                "role":
                "system",
                "content":
                """You are a highly efficient summarization specialist.
                    Create a concise, informative summary of this conversation between a user and an AI assistant.
                    Focus on:
                    - Main topics and themes discussed
                    - Important questions asked by the user
                    - Key information provided by the assistant
                    - Any decisions or conclusions reached
                    - Action items or next steps if mentioned

                    Your summary should be 2-3 sentences and capture only the most significant points.
                    Be professional, clear, and focus on substance over style.
                    Avoid vague language like "various topics" - be specific about what was discussed.
                    """
            }]

            # Clean and convert message format to OpenAI's format
            chat_content = []
            msg_count = 0

            for msg in messages:
                if not isinstance(msg, dict):
                    continue

                # Extract message details
                is_user = msg.get("is_user", False)
                content = msg.get("content", "")

                # Skip empty messages
                if not content or not isinstance(content,
                                                 str) or not content.strip():
                    continue

                # Add to API messages
                role = "user" if is_user else "assistant"
                api_messages.append({"role": role, "content": content.strip()})

                # Add to chat content for length validation
                chat_content.append(
                    f"{'User' if is_user else 'Assistant'}: {content.strip()}")
                msg_count += 1

            # Check if we have enough messages to summarize
            if msg_count < 2:
                return "Not enough conversation content to summarize."

            # Add a final instruction to get the summary
            api_messages.append({
                "role":
                "user",
                "content":
                "Based on the conversation above, provide a brief, informative summary in 2-3 sentences."
            })

            # Make the API call with optimized parameters and error handling
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=api_messages,
                    max_tokens=256,
                    temperature=
                    0.3,  # Lower temperature for more focused, consistent summaries
                    top_p=0.95,
                    presence_penalty=0.0,
                    frequency_penalty=0.0)

                if not response or not response.choices or len(
                        response.choices) == 0:
                    raise ValueError("Empty response received from OpenAI API")

                # Get the summary from the response
                summary = response.choices[0].message.content.strip()

                # Validate the summary
                if not summary:
                    return "Unable to generate a summary for this conversation."

                return summary

            except Exception as api_error:
                logger.error(
                    f"Summary API call to OpenAI failed: {str(api_error)}")
                raise api_error

        except Exception as e:
            logger.error(
                f"Error generating chat summary with OpenAI: {str(e)}",
                exc_info=True)
            return "Unable to generate chat summary due to an error. Please try again later."

    def _mock_get_embedding(self, text):
        """Generate a mock embedding for development purposes."""
        # Generate a deterministic but seemingly random embedding based on the text
        import hashlib

        # Get hash of the text
        text_hash = hashlib.md5(text.encode()).hexdigest()

        # Convert hash to a seed for random number generation
        seed = int(text_hash, 16) % 10000
        np.random.seed(seed)

        # Generate mock embedding
        embedding = np.random.randn(self.embedding_dimension)

        # Normalize the embedding
        embedding = embedding / np.linalg.norm(embedding)

        return embedding
