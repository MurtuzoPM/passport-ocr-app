import os
import cv2
import numpy as np
from PIL import Image

def validate_image(file_path):
    """
    Validates that the file exists and can be opened as an image.
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True, "Valid image"
    except Exception as e:
        return False, f"Invalid image format or corrupted file: {str(e)}"

def preprocess_image(file_path, enable_preprocessing=True):
    """
    Loads an image and preprocesses it for OCR.
    Preprocessing steps include:
    - Grayscale conversion
    - Dynamic resizing to a standard width (min 1200px) to boost OCR on low-res images
    - Contrast enhancement (CLAHE)
    - Edge-preserving denoising (Bilateral Filter)
    """
    # Verify image first
    is_valid, msg = validate_image(file_path)
    if not is_valid:
        raise ValueError(msg)
        
    # Read image using PIL to support WebP, TIFF, BMP, PNG, JPG natively and consistently
    try:
        pil_img = Image.open(file_path).convert('RGB')
        img = np.array(pil_img)
        # Convert RGB to BGR for OpenCV operations
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    except Exception as e:
        # Fallback to direct cv2 read
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"OpenCV failed to read the image: {str(e)}")

    if not enable_preprocessing:
        return img

    # 1. Grayscale conversion
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Dynamic scaling (important for OCR engine success on small images)
    height, width = gray.shape
    if width < 1200:
        scaling_factor = 1200.0 / width
        gray = cv2.resize(gray, (0, 0), fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_CUBIC)
    
    # 3. Enhance Contrast (CLAHE - Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # 4. Denoise (Bilateral Filter smooths out textures while preserving sharp text outlines)
    denoised = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)
    
    return denoised
