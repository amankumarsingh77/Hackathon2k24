import pytest
import os
from app import create_app
from app.utils.file_handler import FileHandler
from app.utils.similarity_detector import SimilarityDetector
from app.utils.document_store import DocumentStore

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_upload_endpoint(client):
    
    test_content = "This is a test document for plagiarism detection."
    test_file_path = "test_document.txt"
    
    with open(test_file_path, "w") as f:
        f.write(test_content)
    
    
    with open(test_file_path, "rb") as f:
        response = client.post("/", data={
            "file": (f, "test_document.txt")
        })
    
    
    os.remove(test_file_path)
    
    assert response.status_code == 200
    
def test_similarity_detection():
    detector = SimilarityDetector()
    
    text1 = ["This is a test document for checking similarity."]
    text2 = ["This is another document for testing similarity detection."]
    
    result = detector.analyze_similarity(text1, text2)
    
    assert 'overall_similarity' in result
    assert 'tfidf_similarity' in result
    assert 'semantic_similarity' in result 