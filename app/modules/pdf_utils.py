import os
import logging
import tempfile
from pdf2image import convert_from_path, exceptions
import re
import traceback

logger = logging.getLogger(__name__)

def convert_pdf_to_images(pdf_path, pages=None):
    """
    Convert PDF pages to images
    
    Args:
        pdf_path (str): Path to the PDF file
        pages (list, optional): List of page numbers to convert (1-indexed). If None, converts all pages.
    
    Returns:
        list: List of paths to the generated images
    """
    try:
        logger.info(f"Converting PDF to images: {pdf_path}")
        logger.info(f"Selected pages: {pages}")
        
        # Log environment information
        logger.info(f"Current PATH: {os.environ['PATH']}")
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        poppler_path = os.path.join(project_root, "poppler", "poppler-23.11.0", "Library", "bin")
        logger.info(f"Poppler path exists: {os.path.exists(poppler_path)}")
        logger.info(f"Poppler path contents: {os.listdir(poppler_path) if os.path.exists(poppler_path) else 'Not found'}")
        
        # Create temporary directory for images
        output_dir = tempfile.mkdtemp(prefix="pdf_images_")
        logger.info(f"Created temp directory: {output_dir}")
        
        # Convert PDF to images
        if pages:
            # Process each page individually and combine the results
            images = []
            for page_num in pages:
                logger.info(f"Processing page {page_num}")
                # Convert from 1-indexed (user input) to 0-indexed (pdf2image)
                page_idx = page_num - 1
                
                try:
                    page_images = convert_from_path(
                        pdf_path,
                        dpi=300,  # Higher DPI for better text recognition
                        fmt="png",
                        output_folder=output_dir,
                        paths_only=True,
                        thread_count=2,
                        use_pdftocairo=True,
                        grayscale=False,
                        first_page=page_idx + 1,  # pdf2image uses 1-indexed for first_page
                        last_page=page_idx + 1,    # pdf2image uses 1-indexed for last_page
                        poppler_path=poppler_path  # Explicitly set poppler path
                    )
                    logger.info(f"Successfully converted page {page_num}")
                    images.extend(page_images)
                except Exception as e:
                    logger.error(f"Error converting page {page_num}: {str(e)}")
                    logger.error(traceback.format_exc())
                    raise
        else:
            # Convert all pages
            images = convert_from_path(
                pdf_path,
                dpi=300,  # Higher DPI for better text recognition
                fmt="png",
                output_folder=output_dir,
                paths_only=True,
                thread_count=2,
                use_pdftocairo=True,
                grayscale=False,
                poppler_path=poppler_path  # Explicitly set poppler path
            )
        
        logger.info(f"Generated {len(images)} images from PDF")
        logger.info(f"Image paths: {images}")
        return images
    
    except exceptions.PDFPageCountError as e:
        logger.error(f"PDF page count error: {str(e)}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Invalid page selection: {str(e)}")
    
    except exceptions.PDFInfoNotInstalledError:
        logger.error("pdftoppm or pdftocairo is not installed")
        logger.error(f"PATH: {os.environ['PATH']}")
        logger.error(f"Poppler path: {poppler_path}")
        logger.error(traceback.format_exc())
        raise RuntimeError("PDF conversion tools not installed. Please install poppler.")
    
    except Exception as e:
        logger.error(f"Error converting PDF to images: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_pdf_page_count(pdf_path):
    """
    Get the total number of pages in a PDF file
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        int: Number of pages in the PDF
    """
    try:
        from PyPDF2 import PdfReader
        
        with open(pdf_path, 'rb') as file:
            pdf = PdfReader(file)
            return len(pdf.pages)
    
    except Exception as e:
        logger.error(f"Error getting PDF page count: {str(e)}")
        raise

def extract_parenthetical_values(pdf_path, page_number=1):
    """
    Extract text from PDF and identify values that appear in parentheses.
    
    Args:
        pdf_path (str): Path to the PDF file
        page_number (int): Page number to extract from (1-based)
        
    Returns:
        dict: Dictionary mapping GIFI codes to bool indicating if value is in parentheses
    """
    try:
        import pdfplumber  # Import here to avoid startup cost if not used
        
        parenthetical_values = {}
        
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[page_number - 1]
            text = page.extract_text()
            
            # Look for patterns like:
            # 1000 ($1,234) or 1000 (1,234)
            # 1000............($1,234)
            # 1000 (1234)
            # Also handles whitespace and dots between code and value
            pattern = r'(\d{4})[\s.]+\(([\$\s]?[\d,]+)\)'
            matches = re.finditer(pattern, text)
            
            # Debug logging
            logger.info(f"Extracted text from page {page_number}:")
            logger.info(text[:500])  # Show first 500 chars
            
            for match in matches:
                gifi_code = match.group(1)
                value = match.group(2)
                logger.info(f"Found parenthetical value for GIFI {gifi_code}: {value}")
                parenthetical_values[gifi_code] = True
                
        return parenthetical_values
        
    except Exception as e:
        logger.error(f"Error extracting parenthetical values: {str(e)}")
        return {}
