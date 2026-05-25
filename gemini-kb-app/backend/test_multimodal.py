import os
import uuid
from vector_store import VectorDB
from dotenv import load_dotenv

load_dotenv()

def test_multimodal():
    db = VectorDB(db_path="./test_chroma_db")
    db.clear()
    
    image_path = "i:/Mark/my-kb/raw/烘培食譜/助教筆記/messageImage_1693059968899.jpg"
    if not os.path.exists(image_path):
        print(f"Test image not found: {image_path}")
        return

    print(f"Indexing image: {image_path}")
    description = db.add_image_document(
        image_path=image_path,
        metadata={"source": image_path, "filename": "test_image.jpg"},
        doc_id=str(uuid.uuid4())
    )
    print(f"Generated Description: {description[:100]}...")

    print("\nQuerying with visual description...")
    query = "一張關於烘焙或是筆記的照片"
    results = db.query(query, n_results=1)
    
    if results['documents'] and results['documents'][0]:
        print(f"Matched Document: {results['documents'][0][0][:100]}...")
        print(f"Matched Metadata: {results['metadatas'][0][0]}")
        print("SUCCESS: Image retrieved via multimodal embedding!")
    else:
        print("FAILURE: No results found.")

if __name__ == "__main__":
    test_multimodal()
