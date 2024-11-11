from flask import render_template, request, flash, redirect, url_for, jsonify, send_from_directory
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
import logging

file_handler = FileHandler()
document_store = DocumentStore()


async def init_detector():
    db = await get_async_db()
    db_ops = DatabaseOperations(db)
    return SimilarityDetector(db_ops)


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
                
                file_path = file_handler.save_file(file)
                processed_result = file_handler.process_file(file_path)
                
                
                if isinstance(processed_result, dict):
                    if 'file_info' in processed_result:
                        
                        processed_file_name = os.path.basename(processed_result['file_info']['processed_file'])
                        processed_file_path = os.path.join('app', 'processed', processed_file_name)
                        
                        
                        try:
                            with open(processed_file_path, 'r', encoding='utf-8') as f:
                                text_content = f.read()
                        except FileNotFoundError:
                            
                            processed_file_path = os.path.join('processed', processed_file_name)
                            with open(processed_file_path, 'r', encoding='utf-8') as f:
                                text_content = f.read()
                    else:
                        raise ValueError("No file info found in processed result")
                else:
                    text_content = processed_result
                
                
                if isinstance(text_content, list):
                    text_content = ' '.join(str(item) for item in text_content)
                elif not isinstance(text_content, str):
                    text_content = str(text_content)
                
                
                vector_embedding = similarity_detector.get_text_embedding(text_content)
                
                
                document = Document(
                    user_id=PyObjectId(),  
                    filename=file.filename,
                    content=text_content,  
                    content_vector=vector_embedding.tolist(),  
                    file_type=file.filename.split('.')[-1],
                    processed_text=text_content  
                )
                
                
                db = await get_async_db()
                db_ops = DatabaseOperations(db)
                doc_id = await db_ops.create_document(document)
                
                
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
                    'current_dir': os.getcwd()  
                }), 500

                
        
        return render_template('upload.html')

    @app.route('/check-similarity/<doc_id>', methods=['GET'])
    async def check_similarity(doc_id):
        try:
            
            db = await get_async_db()
            db_ops = DatabaseOperations(db)
            
            
            target_doc = await db_ops.get_document(doc_id)
            if not target_doc:
                return jsonify({
                    'status': 'error',
                    'message': 'Document not found'
                }), 404

            
            similar_docs = await db_ops.find_similar_documents(
                vector=target_doc['content_vector'],
                threshold=0.3  
            )
            
            
            similar_docs = [doc for doc in similar_docs if str(doc['_id']) != doc_id]
            
            if similar_docs:
                
                similarity_data = similarity_detector.analyze_similarity(
                    target_doc['content'],  
                    similar_docs[0]['content']  
                )
                print(similarity_data)
                
                similarity_result = {
                    'document_id': str(similar_docs[0]['_id']),
                    'filename': similar_docs[0]['filename'],
                    'similarity_data': {
                        'overall_similarity': similarity_data['overall_similarity'],
                        'similarity_score': similarity_data['similarity_score'],
                        'sentence_similarity': similarity_data['sentence_similarity'],
                        'tfidf_similarity': similarity_data['tfidf_similarity'],
                        'document_similarity': similarity_data['document_similarity'],
                        'similarity_breakdown': similarity_data['similarity_breakdown']
                    },
                    'similarity_score': similarity_data['similarity_score'],
                    'created_at': datetime.utcnow(),
                    'similar_documents': [{
                        'id': str(doc['_id']),
                        'filename': doc['filename'],
                        'score': similarity_data['similarity_score'],
                        'matched_segments': similarity_data.get('matched_segments', [])
                    } for doc in similar_docs[:5]]  
                }
            else:
                similarity_result = {
                    'similarity_data': {
                        'overall_similarity': 0,
                        'similarity_score': 0,
                        'sentence_similarity': 0,
                        'tfidf_similarity': 0,
                        'document_similarity': 0,
                        'similarity_breakdown': {
                            'exact_matches': 0,
                            'high_similarity': 0,
                            'moderate_similarity': 0,
                            'low_similarity': 0
                        }
                    },
                    'created_at': datetime.utcnow(),
                    'similar_documents': []
                }

            
            return render_template(
                'similarity_results.html',
                target_document={
                    'id': str(target_doc['_id']),
                    'filename': target_doc['filename'],
                    'file_type': target_doc['file_type']
                },
                similarity_result=similarity_result
            )

        except Exception as e:
            logging.error(f"Error in check_similarity: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/generate-report/<doc_id>', methods=['GET'])
    async def generate_report(doc_id):
        try:
            
            db = await get_async_db()
            db_ops = DatabaseOperations(db)
            
            
            target_doc = await db_ops.get_document(doc_id)
            if not target_doc:
                return jsonify({
                    'status': 'error',
                    'message': 'Document not found'
                }), 404

            
            similar_docs = await db_ops.find_similar_documents(
                vector=target_doc['content_vector'],
                threshold=0.3
            )
            
            
            similar_docs = [doc for doc in similar_docs if str(doc['_id']) != doc_id]

            if similar_docs:
                
                similarity_data = similarity_detector.analyze_similarity(
                    target_doc['content'],  
                    similar_docs[0]['content']  
                )

                
                report_generator = ReportGenerator()
                report = report_generator.generate_report(
                    document_info={
                        'id': str(target_doc['_id']),
                        'name': target_doc['filename'],
                        'processed_at': target_doc.get('created_at', datetime.utcnow().isoformat()),
                        'file_type': target_doc['file_type']
                    },
                    similarity_data={
                        'overall_similarity': similarity_data['overall_similarity'],
                        'similarity_score': similarity_data['similarity_score'],
                        'sentence_similarity': similarity_data['sentence_similarity'],
                        'tfidf_similarity': similarity_data['tfidf_similarity'],
                        'document_similarity': similarity_data['document_similarity'],
                        'similarity_breakdown': similarity_data['similarity_breakdown'],
                        'matched_segments': similarity_data.get('matched_segments', []),
                        'similar_documents': [{
                            'id': str(doc['_id']),
                            'filename': doc['filename'],
                            'score': similarity_data['similarity_score']
                        } for doc in similar_docs[:5]]
                    }
                )

                
                html_path = report['html_path']
                report_filename = os.path.basename(html_path)
                report_url = f"/reports/html/{report_filename}"

                
                return redirect(report_url)

            else:
                flash('No similar documents found for comparison', 'warning')
                return redirect(url_for('check_similarity', doc_id=doc_id))

        except Exception as e:
            logging.error(f"Error in generate_report: {str(e)}")
            flash(f'Error generating report: {str(e)}', 'error')
            return redirect(url_for('check_similarity', doc_id=doc_id))

    
    @app.route('/reports/<type>/<filename>')
    def serve_report(type, filename):
        """Serve report files from the reports directory"""
        if type not in ['html', 'pdf']:
            return jsonify({
                'status': 'error',
                'message': 'Invalid report type'
            }), 400
            
        try:
            
            reports_dir = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'reports',
                type
            ))
            return send_from_directory(reports_dir, filename)
        except Exception as e:
            logging.error(f"Error serving report: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': f'Error serving report: {str(e)}'
            }), 500

    @app.route('/debug/documents', methods=['GET'])
    async def debug_documents():
        try:
            db = await get_async_db()
            db_ops = DatabaseOperations(db)
            
            
            await db_ops.print_vector_info()
            
            
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