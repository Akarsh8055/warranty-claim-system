from waitress import serve
from app import app
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('warranty_claims.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info('Starting Warranty Claims System in production mode...')
    serve(app, host='0.0.0.0', port=5001, threads=4)
    logger.info('Server started successfully.') 