from typing import Dict, List, Optional
import json
from datetime import datetime
import os
from jinja2 import Environment, FileSystemLoader
import pdfkit
import matplotlib.pyplot as plt
import io
import base64
import logging
import matplotlib
matplotlib.use('Agg')  
import atexit

class ReportGenerator:
    def __init__(self, template_dir: str = 'app/templates/reports'):
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.report_dir = 'app/reports'
        self.logger = logging.getLogger(__name__)
        self._ensure_directories()
        
        
        atexit.register(self._cleanup)
    
    def _cleanup(self):
        """Cleanup resources"""
        plt.close('all')
    
    def _ensure_directories(self):
        """Ensure necessary directories exist"""
        os.makedirs(self.report_dir, exist_ok=True)
        os.makedirs(os.path.join(self.report_dir, 'html'), exist_ok=True)
        os.makedirs(os.path.join(self.report_dir, 'pdf'), exist_ok=True)
    
    def generate_report(self, 
                       document_info: Dict, 
                       similarity_data: Dict,
                       web_sources: Optional[Dict] = None) -> Dict:
        """Generate comprehensive plagiarism report"""
        try:
            
            charts = self._generate_charts(similarity_data)
            
            
            report_data = {
                'document': document_info,
                'similarity': similarity_data,
                'web_sources': web_sources or {},
                'charts': charts,
                'generated_at': datetime.now().isoformat(),
                'highlighted_text': self._generate_text_highlights(
                    similarity_data.get('matched_segments', [])
                )
            }
            
            
            report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            html_path = self._save_html_report(report_id, report_data)
            
            
            try:
                pdf_path = self._generate_pdf(html_path, report_id)
            except Exception as e:
                self.logger.warning(f"PDF generation failed: {str(e)}")
                pdf_path = None
            
            response = {
                'report_id': report_id,
                'html_path': html_path,
                'pdf_path': pdf_path,
                'summary': self._generate_summary(report_data)
            }
            
            return response
            
        except Exception as e:
            logging.error(f"Error generating report: {str(e)}")
            raise
    
    def _generate_charts(self, similarity_data: Dict) -> Dict:
        """Generate visualization charts"""
        charts = {}
        
        try:
            
            plt.figure(figsize=(8, 6))
            scores = [
                ('TF-IDF', similarity_data['tfidf_similarity']),
                ('Sentence', similarity_data['sentence_similarity']),
                ('Document', similarity_data['document_similarity']),
                ('Overall', similarity_data['overall_similarity'])
            ]
            
            plt.bar([s[0] for s in scores], [s[1] for s in scores])
            plt.title('Similarity Scores Distribution')
            plt.ylabel('Similarity Score')
            
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            charts['similarity_distribution'] = base64.b64encode(buffer.read()).decode()
            
        finally:
            plt.close('all')  
            
        return charts
    
    def _generate_text_highlights(self, matches: List[Dict]) -> List[Dict]:
        """Generate highlighted text comparisons"""
        highlighted_matches = []
        for match in matches:
            highlighted_matches.append({
                'source': match['source_text'],
                'target': match['matched_text'],
                'similarity': match['similarity'],
                'type': 'high' if match['similarity'] > 0.8 else 'moderate'
            })
        return highlighted_matches
    
    def _save_html_report(self, report_id: str, data: Dict) -> str:
        """Generate and save HTML report"""
        template = self.env.get_template('report_template.html')
        html_content = template.render(**data)
        
        html_path = os.path.join(self.report_dir, 'html', f'{report_id}.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return html_path
    
    def _generate_pdf(self, html_path: str, report_id: str) -> str:
        """Generate PDF from HTML report"""
        pdf_path = os.path.join(self.report_dir, 'pdf', f'{report_id}.pdf')
        
        try:
            
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': 'UTF-8'
            }
            
            
            wkhtmltopdf_paths = [
                'wkhtmltopdf',  
                r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',  
                '/usr/local/bin/wkhtmltopdf',  
                '/usr/bin/wkhtmltopdf'  
            ]
            
            config = None
            for path in wkhtmltopdf_paths:
                if os.path.isfile(path):
                    config = pdfkit.configuration(wkhtmltopdf=path)
                    break
            
            if config:
                pdfkit.from_file(html_path, pdf_path, options=options, configuration=config)
            else:
                pdfkit.from_file(html_path, pdf_path, options=options)
            
            return pdf_path
            
        except Exception as e:
            self.logger.error(f"PDF generation failed: {str(e)}")
            raise
    
    def _generate_summary(self, report_data: Dict) -> Dict:
        """Generate report summary"""
        return {
            'document_name': report_data['document']['name'],
            'overall_similarity': report_data['similarity']['overall_similarity'],
            'matched_passages': len(report_data['similarity'].get('matched_segments', [])),
            'generated_at': report_data['generated_at']
        } 