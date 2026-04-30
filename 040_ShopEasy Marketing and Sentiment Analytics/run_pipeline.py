import nltk
from config.settings import Config
from src.utils.logger import ProjectLogger
# Placeholder imports for layers we will build next
# from src.bronze.ingestion import BronzeIngestion
# from src.silver.transformer import SilverTransformer
# from src.gold.builder import GoldBuilder

logger = ProjectLogger.get_logger("Orchestrator")

def setup_environment():
    """Initializes system dependencies."""
    logger.info("Initializing environment...")
    Config.initialize_directories()
    
    # NLTK Setup
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        logger.info("Downloading NLTK VADER lexicon...")
        nltk.download('vader_lexicon')

def main():
    setup_environment()
    
    logger.info("--- STARTING MEDALLION PIPELINE ---")
    
    # Phase 2: Bronze
    # bronze = BronzeIngestion()
    # bronze.run()
    
    # Phase 3: Silver
    # silver = SilverTransformer()
    # silver.run()
    
    # Phase 4: Gold
    # gold = GoldBuilder()
    # gold.run()
    
    logger.info("--- PIPELINE COMPLETED SUCCESSFULLY ---")

if __name__ == "__main__":
    main()