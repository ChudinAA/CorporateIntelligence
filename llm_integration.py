import os
import logging
import numpy as np
from flask import current_app
try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class LLMService:
    """
    Provides integration with Llama3.1 model for text generation and embeddings.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm = None
        self.embedding_model = None
        
        # Initialize LLM model
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Llama model."""
        try:
            model_path = current_app.config['LLM_MODEL_PATH']
            
            if Llama is None:
                self.logger.warning("llama-cpp-python is not installed. Using mock responses for development.")
                return
            
            if not os.path.exists(model_path):
                self.logger.warning(f"Model path {model_path} does not exist. Using mock responses for development.")
                return
            
            # Load the model
            self.llm = Llama(
                model_path=model_path,
                n_ctx=4096,  # Context window size
                n_batch=512,  # Batch size for prompt processing
                n_gpu_layers=-1,  # Use all available GPU layers
                verbose=False
            )
            
            self.logger.info(f"LLM model loaded from {model_path}")
            
            # For embeddings, we use the same model
            self.embedding_model = self.llm
            
        except Exception as e:
            self.logger.error(f"Error initializing LLM: {str(e)}", exc_info=True)
            self.logger.warning("Using mock responses for development.")
    
    def generate_response(self, prompt, max_tokens=1024, temperature=0.7):
        """
        Generate a response from the LLM.
        
        Args:
            prompt (str): The prompt to send to the model
            max_tokens (int): Maximum number of tokens to generate
            temperature (float): Sampling temperature (0.0-1.0)
            
        Returns:
            str: Generated response
        """
        try:
            if self.llm is None:
                # Return a mock response for development
                return self._mock_generate_response(prompt)
            
            # Generate response with the model
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["User:", "\n\n"],
                echo=False
            )
            
            # Extract the generated text
            generated_text = response['choices'][0]['text']
            return generated_text.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return "I'm sorry, I encountered an error while processing your request."
    
    def get_embedding(self, text):
        """
        Get embedding vector for a text.
        
        Args:
            text (str): Text to embed
            
        Returns:
            np.ndarray: Embedding vector
        """
        try:
            if self.embedding_model is None:
                # Return a mock embedding for development
                return self._mock_get_embedding(text)
            
            # Generate embedding with the model
            embedding = self.embedding_model.embed(text)
            
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}", exc_info=True)
            # Return a mock embedding as fallback
            return self._mock_get_embedding(text)
    
    def _mock_generate_response(self, prompt):
        """Generate a mock response for development purposes."""
        if "hello" in prompt.lower() or "hi" in prompt.lower():
            return "Hello! I'm your AI assistant. How can I help you today?"
        
        if "?" in prompt:
            return "That's a great question. Based on the information available, I'd say it depends on the specific context. Could you provide more details?"
        
        if len(prompt) < 20:
            return "I need a bit more information to provide a helpful response. Could you elaborate?"
        
        return "I understand your query. While I don't have all the specific details about your company's documents at the moment, I can tell you that typically this kind of information would be stored in your knowledge base. If you upload relevant documents, I can help you find more precise answers."
    
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
        embedding = np.random.randn(384)  # Default embedding dimension
        
        # Normalize the embedding
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
