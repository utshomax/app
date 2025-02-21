import sys
import time
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', mode='a'),
        logging.StreamHandler(sys.stdout)
    ],
    force=True
)

# Create a logger instance
logger = logging.getLogger('jobby.monitor')

def run_app():
    while True:
        try:
            logging.info(f"Starting application at {datetime.now()}")
            # Run the main application
            process = subprocess.Popen(
                [sys.executable, 'main.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Monitor the process
            while True:
                return_code = process.poll()
                if return_code is not None:
                    stdout, stderr = process.communicate()
                    if return_code != 0:
                        logging.error(f"Application crashed with code {return_code}")
                        logging.error(f"Error output: {stderr.decode()}")
                        logging.info("Restarting application in 5 seconds...")
                        time.sleep(5)
                        break
                    else:
                        logging.info("Application stopped normally")
                        return
                time.sleep(1)
                
        except Exception as e:
            logging.error(f"Error running application: {str(e)}")
            logging.info("Restarting application in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    logging.info("Starting application monitor")
    run_app()