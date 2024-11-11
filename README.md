# Plagiarism Detection Platform

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v3.0.2-green.svg)
![MongoDB](https://img.shields.io/badge/mongodb-v4.6.1-green.svg)

A sophisticated plagiarism detection system that leverages advanced NLP techniques and vector similarity search to identify potential content matches and paraphrasing.

## 🌟 Features

- **Advanced Similarity Detection**
  - Vector-based content matching using state-of-the-art embeddings
  - Semantic similarity analysis
  - Paraphrase detection
  - TF-IDF based comparison

- **Multiple File Format Support**
  - PDF documents
  - Microsoft Word (DOC, DOCX)
  - Plain text (TXT)

- **Comprehensive Analysis**
  - Detailed similarity scores
  - Matched content segments highlighting
  - Source attribution
  - Exportable reports

- **User-Friendly Interface**
  - Drag-and-drop file upload
  - Interactive results visualization
  - Detailed report generation
  - Responsive design

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- MongoDB
- wkhtmltopdf (for PDF report generation)
- Virtual environment (recommended)

### Installation

1. Clone the repository:

   ```bash

   git clone https://github.com/yourusername/PlagiarismDetectionPlatform.git

   cd PlagiarismDetectionPlatform
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```


3. Install wkhtmltopdf for PDF report generation:

   - Ubuntu: ```bash sudo apt-get install wkhtmltopdf```
   - macOS (using Homebrew): ```bash brew install wkhtmltopdf```
   - Windows: Download from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html)


4. Set up MongoDB:

   Ensure MongoDB is installed and running locally or use MongoDB Atlas for cloud storage.
   Update the MongoDB connection URI in the environment configuration.


5. Running the Application:

   Start the Flask server: ```bash flask run```
   Open your browser and navigate to http://localhost:5000 to access the application.

### 📊 Report Generation

The platform generates detailed, interactive similarity reports with the following elements:

- Similarity Scores: Numeric similarity score based on vector comparison
- Highlighting: Highlights matched content within the document for easy review
- Source Citations: Cites sources of matched content
- Export Options: Downloadable PDF report for offline review and sharing

### 🌍 Deployment
This platform can be deployed on various cloud services, such as AWS, Heroku, or DigitalOcean. For production, ensure to:

- Configure MongoDB Atlas or another production-ready database.
- Set up environment variables securely.
- Use a web server like Gunicorn with Flask for handling production requests.

### 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

### 💼 Target Users
This platform is designed for:

- Academic Institutions: For maintaining academic integrity.
- Researchers and Students: To verify originality in submissions.
- Content Publishers: To ensure originality in published content.

### 👏 Acknowledgments

- Flask for the backend framework
- MongoDB for data storage
- Sentence Transformers and FAISS for similarity search
- wkhtmltopdf for report generation in PDF format
