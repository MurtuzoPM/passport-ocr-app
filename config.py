import os

class Config:
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {'webp', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
    OCR_LANGUAGE = ['en']
    OCR_ENGINE = 'easyocr'
    ENABLE_IMAGE_PREPROCESSING = True
    MAX_PROCESSING_TIME = 30
