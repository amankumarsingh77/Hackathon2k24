import PyPDF2
import docx
import nltk
from langdetect import detect
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string
import re


nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

class TextProcessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stopwords = set(stopwords.words('english'))
    
    def extract_text(self, file_path):
        """Extract text from different file formats"""
        file_extension = file_path.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return self._extract_from_pdf(file_path)
        elif file_extension in ['doc', 'docx']:
            return self._extract_from_docx(file_path)
        elif file_extension == 'txt':
            return self._extract_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def preprocess_text(self, text):
        """Main preprocessing pipeline"""
        
        try:
            language = detect(text)
            if language != 'en':
                raise ValueError(f"Unsupported language detected: {language}")
        except:
            raise ValueError("Language detection failed")
        
        
        text = text.lower()
        
        
        sentences = sent_tokenize(text)
        
        
        processed_sentences = []
        for sentence in sentences:
            processed_sentence = self._process_sentence(sentence)
            if processed_sentence:
                processed_sentences.append(processed_sentence)
        
        return processed_sentences
    
    def _process_sentence(self, sentence):
        """Process individual sentences"""
        
        sentence = re.sub(r'[^\w\s]', '', sentence)
        sentence = re.sub(r'\d+', '', sentence)
        
        
        words = word_tokenize(sentence)
        
        
        processed_words = []
        for word in words:
            if word not in self.stopwords and len(word) > 2:
                lemmatized = self.lemmatizer.lemmatize(word)
                processed_words.append(lemmatized)
        
        return ' '.join(processed_words)
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF files"""
        text = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        return '\n'.join(text)
    
    def _extract_from_docx(self, file_path):
        """Extract text from DOCX files"""
        doc = docx.Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        return '\n'.join(text)
    
    def _extract_from_txt(self, file_path):
        """Extract text from TXT files"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def chunk_text(self, sentences, chunk_size=5):
        """Split text into chunks for processing"""
        return [sentences[i:i + chunk_size] for i in range(0, len(sentences), chunk_size)] 