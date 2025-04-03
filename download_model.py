import os
import logging
import requests
import gzip
import shutil
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_file(url, local_filename):
    """
    Download a file with progress bar
    """
    # Create models directory if it doesn't exist
    os.makedirs(os.path.dirname(local_filename), exist_ok=True)
    
    # Check if file already exists
    if os.path.exists(local_filename):
        logger.info(f"File {local_filename} already exists, skipping download")
        return local_filename
        
    logger.info(f"Downloading {url} to {local_filename}")
    
    # Make HTTP request with stream=True
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    # Get file size from content-length header
    file_size = int(response.headers.get('content-length', 0))
    
    # Initialize progress bar
    progress = tqdm(total=file_size, unit='B', unit_scale=True, desc=local_filename)
    
    # Download with progress updates
    with open(local_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                progress.update(len(chunk))
    
    progress.close()
    
    return local_filename

def main():
    """Download TinyLlama model"""
    logger.info("Starting TinyLlama model download")
    
    # Model URL - using a lightweight GGUF version
    model_url = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    local_path = "models/tinyllama.gguf"
    
    try:
        # Download model file
        download_file(model_url, local_path)
        logger.info(f"TinyLlama model downloaded successfully to {local_path}")
        
    except Exception as e:
        logger.error(f"Error downloading TinyLlama model: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()