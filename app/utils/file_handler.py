import os
import filetype
from werkzeug.utils import secure_filename
from datetime import datetime
from .text_processor import TextProcessor
from .document_store import DocumentStore
import uuid

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
UPLOAD_FOLDER = 'app/uploads'
PROCESSED_FOLDER = 'app/processed'

class FileHandler:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.document_store = DocumentStore()
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    @staticmethod
    def validate_file_type(file):
        
        file_content = file.read()
        file.seek(0)  
        
        
        if file.filename.endswith('.txt'):
            try:
                file_content.decode('utf-8')
                return True
            except:
                return False
        
        
        kind = filetype.guess(file_content)
        if kind is None:
            return False
            
        valid_mimes = {
            'application/pdf',  
            'application/msword',  
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'  
        }
        
        return kind.mime in valid_mimes
    
    def process_file(self, file_path):
        """Process the uploaded file"""
        try:
            
            raw_text = self.text_processor.extract_text(file_path)
            processed_sentences = self.text_processor.preprocess_text(raw_text)
            
            
            doc_id = str(uuid.uuid4())
            metadata = {
                'original_file': file_path,
                'processed_at': datetime.now().isoformat(),
                'total_sentences': len(processed_sentences)
            }
            self.document_store.add_document(doc_id, processed_sentences, metadata)
            
            
            processed_file_path = self._save_processed_text(file_path, processed_sentences)
            
            
            return {
                'status': 'success',
                'message': 'File processed successfully',
                'file_info': {
                    'id': doc_id,
                    'name': os.path.basename(file_path),
                    'processed_file': os.path.basename(processed_file_path),
                    'sentences_count': len(processed_sentences),
                    'processed_at': metadata['processed_at']
                }
            }
            
        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")
    
    def _save_processed_text(self, original_file_path, processed_sentences):
        """Save processed text to a new file"""
        if not os.path.exists(PROCESSED_FOLDER):
            os.makedirs(PROCESSED_FOLDER)
            
        filename = os.path.basename(original_file_path)
        processed_filename = f"processed_{filename}.txt"
        processed_path = os.path.join(PROCESSED_FOLDER, processed_filename)
        
        with open(processed_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(processed_sentences))
            
        return processed_path
    
    @staticmethod
    def save_file(file):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        return file_path