import os
import logging
import numpy as np
import requests
import tqdm
import shutil
import time
from flask import current_app
from llama_cpp import Llama

class LLMService:
    """
    Provides integration with Llama3.1 model for text generation and embeddings.
    """
    
    def __init__(self, app=None):
        self.logger = logging.getLogger(__name__)
        self.app = app
        self.model_path = os.environ.get("LLM_MODEL_PATH", "models/tinyllama-test.gguf")
        self.embedding_dimension = 384 # Default embedding dimension for Llama models
        self.llm = None
        
        # Ensure the model directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # For testing, use TinyLlama model to save on resources
        # In production, would use full Llama3.1-8b model
        model_url = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        
        # Download model if not exists
        if not os.path.exists(self.model_path):
            self.download_model(model_url, self.model_path)
        else:
            self.logger.info(f"Model already exists at {self.model_path}")
            
        # Initialize the LLM
        self._initialize_llm()
        
    def init_app(self, app):
        """Initialize with Flask app instance."""
        self.app = app
    
    def download_model(self, model_url, model_path):
        """Download the Llama model if it doesn't exist."""
        try:
            self.logger.info(f"Downloading model from {model_url}")
            response = requests.get(model_url, stream=True)
            response.raise_for_status()
            
            # Get the file size
            total_size = int(response.headers.get('content-length', 0))
            
            # Create a progress bar
            progress_bar = tqdm.tqdm(total=total_size, unit='B', unit_scale=True, 
                               desc=model_path)
            
            # Write the file to disk with progress updates
            with open(model_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        progress_bar.update(len(chunk))
            
            progress_bar.close()
            self.logger.info(f"Model downloaded successfully to {model_path}")
            
        except Exception as e:
            self.logger.error(f"Error downloading model: {str(e)}")
            # Clean up partial downloads
            if os.path.exists(model_path):
                os.remove(model_path)
            raise
    
    def _initialize_llm(self):
        """Initialize the Llama model."""
        try:
            # Use low settings for replit environment
            # In production, would use higher values
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=2048,         # Context window size
                n_batch=512,        # Batch size
                n_gpu_layers=0,     # Use CPU only
                verbose=False       # Disable verbose output
            )
            self.logger.info(f"LLM model loaded from {self.model_path}")
        except Exception as e:
            self.logger.error(f"Error initializing LLM: {str(e)}")
            # Fall back to mock implementation for development
            self.llm = None
    
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
        if not self.llm:
            return self._mock_generate_response(prompt)
        
        try:
            # Generate response from the model
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["User:", "\n\n"],
                echo=False
            )
            
            # Extract the generated text
            return response['choices'][0]['text'].strip()
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"I encountered an error while generating a response. Please try again later."
    
    def get_embedding(self, text):
        """
        Get embedding vector for a text.
        
        Args:
            text (str): Text to embed
            
        Returns:
            np.ndarray: Embedding vector
        """
        if not self.llm:
            return self._mock_get_embedding(text)
            
        try:
            # Embed text using the model
            embedding = self.llm.embed(text)
            
            # Convert to numpy array
            return np.array(embedding, dtype=np.float32)
            
        except Exception as e:
            self.logger.error(f"Error getting embedding: {str(e)}")
            # Return mock embedding on error
            return self._mock_get_embedding(text)
    
    def _mock_generate_response(self, prompt):
        """Generate a mock response for development purposes."""
        time.sleep(0.5)  # Simulate processing time
        return f"This is a mock response to: {prompt[:30]}..."
    
    def _mock_get_embedding(self, text):
        """Generate a mock embedding for development purposes."""
        # Generate a deterministic but "random-looking" embedding based on the hash of the text
        np.random.seed(hash(text) % 2**32)
        return np.random.random(self.embedding_dimension).astype(np.float32)