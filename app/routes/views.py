from flask import render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from app.utils.file_handler import FileHandler
from app.utils.similarity_detector import SimilarityDetector
from app.utils.document_store import DocumentStore
from app.utils.report_generator import ReportGenerator
import os

file_handler = FileHandler()
similarity_detector = SimilarityDetector()
document_store = DocumentStore()

def init_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    def upload_file():
        if request.method == 'POST':
            if 'file' not in request.files:
                return jsonify({
                    'status': 'error',
                    'message': 'No file selected'
                }), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({
                    'status': 'error',
                    'message': 'No file selected'
                }), 400
            
            if not file_handler.allowed_file(file.filename):
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid file format. Supported formats: PDF, DOC, DOCX, TXT'
                }), 400
            
            try:
                # Save and process the file
                file_path = file_handler.save_file(file)
                result = file_handler.process_file(file_path)
                return jsonify(result)
                
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
        
        return render_template('upload.html')

    @app.route('/check-similarity/<doc_id>', methods=['GET'])
    def check_similarity(doc_id):
        try:
            # Get the document to check (the one we want to check against others)
            target_doc = document_store.get_document(doc_id)
            if not target_doc:
                return jsonify({
                    'status': 'error',
                    'message': 'Document not found'
                }), 404

            # Get all documents
            all_docs = document_store.get_all_documents()
            
            # Filter out the target document and sort by date
            other_docs = [doc for doc in all_docs if doc['id'] != doc_id]
            other_docs.sort(key=lambda x: x['added_at'], reverse=True)
            
            # Get the most recent document
            if other_docs:
                most_recent_doc = other_docs[0]
                # Compare target document with the most recent one
                result = similarity_detector.analyze_similarity(
                    target_doc['content'],  # Source document (the one being checked)
                    most_recent_doc['content']  # Document to compare against
                )
                
                similarity_result = {
                    'document_id': most_recent_doc['id'],
                    'original_file': most_recent_doc['metadata']['original_file'],
                    'similarity_data': result
                }
            else:
                similarity_result = None

            return jsonify({
                'status': 'success',
                'target_document': {
                    'id': target_doc['id'],
                    'file': target_doc['metadata']['original_file']
                },
                'similarity_result': similarity_result
            })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/generate-report/<doc_id>', methods=['GET'])
    def generate_report(doc_id):
        try:
            # Get document and similarity data
            target_doc = document_store.get_document(doc_id)
            if not target_doc:
                return jsonify({
                    'status': 'error',
                    'message': 'Document not found'
                }), 404

            # Get all other documents
            other_docs = [doc for doc in document_store.get_all_documents() 
                         if doc['id'] != doc_id]

            if other_docs:
                # Join sentences into a single string for comparison
                target_text = ' '.join(target_doc['content'])
                comparison_text = ' '.join(other_docs[0]['content'])  # Compare with most recent doc

                # Get similarity results
                similarity_result = similarity_detector.analyze_similarity(
                    [target_text],  # Pass as a list of one string
                    [comparison_text]  # Pass as a list of one string
                )

                # Generate report
                report_generator = ReportGenerator()
                report = report_generator.generate_report(
                    document_info={
                        'id': target_doc['id'],
                        'name': os.path.basename(target_doc['metadata']['original_file']),
                        'processed_at': target_doc['added_at']
                    },
                    similarity_data=similarity_result
                )

                return jsonify({
                    'status': 'success',
                    'report': report
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'No documents available for comparison'
                }), 400

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500