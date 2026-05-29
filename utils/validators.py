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

def _parse_month_name_date(date_str):
    """
    Parse dates with month names like '15 MAY 1990', '15 MAY / MAI 1990', '15/MAI/1990'.
    Works on the original string (no pre-cleaning) to preserve '/' separators.
    Returns (day, month, year) tuple or None.
    """
    MONTH_NAMES = {
        # English
        "JAN": 1, "JANU": 1, "JANUARY": 1, "JANV": 1,
        "FEB": 2, "FEBR": 2, "FEBRUARY": 2, "FEV": 2, "FEVR": 2,
        "MAR": 3, "MARCH": 3, "MARS": 3, "MAERZ": 3,
        "APR": 4, "APRI": 4, "APRIL": 4, "AVR": 4, "AVRI": 4,
        "MAY": 5, "MAI": 5, "MAG": 5, "MAGG": 5,
        "JUN": 6, "JUNE": 6, "JUIN": 6, "GIU": 6,
        "JUL": 7, "JULY": 7, "JUIL": 7, "JUILL": 7, "JULI": 7, "LUG": 7,
        "AUG": 8, "AUGUST": 8, "AOUT": 8, "AGO": 8,
        "SEP": 9, "SEPT": 9, "SEPTEMBER": 9, "SET": 9,
        "OCT": 10, "OCTOBER": 10, "OKT": 10, "OTT": 10,
        "NOV": 11, "NOVEMBER": 11,
        "DEC": 12, "DECEMBER": 12, "DEZ": 12, "DIC": 12, "DICI": 12, "DECE": 12,
        # Italian
        "GEN": 1, "GENN": 1,
        # Russian transliterations (common on Russian passports)
        "ЯНВ": 1, "ФЕВ": 2, "МАР": 3, "АПР": 4, "МАЙ": 5, "ИЮН": 6,
        "ИЮЛ": 7, "АВГ": 8, "СЕН": 9, "ОКТ": 10, "НОЯ": 11, "ДЕК": 12,
    }
    
    if not date_str:
        return None

    # Match directly on the original string without pre-cleaning
    # Pattern: "DD MMM YYYY", "DD MMM / MMM YYYY", "DD/MMM/YYYY", "DD-MMM-YYYY"
    match = re.search(
        r'(\d{1,2})'           # day
        r'[\s/-]+'             # separator between day and month
        r'([A-Za-zА-Яа-я]{3,10})'  # month abbreviation
        r'(?:\s*/\s*[A-Za-zА-Яа-я]{3,10})?'  # optional second month (e.g., "MAI" in "MAY / MAI")
        r'[\s/-]+'             # separator between month and year
        r'(\d{2,4})',          # year
        date_str
    )
    
    if not match:
        return None

    try:
        day = int(match.group(1))
        month_str = match.group(2).upper()
        year = int(match.group(3))

        if year < 100:
            current_year = datetime.now().year
            century = 2000 if year <= (current_year % 100) + 20 else 1900
            year = century + year

        month = MONTH_NAMES.get(month_str)
        if month is None:
            month = MONTH_NAMES.get(month_str[:3])
        if month is None:
            month = MONTH_NAMES.get(month_str[:4])
        if month is None:
            return None

        datetime(year, month, day)
        return (day, month, year)
    except (ValueError, TypeError):
        return None


def normalize_date(date_str):
    """
    Attempts to normalize various date formats to YYYY-MM-DD.
    Supports YYMMDD (from MRZ), DD/MM/YYYY, DD.MM.YYYY, YYYY/MM/DD, and wordy formats.
    """
    if not date_str:
        return None
    
    # Try month-name date format first (e.g., "15 MAY 1990")
    month_date = _parse_month_name_date(date_str)
    if month_date:
        day, month, year = month_date
        return f"{year:04d}-{month:02d}-{day:02d}"
    
    # Clean text first — handle commas and colons which OCR sometimes produces instead of dots
    date_str = re.sub(r'[\s\-/. ,:;]+', ' ', date_str).strip()
    
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
