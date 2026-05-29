import re
import sys
import os
from datetime import datetime

# Adjust path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.validators import validate_passport_number, normalize_date, clean_text

def is_latin_text(text):
    if not text:
        return False
    cleaned = re.sub(r'[^A-Za-z\s]', '', text).strip()
    if re.search(r'[\u0400-\u04FF]', text):
        return False
    return len(cleaned) >= 2

def extract_latin_part(text):
    if not text:
        return ""
    # Split by common separators
    parts = re.split(r'[/\\,;]', text)
    for part in parts:
        part_clean = part.strip()
        if re.search(r'[A-Za-z]', part_clean) and not re.search(r'[\u0400-\u04FF]', part_clean):
            # Keep letters, spaces, and standard hyphens/dots
            part_clean = re.sub(r'[^A-Za-z\s\-.]', '', part_clean).strip()
            if len(part_clean) >= 2:
                return part_clean
    return ""

class TextParser:
    def __init__(self):
        pass

    def parse(self, ocr_results):
        lines = [clean_text(item['text']) for item in ocr_results if item.get('text')]
        confidences = [item.get('confidence', 0.5) for item in ocr_results if item.get('text')]
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        parsed_data = {
            "passport_number": None,
            "full_name": None,
            "date_of_birth": None,
            "nationality": None,
            "gender": None,
            "expiry_date": None,
            "confidence": avg_confidence,
            "mrz_detected": False
        }

        # Step 1: MRZ Parsing (Primary Priority)
        mrz_lines = self._extract_mrz_lines(lines)
        if mrz_lines and len(mrz_lines) >= 2:
            try:
                mrz_parsed = self._parse_mrz(mrz_lines[0], mrz_lines[1])
                parsed_data.update(mrz_parsed)
                parsed_data["mrz_detected"] = True
                
                if parsed_data["passport_number"]:
                    parsed_data["confidence"] = max(parsed_data["confidence"], 0.95)
                    parsed_data["date_of_birth"] = normalize_date(parsed_data["date_of_birth"])
                    parsed_data["expiry_date"] = normalize_date(parsed_data["expiry_date"])
                    return parsed_data
            except Exception as e:
                print(f"MRZ parsing failed: {str(e)}")

        # Step 2: Visual Parser Fallback (Secondary Priority)
        visual_data = self._parse_visual_fields(lines)
        for key, val in visual_data.items():
            if not parsed_data.get(key) and val:
                parsed_data[key] = val

        # Standardize gender
        if parsed_data.get("gender"):
            gender_val = str(parsed_data["gender"]).upper().strip()
            if 'M' in gender_val:
                parsed_data["gender"] = 'M'
            elif 'F' in gender_val:
                parsed_data["gender"] = 'F'
            else:
                parsed_data["gender"] = None

        # Standardize Passport Number
        if parsed_data.get("passport_number"):
            parsed_data["passport_number"] = re.sub(r'[^A-Z0-9]', '', parsed_data["passport_number"].upper())
            
        parsed_data["date_of_birth"] = normalize_date(parsed_data.get("date_of_birth"))
        parsed_data["expiry_date"] = normalize_date(parsed_data.get("expiry_date"))

        # Heuristic quality-score adjustment
        valid_fields = 0
        total_fields = 5
        
        if validate_passport_number(parsed_data.get("passport_number")): valid_fields += 1
        if parsed_data.get("full_name") and len(parsed_data["full_name"]) > 3: valid_fields += 1
        if parsed_data.get("date_of_birth") and '-' in str(parsed_data["date_of_birth"]): valid_fields += 1
        if parsed_data.get("expiry_date") and '-' in str(parsed_data["expiry_date"]): valid_fields += 1
        if parsed_data.get("nationality"): valid_fields += 1
        
        field_score = valid_fields / total_fields
        parsed_data["confidence"] = round((parsed_data["confidence"] * 0.3) + (field_score * 0.7), 2)

        return parsed_data

    def _extract_mrz_lines(self, lines):
        cleaned_lines = []
        for line in lines:
            # Clean up common OCR symbol misreads to support MRZ parsing
            cleaned = line.strip().upper()
            cleaned = re.sub(r'\s+', '', cleaned)
            for char in ['(', ')', '{', '}', '[', ']', '«', '»', '¢', '£', '¥', '\\', '|', '/', ':', ';']:
                cleaned = cleaned.replace(char, '<')
            cleaned_lines.append(cleaned)
            
        first_line = None
        second_line = None
        first_line_idx = -1
        
        # 1. Locate the first line starting with P
        for idx, cleaned in enumerate(cleaned_lines):
            if (cleaned.startswith('P<') or cleaned.startswith('P_') or re.match(r'^P[<A-Z_]{4,}', cleaned)) and len(cleaned) >= 32:
                first_line = cleaned
                first_line_idx = idx
                break
                
        if first_line_idx != -1:
            # 2. Locate the second line (usually right below the first)
            for offset in range(1, 4):
                next_idx = first_line_idx + offset
                if next_idx < len(cleaned_lines):
                    cand = cleaned_lines[next_idx]
                    # Second line is alphanumeric, length 32-50, and doesn't start with P<
                    if len(cand) >= 32 and not (cand.startswith('P<') or cand.startswith('P_')):
                        second_line = cand
                        break
                        
        if first_line and second_line:
            # Pad to standard 44 characters if needed
            first_line = first_line.ljust(44, '<')[:44]
            second_line = second_line.ljust(44, '<')[:44]
            return [first_line, second_line]
            
        return []

    def _parse_mrz(self, line1, line2):
        data = {}
        
        # Line 1: Country & Name details
        country_code = line1[2:5].replace('<', '').strip()
        data["nationality"] = country_code
        
        name_part = line1[5:]
        if '<<' in name_part:
            parts = name_part.split('<<')
            surname = parts[0].replace('<', ' ').strip()
            given_names = parts[1].replace('<', ' ').strip()
            data["full_name"] = f"{given_names} {surname}".strip()
        else:
            data["full_name"] = name_part.replace('<', ' ').strip()

        # Clean/Standardize Name spaces
        if data.get("full_name"):
            data["full_name"] = re.sub(r'\s+', ' ', data["full_name"]).title()

        # Line 2: Passport Number & Dates
        raw_passport_num = line2[0:9]
        passport_num = ""
        for char in raw_passport_num:
            if char == 'O': passport_num += '0'
            elif char == 'I': passport_num += '1'
            elif char == 'Z': passport_num += '2'
            else: passport_num += char
        data["passport_number"] = passport_num.replace('<', '').strip()
        
        raw_dob = line2[13:19]
        dob_clean = ""
        for char in raw_dob:
            if char == 'O': dob_clean += '0'
            elif char == 'I': dob_clean += '1'
            else: dob_clean += char
        data["date_of_birth"] = dob_clean
        
        gender = line2[20]
        if gender == 'M':
            data["gender"] = 'M'
        elif gender == 'F':
            data["gender"] = 'F'
        else:
            data["gender"] = None
            
        raw_expiry = line2[21:27]
        expiry_clean = ""
        for char in raw_expiry:
            if char == 'O': expiry_clean += '0'
            elif char == 'I': expiry_clean += '1'
            else: expiry_clean += char
        data["expiry_date"] = expiry_clean
        
        return data

    def _parse_visual_fields(self, lines):
        data = {
            "passport_number": None,
            "full_name": None,
            "date_of_birth": None,
            "nationality": None,
            "gender": None,
            "expiry_date": None
        }

        full_text = " ".join(lines)

        # 1. Search for Passport Number
        passport_patterns = [
            r'PASSPORT\s+NO\.?\s*([A-Z0-9]{8,12})',
            r'PASSEPORT\s+N[O°]\.?\s*([A-Z0-9]{8,12})',
            r'No\.?\s*([A-Z0-9]{8,12})',
            r'\b([A-Z][0-9]{8,11})\b',
            r'\b([0-9]{9,12})\b'
        ]
        for pattern in passport_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data["passport_number"] = match.group(1)
                break

        # 2. Extract Name via Label Detection
        surname = ""
        given_names = ""
        for i, line in enumerate(lines):
            # Check Surname labels
            if re.search(r'SURNAME|NOM|FAMILY\s+NAME|HACAB', line, re.IGNORECASE):
                for offset in [1, 2]:
                    if i + offset < len(lines):
                        cand = lines[i+offset].strip()
                        latin = extract_latin_part(cand)
                        if latin:
                            surname = latin
                            break
                        elif is_latin_text(cand):
                            surname = cand
                            break
                if not surname and i + 1 < len(lines):
                    surname = lines[i+1].strip()

            # Check Given Name labels
            if re.search(r'GIVEN\s+NAMES|PRENOMS|NAME|HOML', line, re.IGNORECASE):
                for offset in [1, 2]:
                    if i + offset < len(lines):
                        cand = lines[i+offset].strip()
                        latin = extract_latin_part(cand)
                        if latin:
                            given_names = latin
                            break
                        elif is_latin_text(cand):
                            given_names = cand
                            break
                if not given_names and i + 1 < len(lines):
                    given_names = lines[i+1].strip()

        if surname or given_names:
            data["full_name"] = f"{given_names} {surname}".strip().title()
        else:
            # Fallback search for full name lines
            for line in lines[2:10]:
                if line.isupper() and len(line.split()) >= 2 and not any(lbl in line for lbl in ["PASSPORT", "UNITED", "REPUBLIC", "OFFICE", "STATE", "COUNTRY", "NOM", "PRENOM", "TAJIKISTAN"]):
                    data["full_name"] = line.strip().title()
                    break

        # 3. Extract Nationality via Label Detection
        for i, line in enumerate(lines):
            if re.search(r'NATIONALITY|NATIONALITE|WAXPBAH', line, re.IGNORECASE):
                for offset in [1, 2]:
                    if i + offset < len(lines):
                        cand = lines[i+offset].strip()
                        latin = extract_latin_part(cand)
                        if latin:
                            data["nationality"] = latin
                            break
                        elif is_latin_text(cand):
                            data["nationality"] = cand
                            break

        # 4. Extract Birth and Expiry Dates
        dob_keywords = ["BIRTH", "NAISSANCE", "NE", "DOB", "TABA\u041B\u041B\u0423\u0414"]
        expiry_keywords = ["EXPIRY", "EXPIRATION", "EXP", "\u042d\u0421\u0422\u0418\u0411\u041e\u0420"]
        
        # Support periods, commas, colons, slashes, spaces
        date_pattern = r'(\b\d{1,2}[-/. ,:;]+(?:\d{1,2}|[A-Za-z]{3,10})[-/. ,:;]+\d{2,4}\b)'
        
        for i, line in enumerate(lines):
            if any(k in line.upper() for k in dob_keywords):
                for offset in [0, 1, -1, 2]:
                    if 0 <= i + offset < len(lines):
                        match = re.search(date_pattern, lines[i+offset])
                        if match:
                            data["date_of_birth"] = match.group(1)
                            break
            if any(k in line.upper() for k in expiry_keywords):
                for offset in [0, 1, -1, 2]:
                    if 0 <= i + offset < len(lines):
                        match = re.search(date_pattern, lines[i+offset])
                        if match:
                            data["expiry_date"] = match.group(1)
                            break

        # 5. Extract Gender / Sex
        for line in lines:
            cleaned = re.sub(r'[\s/]+', '', line).upper()
            if cleaned == 'M' or cleaned == 'F' or cleaned == 'MM' or cleaned == 'FF':
                data["gender"] = 'M' if 'M' in cleaned else 'F'
                break

        return data
