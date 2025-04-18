import os
import logging
import pandas as pd
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Add a set of intentionally excluded GIFI codes (safe list)
SAFE_LIST_CODES = {
    '1599', '2599', '3139', '3499', '3600', '3620', '3640', '3680', '3720', '3849',
    '8089', '8299', '8518', '8519', '9367', '9368', '9369', '9970', '9998', '9999'
}

def list_available_mappings():
    """
    List all available mapping Excel files in the mapping directory.
    Returns:
        dict: Dictionary of mapping name (without _map.xlsx) to file path
    """
    mapping_dir = Path(__file__).parent.parent / "mapping"
    mapping_files = {}
    for file in mapping_dir.glob("*_map.xlsx"):
        name = file.stem.replace('_map', '')
        mapping_files[name] = file
    return mapping_files


def load_mapping(dictionary_name):
    """
    Load a mapping dictionary from the mapping directory by name (e.g., 'GIFI', 'T2S1', 'T661')
    Args:
        dictionary_name (str): Name of the mapping (case-insensitive, e.g., 'GIFI')
    Returns:
        dict: Dictionary mapping codes to cell IDs
    Raises:
        FileNotFoundError: If mapping file does not exist
        ValueError: If required columns are missing
    """
    mapping_dir = Path(__file__).parent.parent / "mapping"
    xlsx_path = mapping_dir / f"{dictionary_name.upper()}_map.xlsx"
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {xlsx_path}")
    df = pd.read_excel(xlsx_path)
    # Validate columns (expect at least two columns)
    if df.shape[1] < 2:
        raise ValueError(f"Mapping file {xlsx_path} must have at least two columns (Cell ID, Code)")
    mapping = {}
    for _, row in df.iterrows():
        cell_id = row.iloc[0]
        code = row.iloc[1]
        if pd.notna(cell_id) and pd.notna(code):
            mapping[str(code)] = str(cell_id)
    logger.info(f"Loaded {len(mapping)} mappings from {xlsx_path}")
    return mapping


def map_extracted_data_to_cell_ids(extracted_data, dictionary_name="GIFI"):
    """
    Map extracted codes and values to cell IDs using the selected dictionary.
    Args:
        extracted_data (dict): Dictionary of extracted codes and their values
        dictionary_name (str): Name of the mapping dictionary to use (default: 'GIFI')
    Returns:
        tuple: Dictionary of cell IDs and their values, list of mapping warnings
    """
    try:
        logger.info(f"Mapping {len(extracted_data)} extracted items to cell IDs using {dictionary_name} dictionary")
        mapping_dict = load_mapping(dictionary_name)
        mapped = {}
        mapping_warnings = []
        for code, value in extracted_data.items():
            code_str = str(code).strip()
            cell_id = mapping_dict.get(code_str)
            if cell_id:
                mapped[cell_id] = value
            elif code_str in SAFE_LIST_CODES:
                continue
            else:
                mapping_warnings.append(f"Code {code_str} not found in {dictionary_name} mapping.")
        return mapped, mapping_warnings
    except Exception as e:
        logger.error(f"Error mapping extracted data: {str(e)}")
        raise


def convert_gifi_map_to_json():
    """
    Convert the GIFI mapping from XLSX to JSON format
    
    Returns:
        str: Path to the generated JSON file
    """
    try:
        # Load the mapping
        gifi_map = load_mapping('GIFI')
        
        # Define the output path
        mapping_dir = Path(__file__).parent.parent / "mapping"
        json_path = mapping_dir / "GIFI_map.json"
        
        # Write to JSON file
        with open(json_path, 'w') as f:
            json.dump(gifi_map, f, indent=4)
        
        logger.info(f"GIFI mapping converted to JSON: {json_path}")
        return str(json_path)
    
    except Exception as e:
        logger.error(f"Error converting GIFI mapping to JSON: {str(e)}")
        raise


# For backward compatibility
load_gifi_map = lambda: load_mapping('GIFI')
