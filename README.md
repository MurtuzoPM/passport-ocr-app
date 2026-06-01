#  Passport OCR Scanner

> **An intelligent automated OCR pipeline that extracts structured metadata from passport images using EasyOCR, OpenCV, and advanced NLP parsing.**

![Flask](https://img.shields.io/badge/Flask-2.3%2B-000?logo=flask)
![EasyOCR](https://img.shields.io/badge/EasyOCR-1.6%2B-4FC08D?logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-5C3EE8?logo=opencv)
![License](https://img.shields.io/badge/License-MIT-blue)

---

##  Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
  - [Web UI](#web-ui)
  - [REST API](#rest-api)
  - [Batch Processing](#batch-processing)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

##  Overview

The **Passport OCR Scanner** is an application that automatically extracts structured information from scanned passport pages. It combines **computer vision preprocessing** (grayscale, denoising, contrast enhancement) with **EasyOCR** text recognition and a sophisticated **NLP parsing engine** to extract fields such as:

| Field | Example |
|-------|---------|
| Passport Number | `A12345678` |
| Full Name | `JOHN MICHAEL DOE` |
| Date of Birth | `1990-05-15` |
| Nationality | `USA` |
| Gender | `M` |
| Date of Issue | `2020-05-15` |
| Date of Expiry | `2030-05-15` |
| Issuing Authority | `USDOS / DEPT OF STATE` |

The system supports **both MRZ (Machine Readable Zone)** and **visual text field** parsing, with fallback strategies to handle corrupted OCR output, mixed-language documents, and low-quality scans.

---

## Features

### Core Capabilities
- ** MRZ Parsing** — Extracts data from ICAO-standard Machine Readable Zones (lines 1 & 2) with high confidence
- ** Visual Field Extraction** — NLP-driven parsing of non-MRZ fields (date of issue, authority) using keyword detection and positional heuristics
- ** Smart Image Preprocessing** — Automatic grayscale conversion, CLAHE contrast enhancement, bilateral denoising, and dynamic resolution scaling
- ** OCR Error Correction** — Intelligent date validation that corrects common OCR misreadings (e.g., `40` → `20`/`09`/`30`, `O` → `0`, `I` → `1`)
- ** Confidence Scoring** — Hybrid confidence metric combining raw OCR confidence with parsed field validation quality
- ** Fallback OCR Engine** — Graceful degradation when EasyOCR is unavailable (mock demo data for testing)

### Web UI Features
- ** Drag & Drop Upload** — Modern file upload with drag-and-drop support for both single and batch modes
- ** Batch Processing** — Upload multiple passport images and process them sequentially with real-time progress tracking
- ** Results Dashboard** — Clean, structured field display with MRZ detection badges and confidence meters
- ** JSON Export** — Copy to clipboard or download results as JSON files (single & batch)
- ** Raw Inspection** — Modal viewer for inspecting complete JSON output per file
- ** Session Statistics** — Batch processing summary with success rates, average confidence, and cumulative time

### API Features
- **RESTful Design** — Clean JSON API with proper HTTP status codes
- **Single & Batch Endpoints** — Process one or many images in a single request
- **Debug Mode** — Optional `?debug=true` query parameter for verbose OCR logging
- **Concurrent-Safe** — UUID-tagged temp files with automatic cleanup
- **Health Endpoint** — System readiness probe with EasyOCR availability status

---

---

##  Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌───────────────────┐
│   Web UI     │────▶│   Flask API     │────▶│   Image Processor  │
│  (Tailwind)  │     │  (REST JSON)    │     │  (OpenCV/PIL)      │
└──────────────┘     └─────────────────┘     └────────┬──────────┘
                                                       │
                                                       ▼
                                              ┌───────────────────┐
                                              │   OCR Handler     │
                                              │  (EasyOCR)        │
                                              └────────┬──────────┘
                                                       │
                                                       ▼
                                              ┌───────────────────┐
                                              │   Text Parser     │
                                              │  (NLP / Regex)    │
                                              └────────┬──────────┘
                                                       │
                                                       ▼
                                              ┌───────────────────┐
                                              │   JSON Output     │
                                              │  (Structured)     │
                                              └───────────────────┘
```

### Pipeline Flow

1. **Upload** — Image received via Web UI drag-drop or REST API
2. **Preprocessing** — OpenCV converts to grayscale, applies CLAHE contrast, bilateral denoising, and rescales to ≥1200px width
3. **OCR** — EasyOCR extracts text with per-character confidence scores
4. **Text Parsing** — Dual-strategy extraction:
   - **MRZ Parsing** — Decodes ICAO 9303 standard lines for passport number, DOB, expiry, gender, nationality
   - **Visual Parsing** — Keyword-driven extraction for dates, names, authority, with positional heuristics
5. **Validation & Correction** — OCR error correction, date validation, field normalization
6. **Confidence Scoring** — Hybrid metric (30% raw OCR confidence + 70% field validation quality)
7. **Response** — Structured JSON returned to client

---

##  Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.8+** | Core runtime |
| **Flask 2.3+** | REST API framework |
| **EasyOCR 1.6+** | Deep learning OCR engine (CPU-based) |
| **OpenCV 4.8+** | Image preprocessing (grayscale, CLAHE, denoising) |
| **Pillow 10.3+** | Image format support (WebP, TIFF, BMP, PNG, JPG) |
| **NumPy 1.24+** | Array operations for image processing |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Tailwind CSS** | Utility-first styling (CDN-loaded) |
| **Vanilla JS** | DOM manipulation & async fetch API |
| **FontAwesome 6** | Iconography |

---

##  Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Web browser (for Web UI)

### Step 1: Clone the Repository

```bash
git clone https://github.com/MurtuzoPM/passport-ocr-app.git
cd passport-ocr-app
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Linux/macOS
# OR
venv\Scripts\activate      # On Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** EasyOCR will automatically download its pre-trained model on first run (~1-2 GB download). Ensure you have a stable internet connection.

### Step 4: Run the Application

```bash
python app.py
```

The server will start at `http://127.0.0.1:5000`.

> **Tip:** The first run may take longer as EasyOCR downloads its model files. Subsequent runs will be much faster.

---

##  Configuration

All configuration is managed via `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `UPLOAD_FOLDER` | `./uploads` | Temporary directory for uploaded files |
| `MAX_FILE_SIZE` | `50 MB` | Maximum upload file size |
| `ALLOWED_EXTENSIONS` | `webp, png, jpg, jpeg, tiff, bmp` | Accepted image formats |
| `OCR_LANGUAGE` | `['en']` | EasyOCR language packs |
| `OCR_ENGINE` | `easyocr` | OCR backend (future extensibility) |
| `ENABLE_IMAGE_PREPROCESSING` | `True` | Toggle OpenCV preprocessing pipeline |
| `MAX_PROCESSING_TIME` | `30` seconds | Processing timeout threshold |

You can override these via environment variables or by modifying `config.py` directly.

---

##  Usage

### Web UI

Open `http://127.0.0.1:5000` in your browser:

#### Single Scan
1. Drag & drop a passport image onto the upload zone (or click to browse)
2. Click **"Analyze Passport"**
3. View extracted fields, confidence score, and raw JSON
4. Copy JSON to clipboard or download as a `.json` file

#### Batch Scan
1. Click the **"Batch Scan"** tab
2. Drag & drop multiple passport images (or select using file dialog)
3. Click **"Process Batch Queue"**
4. Watch real-time progress as each file is processed
5. View the results table with per-file confidence and status
6. Export all results as a single JSON file

### REST API

The application runs as a headless API microservice. Access the interactive API documentation at the root endpoint:

```bash
curl http://127.0.0.1:5000/
```

#### Extract Data from a Single Passport

```bash
curl -X POST -F "file=@passport.jpg" http://127.0.0.1:5000/api/extract
```

**Response:**
```json
{
  "success": true,
  "data": {
    "passport_number": "A12345678",
    "first_name": "JOHN MICHAEL",
    "last_name": "DOE",
    "date_of_birth": "1990-05-15",
    "nationality": "USA",
    "gender": "M",
    "date_of_issue": "2020-05-15",
    "expiry_date": "2030-05-15",
    "authority": "USDOS / DEPT OF STATE",
    "confidence": 0.95,
    "mrz_detected": true
  },
  "filename": "passport.jpg",
  "processing_time": 1.452
}
```

#### Debug Mode

Add `?debug=true` to see detailed OCR engine output in server logs:

```bash
curl -X POST -F "file=@passport.jpg" "http://127.0.0.1:5000/api/extract?debug=true"
```

#### Batch Processing

```bash
curl -X POST -F "files=@passport1.jpg" -F "files=@passport2.jpg" http://127.0.0.1:5000/api/extract-batch
```

**Response:**
```json
{
  "success": true,
  "batch_size": 2,
  "results": [
    {
      "filename": "passport1.jpg",
      "success": true,
      "data": { "...extracted fields..." },
      "processing_time": 1.23
    },
    {
      "filename": "passport2.jpg",
      "success":true,
      "data": { "...extracted fields..." },
      "processing_time": 1.45
    }
  ],
  "total_processing_time": 2.68
}
```

#### Health Check

```bash
curl http://127.0.0.1:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "easyocr_available": true,
  "config": {
    "max_file_size_mb": 50,
    "allowed_extensions": ["webp", "png", "jpg", "jpeg", "tiff", "bmp"],
    "ocr_language": ["en"]
  }
}
```

---

##  API Reference

### `GET /`
Interactive REST API documentation (returns JSON describing all endpoints).

### `GET /health`
System readiness probe.
- **Response:** `{ status, easyocr_available, config }`
- **Status Codes:** `200 OK`

### `POST /api/extract`
Extract passport data from a single image.
- **Content-Type:** `multipart/form-data`
- **Params:** `file` (image file)
- **Query Params:** `?debug=true` (optional, enables verbose logging)
- **Status Codes:**
  - `200` — Success
  - `400` — No file / Invalid format
  - `422` — Processing error
  - `500` — Internal server error

### `POST /api/extract-batch`
Extract passport data from multiple images.
- **Content-Type:** `multipart/form-data`
- **Params:** `files` or `files[]` (multiple image files)
- **Status Codes:**
  - `200` — Success (partial failures included in results array)
  - `400` — No files
  - `500` — Internal server error

---

##  Project Structure

```
passport-ocr-app/
├── app.py                          # Flask application entry point & API routes
├── config.py                       # Application configuration settings
├── requirements.txt                # Python dependencies
├── test_app.py                     # Module load & smoke test
├── README.md                       # This file
├── uploads/                        # Temporary upload directory (auto-created)
│
├── utils/
│   └── validators.py               # File validation, date normalization,
│                                   # passport number validation, OCR text cleaning
│
├── ocr_engine/
│   ├── __init__.py                 # Package init
│   ├── image_processor.py          # OpenCV preprocessing pipeline
│   │                               # (grayscale, CLAHE, bilateral filter, resize)
│   ├── ocr_handler.py              # EasyOCR wrapper with fallback mock data
│   └── text_parser.py              # NLP parser: MRZ decoding + visual field extraction
│                                   # (names, dates, authority, gender, nationality)
│
├── static/
│   ├── css/
│   │   └── style.css               # Custom styles, scrollbar, animation keyframes
│   └── js/
│       └── script.js               # Full UI logic: drag-drop, scan, batch, export
│
└── templates/
    └── index.html                  # Single-page app with Tailwind CSS UI
```

---

##  Development

### Running Tests

```bash
python test_app.py
```

The smoke test validates:
- Module imports resolve correctly
- OCR handler initializes (with fallback if EasyOCR unavailable)
- Text parser produces expected output with all required fields
- Fields `first_name`, `last_name`, `date_of_issue`, and `authority` are present

### Extending the OCR Engine

#### Adding New Languages

Modify `config.py`:
```python
OCR_LANGUAGE = ['en', 'fr', 'de', 'es']  # EasyOCR supported languages
```

#### Adding Custom Preprocessing Steps

Edit `ocr_engine/image_processor.py` and add your OpenCV operations to the `preprocess_image()` function.

#### Adding New Extracted Fields

1. Update `text_parser.py` — Add parsing logic in `_parse_visual_fields()`
2. Update `TextParser.parse()` — Add field to default `parsed_data` dictionary
3. Update `app.py` — The field will automatically appear in JSON output
4. Update `templates/index.html` — Add display field in results section
5. Update `static/js/script.js` — Bind the new field in `renderSingleResults()`

### Deployment Considerations

For production deployment:
- Use a production WSGI server (Gunicorn, uWSGI)
- Set `debug=False` in `app.py`
- Configure proper CORS headers for cross-origin requests
- Add rate limiting for API endpoints
- Use HTTPS for secure file uploads
- Consider GPU-accelerated EasyOCR for faster processing

---

##  Troubleshooting

### EasyOCR Not Found / Import Error

```bash
pip install easyocr
```

If you still face issues, the application falls back gracefully with mock demo data. You'll see:
```
Warning: EasyOCR library is not installed. Using fallback OCR mode.
```

### Image Not Processing

- Ensure the file format is one of: WebP, PNG, JPG, JPEG, TIFF, BMP
- Max file size: 50 MB
- Check server logs for detailed error messages

### Slow Processing

- First run requires EasyOCR model download (~1-2 GB)
- CPU-based OCR is inherently slower than GPU; expect 1-5 seconds per image
- Reduce image resolution before upload if speed is critical

### Memory Issues

- Large batch jobs may consume significant RAM
- The application cleans up temp files automatically after each request
- Adjust `MAX_FILE_SIZE` in `config.py` if needed

---

##  License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

##  Acknowledgments

- [EasyOCR](https://github.com/JaidedAI/EasyOCR) — Ready-to-use OCR with 80+ languages
- [OpenCV](https://opencv.org/) — Computer vision library
- [Flask](https://flask.palletsprojects.com/) — Python web framework
- [Tailwind CSS](https://tailwindcss.com/) — Utility-first CSS framework
- [FontAwesome](https://fontawesome.com/) — Icon library

---


