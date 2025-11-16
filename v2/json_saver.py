"""
Saves the analysis results to a JSON file.
"""
import json
from typing import Dict

def save_analysis_to_json(analysis_data: Dict, file_path: str):
    """
    Saves the analysis data to a JSON file.

    Args:
        analysis_data: A dictionary containing the analysis results.
        file_path: The path to the output JSON file.
    """
    with open(file_path, "w") as f:
        json.dump(analysis_data, f, indent=2)
