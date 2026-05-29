import os
import time
import uuid
import logging
import sys

# Add current path to sys.path to resolve imports on startup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

from config import Config
from ocr_engine.image_processor import preprocess_image, validate_image
from ocr_engine.ocr_handler import OCRHandler
from ocr_engine.text_parser import TextParser
from utils.validators import allowed_file

# Initialize Flask App
app = Flask(__name__)
app.config.from_object(Config)

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize OCR Engines
logging.info("Initializing OCR engines...")
ocr_handler = OCRHandler(languages=app.config['OCR_LANGUAGE'])
text_parser = TextParser()
logging.info("OCR engines initialized successfully.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    from ocr_engine.ocr_handler import EASYOCR_AVAILABLE
    return jsonify({
        "status": "healthy",
        "easyocr_available": EASYOCR_AVAILABLE,
        "config": {
            "max_file_size_mb": app.config['MAX_FILE_SIZE'] / (1024 * 1024),
            "allowed_extensions": list(app.config['ALLOWED_EXTENSIONS']),
            "ocr_language": app.config['OCR_LANGUAGE']
        }
    })

def process_single_image(file_path):
    """
    Core pipeline wrapper: Preprocess -> OCR -> Parse.
    """
    # 1. Preprocess image
    preprocessed_img = preprocess_image(
        file_path, 
        enable_preprocessing=app.config['ENABLE_IMAGE_PREPROCESSING']
    )

    # 2. Perform OCR text extraction
    ocr_results = ocr_handler.extract_text(preprocessed_img)

    # 3. Parse text into structured fields
    parsed_data = text_parser.parse(ocr_results)
    
    return parsed_data

@app.route('/api/extract', methods=['POST'])
def extract():
    start_time = time.time()
    
    # Validation checks for multipart request
    if 'file' not in request.files:
        processing_time = round(time.time() - start_time, 2)
        return jsonify({
            "success": False,
            "error": "No file part in the request payload",
            "processing_time": processing_time
        }), 400
        
    file = request.files['file']
    
    if file.filename == '':
        processing_time = round(time.time() - start_time, 2)
        return jsonify({
            "success": False,
            "error": "No file selected for scanning",
            "processing_time": processing_time
        }), 400

    # Format check
    if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        processing_time = round(time.time() - start_time, 2)
        return jsonify({
            "success": False,
            "error": f"Unsupported file format. Supported: {', '.join(app.config['ALLOWED_EXTENSIONS'])}",
            "processing_time": processing_time
        }), 400

    # Generate unique non-overlapping secure filename for concurrency safety
    unique_id = str(uuid.uuid4())
    original_ext = file.filename.rsplit('.', 1)[1].lower()
    temp_filename = secure_filename(f"{unique_id}.{original_ext}")
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
    
    try:
        # Save temp file
        file.save(temp_path)
        
        # Execute pipeline
        extracted_data = process_single_image(temp_path)
        
        processing_time = round(time.time() - start_time, 3)
        return jsonify({
            "success": True,
            "data": extracted_data,
            "filename": file.filename,
            "processing_time": processing_time
        })

    except ValueError as ve:
        processing_time = round(time.time() - start_time, 3)
        return jsonify({
            "success": False,
            "error": str(ve),
            "processing_time": processing_time
        }), 422
    except Exception as e:
        logging.error(f"Uncaught extraction error: {str(e)}", exc_info=True)
        processing_time = round(time.time() - start_time, 3)
        return jsonify({
            "success": False,
            "error": f"Internal processing error: {str(e)}",
            "processing_time": processing_time
        }), 500
    finally:
        # Proactively clean up file after operation to preserve storage security
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as ex:
                logging.error(f"Failed to remove temp file {temp_path}: {str(ex)}")

@app.route('/api/extract-batch', methods=['POST'])
def extract_batch():
    start_time = time.time()
    
    # Batch inputs key support (covers both "files" and standard list arrays "files[]")
    if 'files' not in request.files and 'files[]' not in request.files:
        processing_time = round(time.time() - start_time, 2)
        return jsonify({
            "success": False,
            "error": "No files found in the request payload",
            "processing_time": processing_time
        }), 400
        
    files = request.files.getlist('files') or request.files.getlist('files[]')
    
    if not files or (len(files) == 1 and files[0].filename == ''):
        processing_time = round(time.time() - start_time, 2)
        return jsonify({
            "success": False,
            "error": "No file selections made",
            "processing_time": processing_time
        }), 400

    results = []
    
    for file in files:
        file_start = time.time()
        
        if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            results.append({
                "filename": file.filename,
                "success": False,
                "error": f"Unsupported file format. Supported: {', '.join(app.config['ALLOWED_EXTENSIONS'])}",
                "processing_time": round(time.time() - file_start, 3)
            })
            continue

        unique_id = str(uuid.uuid4())
        original_ext = file.filename.rsplit('.', 1)[1].lower()
        temp_filename = secure_filename(f"{unique_id}.{original_ext}")
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)

        try:
            file.save(temp_path)
            extracted_data = process_single_image(temp_path)
            
            results.append({
                "filename": file.filename,
                "success": True,
                "data": extracted_data,
                "processing_time": round(time.time() - file_start, 3)
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e),
                "processing_time": round(time.time() - file_start, 3)
            })
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    total_time = round(time.time() - start_time, 3)
    return jsonify({
        "success": True,
        "batch_size": len(files),
        "results": results,
        "total_processing_time": total_time
    })

if __name__ == '__main__':
    # Standard Flask entry point
    app.run(host='0.0.0.0', port=5000, debug=True)
