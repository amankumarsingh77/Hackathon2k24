import signal
import sys
from app import create_app
import atexit
import logging
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle cleanup when the application is shutting down"""
    logger.info('Shutting down gracefully...')
    sys.exit(0)

def cleanup():
    """Cleanup function to be called on exit"""
    logger.info('Performing cleanup...')
    # Add any cleanup tasks here
    plt.close('all')  # Close any open matplotlib figures

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function
    atexit.register(cleanup)
    
    try:
        app = create_app()
        app.run(debug=True, use_reloader=False)  # Disable reloader to avoid duplicate processes
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1) 