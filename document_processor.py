import os
import logging
import tempfile
from typing import List, Dict
import PyPDF2
import docx
import pandas as pd
from werkzeug.utils import secure_filename
from flask import current_app
from models import Document, DocumentChunk
from app import db
from vector_store import VectorStore
from openai_integration import OpenAIService

class DocumentProcessor:
    def __init__(self):
        self.vector_store = VectorStore()
        self.logger = logging.getLogger(__name__)

    def process_uploaded_file(self, file, user_id: int) -> Dict:
        """Process uploaded file and store in vector database"""
        try:
            if not self._is_allowed_file(file.filename):
                return {"success": False, "error": "File type not supported"}

            # Save and process file
            file_info = self._save_file(file, user_id)
            if not file_info["success"]:
                return file_info

            # Create document record
            document = self._create_document_record(file_info, user_id)

            # Extract and process text
            text = self._extract_text(file_info["file_path"], file_info["file_type"])
            if not text:
                return self._handle_extraction_error(document)

            # Create and store chunks
            chunks = self._process_chunks(text, document.id, user_id)
            if not chunks["success"]:
                return self._handle_chunking_error(document, chunks["error"])

            # Update document status
            document.processed = True
            db.session.commit()

            return {
                "success": True,
                "document_id": document.id,
                "chunks_count": len(chunks["chunks"]),
                "document_name": file_info["original_filename"]
            }

        except Exception as e:
            self.logger.error(f"Document processing error: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _save_file(self, file, user_id: int) -> Dict:
        """Save uploaded file and return file info"""
        try:
            original_filename = file.filename
            secure_name = secure_filename(original_filename)
            filename = f"{user_id}_{secure_name}"
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            file.save(file_path)

            return {
                "success": True,
                "file_path": file_path,
                "filename": filename,
                "original_filename": original_filename,
                "file_type": original_filename.rsplit('.', 1)[1].lower(),
                "file_size": os.path.getsize(file_path)
            }
        except Exception as e:
            return {"success": False, "error": f"File save error: {str(e)}"}

    def _create_document_record(self, file_info: Dict, user_id: int) -> Document:
        """Create document record in database"""
        document = Document(
            filename=file_info["filename"],
            original_filename=file_info["original_filename"],
            file_type=file_info["file_type"],
            file_size=file_info["file_size"],
            user_id=user_id,
            processed=False
        )
        db.session.add(document)
        db.session.commit()
        return document

    def _process_chunks(self, text: str, document_id: int, user_id: int) -> Dict:
        """Process text into chunks and store in vector database"""
        try:
            # Create chunks
            chunks = self._create_chunks(text)
            chunk_objects = []

            # Create chunk records
            for i, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_text=chunk_text,
                    chunk_index=i
                )
                db.session.add(chunk)
                chunk_objects.append(chunk)

            db.session.flush()

            # Prepare metadata for vector store
            metadata_list = [{
                "chunk_id": chunk.id,
                "document_id": document_id,
                "chunk_index": chunk.chunk_index
            } for chunk in chunk_objects]

            # Store in vector database
            if not self.vector_store.add_document_chunks(chunk_objects, metadata_list, user_id):
                raise Exception("Failed to store chunks in vector database")

            db.session.commit()
            return {"success": True, "chunks": chunk_objects}

        except Exception as e:
            db.session.rollback()
            return {"success": False, "error": str(e)}

    def _is_allowed_file(self, filename: str) -> bool:
        """Check if file type is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

    def _extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text from document based on file type"""
        try:
            extractors = {
                'pdf': self._extract_from_pdf,
                'txt': self._extract_from_txt,
                'docx': self._extract_from_docx,
                'xlsx': lambda x: self._extract_from_spreadsheet(x, 'xlsx'),
                'csv': lambda x: self._extract_from_spreadsheet(x, 'csv')
            }

            extractor = extractors.get(file_type)
            if not extractor:
                raise ValueError(f"Unsupported file type: {file_type}")

            return extractor(file_path)

        except Exception as e:
            self.logger.error(f"Text extraction error: {str(e)}")
            return None

    def _extract_from_pdf(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() for page in reader.pages)

    def _extract_from_txt(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    def _extract_from_docx(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)

    def _extract_from_spreadsheet(self, file_path: str, file_type: str) -> str:
        df = pd.read_excel(file_path) if file_type == 'xlsx' else pd.read_csv(file_path)
        return df.to_string(index=False)

    def _create_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Create chunks from text using smart splitting"""
        import re

        def split_into_sentences(text):
            return re.split(r'(?<=[.!?])\s+', text)

        sentences = split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(sentence)
            current_size += sentence_size + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _handle_extraction_error(self, document: Document) -> Dict:
        """Handle text extraction error"""
        document.processing_error = "Failed to extract text from document"
        db.session.commit()
        return {
            "success": False,
            "error": "Failed to extract text from document",
            "document_id": document.id
        }

    def _handle_chunking_error(self, document: Document, error: str) -> Dict:
        """Handle chunking error"""
        document.processing_error = f"Chunking error: {error}"
        db.session.commit()
        return {
            "success": False,
            "error": f"Failed to process document chunks: {error}",
            "document_id": document.id
        }