import os
import logging
import base64
import requests
import json
from dotenv import load_dotenv
from modules.pdf_utils import extract_parenthetical_values

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def post_process_gifi_values(data, parenthetical_values):
    """
    Post-process extracted GIFI values
    
    Args:
        data (dict): Dictionary mapping GIFI codes to values
        parenthetical_values (dict): Dictionary mapping GIFI codes to bool indicating if value was in parentheses
        
    Returns:
        dict: Processed dictionary mapping GIFI codes to values
    """
    # List of GIFI codes that should always be positive
    # These are typically accumulated values that are displayed in parentheses
    # but should remain positive
    POSITIVE_EXCEPTIONS = {
        '1741',  # Accumulated amortization of machinery, equipment, furniture and fixtures
        '1743',  # Accumulated amortization of automotive equipment
        '1745',  # Accumulated amortization of leasehold improvements
        '1775',  # Accumulated amortization of intangible assets
        '1786',  # Accumulated amortization of resource properties
        '1787',  # Accumulated amortization of deferred charges
        '1788',  # Accumulated amortization of deferred expenses
        '1919',  # Accumulated amortization of goodwill
    }
    
    processed = {}
    for code, value in data.items():
        try:
            # Remove any remaining formatting
            clean_value = value.replace(',', '').replace('$', '').replace('(', '').replace(')', '')
            
            # Convert to integer
            numeric_value = int(clean_value)
            
            # Make negative if in parentheses and not an exception
            if code in parenthetical_values and code not in POSITIVE_EXCEPTIONS:
                numeric_value = -numeric_value
            
            # Convert back to string
            processed[code] = str(numeric_value)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to process value for GIFI {code}: {str(e)}")
            processed[code] = value
    
    return processed

def extract_data_with_vision(image_path, pdf_path=None, page_number=1):
    """
    Extract GIFI codes and values from an image using OpenAI's Vision API
    
    Args:
        image_path (str): Path to the image file
        pdf_path (str, optional): Path to the original PDF file, used for text extraction
        page_number (int, optional): Page number in PDF to extract from (1-based)
        
    Returns:
        dict: Dictionary mapping GIFI codes to their values
    """
    try:
        logger.info(f"Extracting data from image: {image_path}")
        
        # Get parenthetical values from PDF if available
        parenthetical_values = {}
        if pdf_path:
            parenthetical_values = extract_parenthetical_values(pdf_path, page_number)
            logger.info(f"Found {len(parenthetical_values)} parenthetical values")
        
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Prepare the messages for the API
        messages = [
            {
                "role": "system",
                "content": """You are an expert at extracting GIFI codes and their corresponding values from tax form images. Follow these rules:
                1. Only extract GIFI codes and their corresponding values from the "Current Year" column
                2. Return values as strings without currency symbols or commas
                3. For values in parentheses, remove the parentheses but keep the value positive - we'll handle negatives in post-processing
                4. Ignore any text that isn't a GIFI code and its value
                5. If a value appears to be zero, return "0"
                6. Format the response as a JSON object with GIFI codes as keys and values as strings
                7. Only include entries where you are confident in both the GIFI code and value
                8. Do not include any explanatory text in your response, just the JSON
                Example response:
                {
                    "1000": "123456",
                    "2599": "0"
                }"""
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the GIFI codes and values from this tax form image:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]
            }
        ]
        
        # Make the API request
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
            },
            json={
                "model": "gpt-4o",
                "messages": messages,
                "max_tokens": 1000
            },
            timeout=30
        )
        
        # Check for errors
        response.raise_for_status()
        
        # Parse the response
        try:
            content = response.json()["choices"][0]["message"]["content"]
            
            # Handle case where JSON is wrapped in markdown code blocks
            if content.startswith("```") and "```" in content:
                # Extract JSON from markdown code block
                content = content.split("```")[1]
                if content.startswith("json\n"):
                    content = content[5:]  # Remove "json\n" prefix
                elif content.startswith("json"):
                    content = content[4:]  # Remove "json" prefix
            
            data = json.loads(content)
            
            # Post-process the data
            processed_data = post_process_gifi_values(data, parenthetical_values)
            
            logger.info(f"Successfully extracted data from image: {len(processed_data)} items")
            return processed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response as JSON: {str(e)}")
            logger.error(f"Raw response: {content}")
            raise
            
        except KeyError as e:
            logger.error(f"Unexpected API response format: {str(e)}")
            logger.error(f"Response: {response.json()}")
            raise
        
    except Exception as e:
        logger.error(f"Error extracting data from image: {str(e)}")
        raise
