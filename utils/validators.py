import re
from datetime import datetime

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def clean_text(text):
    if not text:
        return ""
    # Remove leading/trailing whitespaces and standardize whitespace
    cleaned = re.sub(r'\s+', ' ', text).strip()
    return cleaned

def validate_passport_number(passport_num):
    if not passport_num:
        return False
    # Typical passports are 6 to 12 characters, alphanumeric
    cleaned = re.sub(r'\s+', '', passport_num).upper()
    pattern = r'^[A-Z0-9]{6,12}$'
    return bool(re.match(pattern, cleaned))

def normalize_date(date_str):
    """
    Attempts to normalize various date formats to YYYY-MM-DD.
    Supports YYMMDD (from MRZ), DD/MM/YYYY, DD.MM.YYYY, YYYY/MM/DD, and wordy formats.
    """
    if not date_str:
        return None
    
    # Clean text first
    date_str = re.sub(r'[\s\-/. ]+', ' ', date_str).strip()
    
    # Try MRZ date format YYMMDD (6 digits)
    if len(date_str) == 6 and date_str.isdigit():
        try:
            # We assume passports expire/are issued within a century.
            # E.g., if YY <= current_year + 10, it is 20YY, else 19YY.
            yy = int(date_str[0:2])
            mm = int(date_str[2:4])
            dd = int(date_str[4:6])
            
            # Simple heuristic for century
            current_year = datetime.now().year
            century = 2000 if yy <= (current_year % 100) + 20 else 1900
            year = century + yy
            
            datetime(year, mm, dd) # Validate date viability
            return f"{year:04d}-{mm:02d}-{dd:02d}"
        except ValueError:
            pass

    # Try standard ISO YYYY-MM-DD
    match_iso = re.search(r'(\d{4})[-/. ](\d{1,2})[-/. ](\d{1,2})', date_str)
    if match_iso:
        try:
            y, m, d = map(int, match_iso.groups())
            datetime(y, m, d)
            return f"{y:04d}-{m:02d}-{d:02d}"
        except ValueError:
            pass

    # Try DD-MM-YYYY or DD.MM.YYYY or DD/MM/YYYY
    match_dmy = re.search(r'(\d{1,2})[-/. ](\d{1,2})[-/. ](\d{4})', date_str)
    if match_dmy:
        try:
            d, m, y = map(int, match_dmy.groups())
            datetime(y, m, d)
            return f"{y:04d}-{m:02d}-{d:02d}"
        except ValueError:
            pass
            
    # Try DD-MM-YY (usually 2 digits year)
    match_dmy2 = re.search(r'(\d{1,2})[-/. ](\d{1,2})[-/. ](\d{2})', date_str)
    if match_dmy2:
        try:
            d, m, y2 = map(int, match_dmy2.groups())
            current_year = datetime.now().year
            century = 2000 if y2 <= (current_year % 100) + 20 else 1900
            y = century + y2
            datetime(y, m, d)
            return f"{y:04d}-{m:02d}-{d:02d}"
        except ValueError:
            pass

    # Fallback to general cleaning
    return date_str
