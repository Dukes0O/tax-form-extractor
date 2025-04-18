import os
import logging
import sys
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime
import PyPDF2
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

# Add Poppler to PATH and DLL search paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
poppler_path = os.path.join(project_root, "poppler", "poppler-23.11.0", "Library", "bin")
os.environ["PATH"] = poppler_path + os.pathsep + os.environ["PATH"]
if hasattr(os, 'add_dll_directory'):  # Windows-specific DLL directory handling
    os.add_dll_directory(poppler_path)
print(f"\nAdded Poppler to PATH: {poppler_path}")
logger.info(f"Added Poppler to PATH: {poppler_path}")
logger.info(f"Current PATH: {os.environ['PATH']}")

# Import utility modules
from modules.pdf_utils import convert_pdf_to_images
from modules.docx_utils import extract_text_from_docx
from modules.openai_utils import extract_data_with_vision
from modules.csv_utils import generate_csv
from modules.mapping_utils import map_extracted_data_to_cell_ids, list_available_mappings

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['UPLOAD_FOLDER'] = os.path.join(tempfile.gettempdir(), 'tax_form_uploads')
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'doc'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            logger.error("No file part in request")
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("No selected file")
            return jsonify({'error': 'No selected file'}), 400
        
        if file:
            filename = secure_filename(file.filename)
            logger.info(f"Processing uploaded file: {filename}")
            
            # Create upload directory if it doesn't exist
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
                logger.info(f"Created upload directory: {app.config['UPLOAD_FOLDER']}")
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logger.info(f"Saved file to: {filepath}")
            
            # Determine file type
            filetype = 'pdf' if filename.lower().endswith('.pdf') else 'docx' if filename.lower().endswith(('.docx', '.doc')) else None
            if not filetype:
                logger.error(f"Unsupported file type: {filename}")
                return jsonify({'error': 'Unsupported file type'}), 400
            
            logger.info(f"File type determined: {filetype}")
            return jsonify({
                'filepath': filepath,
                'filename': filename,
                'filetype': filetype
            })
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Error uploading file: {str(e)}'}), 500

@app.route('/get_page_count', methods=['POST'])
def get_page_count():
    """Get the number of pages in a PDF file"""
    data = request.json
    filepath = data.get('filepath')
    
    if not filepath or not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Check if the file is a PDF
        if not filepath.lower().endswith('.pdf'):
            return jsonify({'error': 'File is not a PDF'}), 400
        
        # Get page count
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)
        
        logger.info(f"PDF page count: {page_count} for file: {filepath}")
        
        return jsonify({
            'success': True,
            'pageCount': page_count
        })
    
    except Exception as e:
        logger.error(f"Error getting page count: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Error getting page count: {str(e)}'}), 500

@app.route('/available_mappings', methods=['GET'])
def available_mappings():
    """Return a list of available mapping dictionaries (for UI dropdown), with descriptions."""
    try:
        mappings = list_available_mappings()
        # Attempt to read a description from a companion file (e.g., GIFI_map.txt)
        result = []
        for name, path in mappings.items():
            desc_path = path.with_suffix('.txt')
            desc = ''
            if desc_path.exists():
                with open(desc_path, 'r', encoding='utf-8') as f:
                    desc = f.read().strip()
            result.append({'name': name, 'description': desc})
        return jsonify({'mappings': result})
    except Exception as e:
        logger.error(f"Error listing mappings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_file():
    """Process the uploaded file and extract data (multi-dictionary support, mapping warnings)"""
    try:
        data = request.json
        filepath = data.get('filepath')
        filetype = data.get('filetype')
        pages = data.get('pages', [])
        save_directory = data.get('save_directory')
        dictionary_name = data.get('dictionary', 'GIFI')

        if not filepath or not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return jsonify({'error': 'File not found'}), 404

        extracted_data = {}
        mapping_warnings = []
        if filetype == 'pdf':
            logger.info(f"Processing PDF with selected pages: {pages}")
            image_paths = convert_pdf_to_images(filepath, pages)
            for i, img_path in enumerate(image_paths):
                page_num = pages[i] if i < len(pages) else i + 1
                extracted_data[f'page_{page_num}'] = extract_data_with_vision(img_path)
        elif filetype in ['docx', 'doc']:
            text = extract_text_from_docx(filepath)
            extracted_data['text'] = text
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        # Map extracted data to cell IDs using selected dictionary
        # (mapping_utils.map_extracted_data_to_cell_ids now returns both mapped and warnings)
        combined_data = {k: v for page_data in extracted_data.values() for k, v in page_data.items()}
        mapped_data, mapping_warnings = map_extracted_data_to_cell_ids(combined_data, dictionary_name)

        logger.info(f"Mapped {len(mapped_data)} items to cell IDs using {dictionary_name}")

        # Determine save directory
        if not save_directory:
            save_directory = os.path.dirname(filepath)

        csv_filename = f"tax_form_data_{dictionary_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path = os.path.join(save_directory, csv_filename)
        generate_csv(mapped_data, csv_path)
        logger.info(f"Processing complete. CSV saved to {csv_path}")

        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'csv_filename': csv_filename,
            'csv_path': csv_path,
            'mapping_warnings': mapping_warnings
        })
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download the generated CSV file"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
