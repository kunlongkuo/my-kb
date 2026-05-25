import os
import threading
import chromadb
from sentence_transformers import SentenceTransformer
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Models for Multilingual Image/Text search
# TEXT_MODEL supports Traditional Chinese
# VISION_MODEL supports images and is aligned with the CLIP space
TEXT_MODEL_NAME = "sentence-transformers/clip-ViT-B-32-multilingual-v1"
VISION_MODEL_NAME = "sentence-transformers/clip-ViT-B-32"

class VectorDB:
    _text_model = None
    _vision_model = None
    _loading_lock = threading.Lock()
    is_ready = False

    @classmethod
    def get_models(cls):
        with cls._loading_lock:
            if cls._text_model is None:
                from sentence_transformers import SentenceTransformer
                import torch
                
                # Auto-detect optimal device
                if torch.cuda.is_available():
                    device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"
                print(f"--- 偵測到向量模型最佳裝置為：[{device}] ---")
                
                print(f"Initializing Text Model: {TEXT_MODEL_NAME} on {device}...")
                cls._text_model = SentenceTransformer(TEXT_MODEL_NAME, device=device)
                
                print(f"Initializing Vision Model: {VISION_MODEL_NAME} on {device}...")
                cls._vision_model = SentenceTransformer(VISION_MODEL_NAME, device=device)
                
                cls.is_ready = True
                print("All local AI models loaded successfully.")
            return cls._text_model, cls._vision_model

    def __init__(self, db_path="./chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="kb_collection",
            metadata={"hnsw:space": "cosine"}
        )
        # Models will be loaded on first use or via background thread

    def get_text_embedding(self, text):
        """Generate embedding for text content and normalize it."""
        text_model, _ = self.get_models()
        import numpy as np
        embedding = text_model.encode([text])[0]
        # Normalize to unit length for better cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding.tolist()

    def get_image_embedding(self, image_path):
        """Generate embedding for an image and normalize it."""
        _, vision_model = self.get_models()
        import numpy as np
        img = Image.open(image_path).convert("RGB")
        embedding = vision_model.encode([img])[0]
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding.tolist()

    def add_document(self, text, metadata, doc_id):
        """Add a text document to the vector store."""
        embedding = self.get_text_embedding(text)
        self.collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def add_image_document(self, image_path, metadata, doc_id):
        """Add an image document using local CLIP embedding."""
        # Local CLIP doesn't strictly need a text description to search by text,
        # but we store the filename as the "document" content.
        filename = os.path.basename(image_path)
        embedding = self.get_image_embedding(image_path)
        
        metadata["type"] = "image"
        metadata["filename"] = filename
        
        self.collection.add(
            embeddings=[embedding],
            documents=[f"Image: {filename}"],
            metadatas=[metadata],
            ids=[doc_id]
        )
        return f"Image indexed: {filename}"

    def query(self, query_text, n_results=20):
        """Query the vector store with text using local embedding."""
        query_embedding = self.get_text_embedding(query_text)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results

    def get_doc_count(self):
        """Return the number of documents in the collection."""
        return self.collection.count()

    def clear(self):
        """Clear all documents from the collection."""
        self.client.delete_collection("kb_collection")
        self.collection = self.client.get_or_create_collection(
            name="kb_collection",
            metadata={"hnsw:space": "cosine"}
        )
