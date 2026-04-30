import logging
import os
from datetime import datetime

class ProjectLogger:
    """Standardized logging for the entire pipeline."""
    
    @staticmethod
    def get_logger(module_name):
        logger = logging.getLogger(module_name)
        
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # Console Handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # File Handler
            log_file = os.path.join("logs", f"pipeline_{datetime.now().strftime('%Y%m%d')}.log")
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
        return logger