import logging
from pathlib import Path

# Import the main functions from your existing setup scripts
from .build_raw_data_cache import cache_all_raw_data
from .build_history import build_historical_data_from_cache
from .init_h2h_records import initialize_h2h_records

logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_full_historical_build():
    """
    Orchestrates the entire one-time historical data build process.
    This is intended to be run on a cold start when data files are missing.
    """
    logging.info("\n>>>--- Performing one-time historical data build ---<<<")
    
    cache_all_raw_data()
    build_historical_data_from_cache()
    initialize_h2h_records()
    
    logging.info("\n>>>--- Historical data build complete. ---<<<")