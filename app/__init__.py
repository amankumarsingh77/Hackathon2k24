from flask import Flask
from app.routes.views import init_routes
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-here'  
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  
    
    
    @app.template_filter('datetime')
    def format_datetime(value):
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime('%Y-%m-%d %H:%M:%S')
    
    init_routes(app)
    return app 