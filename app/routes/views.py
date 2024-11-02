from flask import render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from app.utils.file_handler import FileHandler
from app.utils.similarity_detector import SimilarityDetector
from app.utils.document_store import DocumentStore
from app.utils.report_generator import ReportGenerator
from app.utils.db_operations import DatabaseOperations
from app.config.database import get_async_db
from app.models.models import Document, PyObjectId
import asyncio
import os
from datetime import datetime

file_handler = FileHandler()
document_store = DocumentStore()

# Initialize database and detector
async def init_detector():
    db = await get_async_db()
    db_ops = DatabaseOperations(db)
    return SimilarityDetector(db_ops)

# Get event loop and create detector instance
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
similarity_detector = loop.run_until_complete(init_detector())

def init_routes(app):
    @app.route('/', methods=['GET', 'POST'])
    async def upload_file():
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
                processed_result = file_handler.process_file(file_path)
                
                # Extract content from processed result
                if isinstance(processed_result, dict):
                    if 'file_info' in processed_result:
                        # Get the processed file path and ensure it's relative to app directory
                        processed_file_name = os.path.basename(processed_result['file_info']['processed_file'])
                        processed_file_path = os.path.join('app', 'processed', processed_file_name)
                        
                        # Read the processed text file
                        try:
                            with open(processed_file_path, 'r', encoding='utf-8') as f:
                                text_content = f.read()
                        except FileNotFoundError:
                            # Try alternate path
                            processed_file_path = os.path.join('processed', processed_file_name)
                            with open(processed_file_path, 'r', encoding='utf-8') as f:
                                text_content = f.read()
                    else:
                        raise ValueError("No file info found in processed result")
                else:
                    text_content = processed_result
                
                # Ensure text_content is a string
                if isinstance(text_content, list):
                    text_content = ' '.join(str(item) for item in text_content)
                elif not isinstance(text_content, str):
                    text_content = str(text_content)
                
                # Get vector embedding
                vector_embedding = similarity_detector.get_text_embedding(text_content)
                
                # Create document for MongoDB
                document = Document(
                    user_id=PyObjectId(),  # Placeholder until user system is implemented
                    filename=file.filename,
                    content=text_content,  # The actual text content
                    content_vector=vector_embedding.tolist(),  # Vector embedding for similarity search
                    file_type=file.filename.split('.')[-1],
                    processed_text=text_content  # Same as content for now
                )
                
                # Save to MongoDB
                db = await get_async_db()
                db_ops = DatabaseOperations(db)
                doc_id = await db_ops.create_document(document)
                
                # Redirect to similarity results page
                return jsonify({
                    'status': 'success',
                    'message': 'File uploaded and processed successfully',
                    'document_id': doc_id,
                    'redirect_url': f'/check-similarity/{doc_id}'
                })
                
            except Exception as e:
                import traceback
                return jsonify({
                    'status': 'error',
                    'message': str(e),
                    'traceback': traceback.format_exc(),
                    'processed_result_type': str(type(processed_result)),
                    'processed_result_preview': str(processed_result)[:200],
                    'current_dir': os.getcwd()  # For debugging
                }), 500
        
        return render_template('upload.html')

    @app.route('/check-similarity/<doc_id>', methods=['GET'])
    async def check_similarity(doc_id):
        try:
            # Get database connection
            db = await get_async_db()
            db_ops = DatabaseOperations(db)
            
            # Get the target document from MongoDB
            target_doc = await db_ops.get_document(doc_id)
            if not target_doc:
                return jsonify({
                    'status': 'error',
                    'message': 'Document not found'
                }), 404

            # Get similar documents using vector search
            similar_docs = await db_ops.find_similar_documents(
                vector=target_doc['content_vector'],
                threshold=0.8  # Configurable similarity threshold
            )
            
            # Filter out the target document itself
            similar_docs = [doc for doc in similar_docs if str(doc['_id']) != doc_id]
            
            if similar_docs:
                # Compare target document with the most similar one
                result = similarity_detector.analyze_similarity(
                    target_doc['content'],  # Source document
                    similar_docs[0]['content']  # Most similar document
                )
                
                similarity_result = {
                    'document_id': str(similar_docs[0]['_id']),
                    'filename': similar_docs[0]['filename'],
                    'similarity_data': result,
                    'similarity_score': similar_docs[0].get('score', 0),
                    'created_at': datetime.utcnow(),
                    'similar_documents': [{
                        'id': str(doc['_id']),
                        'filename': doc['filename'],
                        'score': doc.get('score', 0),
                        'matched_segments': result.get('matched_segments', [])
                    } for doc in similar_docs[:5]]  # Return top 5 similar documents
                }
            else:
                similarity_result = {
                    'similarity_data': {
                        'overall_similarity': 0,
                        'semantic_similarity': 0,
                        'cosine_similarity': 0
                    },
                    'created_at': datetime.utcnow(),
                    'similar_documents': []
                }

            return render_template('similarity_results.html',
                                target_document={
                                    'id': str(target_doc['_id']),
                                    'filename': target_doc['filename'],
                                    'file_type': target_doc['file_type']
                                },
                                similarity_result=similarity_result)

        except Exception as e:
            import traceback
            return jsonify({
                'status': 'error',
                'message': str(e),
                'traceback': traceback.format_exc()
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

    @app.route('/debug/documents', methods=['GET'])
    async def debug_documents():
        try:
            db = await get_async_db()
            db_ops = DatabaseOperations(db)
            
            # Get vector info
            await db_ops.print_vector_info()
            
            # Get sample documents
            docs = await db_ops.get_document_vectors()
            
            return jsonify({
                'status': 'success',
                'documents': docs
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500