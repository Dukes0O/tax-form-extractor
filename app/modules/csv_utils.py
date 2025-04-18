import os
import logging
import csv
import tempfile
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

def generate_csv(mapped_data, save_path):
    """
    Generate a CSV file from mapped data and save it to the specified location.
    
    Args:
        mapped_data (dict): Dictionary of cell IDs and their values.
        save_path (str): Path where the CSV file should be saved.
    
    Returns:
        str: Path to the generated CSV file.
    """
    try:
        logger.info(f"Generating CSV at: {save_path} with {len(mapped_data)} mapped items")

        with open(save_path, 'w', newline='') as csvfile:
            fieldnames = ['cell_id', 'value']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for cell_id, value in mapped_data.items():
                writer.writerow({'cell_id': cell_id, 'value': value})

        logger.info(f"CSV file saved to: {save_path}")
        return save_path

    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}")
        raise


def generate_taxprep_csv(mapped_data, template_path=None):
    """
    Generate a CSV file compatible with TaxPrep software
    
    Args:
        mapped_data (dict): Dictionary of cell IDs and their values
        template_path (str, optional): Path to a TaxPrep CSV template
    
    Returns:
        str: Path to the generated CSV file
    """
    try:
        logger.info(f"Generating TaxPrep CSV with {len(mapped_data)} mapped items")
        
        # Create a timestamp for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"taxprep_data_{timestamp}.csv"
        csv_path = os.path.join(tempfile.gettempdir(), csv_filename)
        
        # If a template is provided, use it as a base
        if template_path and os.path.exists(template_path):
            logger.info(f"Using template: {template_path}")
            df = pd.read_csv(template_path)
            
            # Update values in the template
            for cell_id, value in mapped_data.items():
                if cell_id in df.columns:
                    # If the cell ID is a column, update the first row
                    df.at[0, cell_id] = value
                else:
                    # If not found, log a warning
                    logger.warning(f"Cell ID {cell_id} not found in template")
            
            # Save the updated template
            df.to_csv(csv_path, index=False)
        
        else:
            # Create a new CSV file with the mapped data
            with open(csv_path, 'w', newline='') as csvfile:
                # Determine all unique cell IDs
                fieldnames = list(mapped_data.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerow(mapped_data)
        
        logger.info(f"TaxPrep CSV file generated: {csv_path}")
        return csv_path
    
    except Exception as e:
        logger.error(f"Error generating TaxPrep CSV: {str(e)}")
        raise
