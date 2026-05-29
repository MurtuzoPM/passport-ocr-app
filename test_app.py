import sys
import os
import json

# Force relative path resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ocr_engine.image_processor import preprocess_image
    from ocr_engine.ocr_handler import OCRHandler
    from ocr_engine.text_parser import TextParser
    from utils.validators import validate_passport_number, normalize_date
    
    print("SUCCESS: Modules loaded successfully!")
    
    handler = OCRHandler()
    parser = TextParser()
    
    # Run mock extraction
    ocr_data = handler.extract_text(None)
    parsed_data = parser.parse(ocr_data)
    
    print("\nSUCCESS: Headless OCR Parsing outputs verified.")
    print("Parsed Data Sample:")
    print(json.dumps(parsed_data, indent=2))
    
    # Verify new fields exist in output dictionary
    assert "first_name" in parsed_data
    assert "last_name" in parsed_data
    assert "date_of_issue" in parsed_data
    assert "authority" in parsed_data
    
    sys.exit(0)
except Exception as e:
    print(f"FAILED: Exception occurred: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
