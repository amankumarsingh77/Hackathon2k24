import signal
import sys
from app import create_app
import atexit
import logging
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    logger.info('Shutting down gracefully...')
    sys.exit(0)

def cleanup():
    logger.info('Performing cleanup...')
    plt.close('all') 

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)
    
    try:
        app = create_app()
        app.run(debug=True, use_reloader=False)  
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1) 