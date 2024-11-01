import os
import json
from typing import List, Dict, Optional
from datetime import datetime

class DocumentStore:
    def __init__(self, store_dir: str = 'app/document_store'):
        self.store_dir = store_dir
        self.index_file = os.path.join(store_dir, 'index.json')
        self._initialize_store()
    
    def _initialize_store(self):
        """Initialize document store directory and index"""
        if not os.path.exists(self.store_dir):
            os.makedirs(self.store_dir)
        
        if not os.path.exists(self.index_file):
            self._save_index({})
    
    def _load_index(self) -> Dict:
        """Load document index"""
        with open(self.index_file, 'r') as f:
            return json.load(f)
    
    def _save_index(self, index: Dict):
        """Save document index"""
        with open(self.index_file, 'w') as f:
            json.dump(index, f, indent=4)
    
    def add_document(self, doc_id: str, processed_text: List[str], 
                    metadata: Dict) -> str:
        """Add a processed document to the store"""
        index = self._load_index()
        
        # Create document entry
        doc_entry = {
            'id': doc_id,
            'added_at': datetime.now().isoformat(),
            'metadata': metadata,
            'file_path': f"{doc_id}.json"
        }
        
        # Save document content
        doc_path = os.path.join(self.store_dir, doc_entry['file_path'])
        with open(doc_path, 'w') as f:
            json.dump({
                'text': processed_text,
                'metadata': metadata
            }, f, indent=4)
        
        # Update index
        index[doc_id] = doc_entry
        self._save_index(index)
        
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a document from the store"""
        index = self._load_index()
        
        if doc_id not in index:
            return None
        
        doc_entry = index[doc_id]
        doc_path = os.path.join(self.store_dir, doc_entry['file_path'])
        
        with open(doc_path, 'r') as f:
            content = json.load(f)
            
        return {
            **doc_entry,
            'content': content['text']
        }
    
    def get_all_documents(self) -> List[Dict]:
        """Get all documents for comparison"""
        index = self._load_index()
        documents = []
        
        for doc_id in index:
            doc = self.get_document(doc_id)
            if doc:
                documents.append(doc)
        
        return documents 