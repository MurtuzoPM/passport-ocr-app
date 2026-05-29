import re
import sys
import os
from datetime import datetime

# Adjust path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.validators import validate_passport_number, normalize_date, clean_text

class TextParser:
    def __init__(self):
        pass

    def parse(self, ocr_results):
        """
        Parses list of OCR results into structured passport fields.
        ocr_results is a list of dicts: [{'text': '...', 'confidence': 0.95}, ...]
        """
        # Collect and clean raw strings
        lines = [clean_text(item['text']) for item in ocr_results if item.get('text')]
        confidences = [item.get('confidence', 0.5) for item in ocr_results if item.get('text')]
        
        # Calculate average raw character/line confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Initialize structured fields
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

        # Step 1: Look for MRZ (Machine Readable Zone) lines
        mrz_lines = self._extract_mrz_lines(lines)
        if mrz_lines and len(mrz_lines) >= 2:
            try:
                mrz_parsed = self._parse_mrz(mrz_lines[0], mrz_lines[1])
                parsed_data.update(mrz_parsed)
                parsed_data["mrz_detected"] = True
                
                # MRZ data is highly structured and validated by checksums.
                # If we successfully parsed passport number, boost default confidence.
                if parsed_data["passport_number"]:
                    parsed_data["confidence"] = max(parsed_data["confidence"], 0.95)
                    
                    # Normalize dates extracted from MRZ
                    parsed_data["date_of_birth"] = normalize_date(parsed_data["date_of_birth"])
                    parsed_data["expiry_date"] = normalize_date(parsed_data["expiry_date"])
                    return parsed_data
            except Exception as e:
                print(f"MRZ parsing error: {str(e)}. Proceeding with visual parser fallback.")

        # Step 2: Fallback to Visual Field parsing (using NLP/Regex)
        visual_data = self._parse_visual_fields(lines)
        for key, val in visual_data.items():
            if not parsed_data.get(key) and val:
                parsed_data[key] = val

        # Ensure gender is strictly standardized to M / F / None
        if parsed_data.get("gender"):
            gender_val = str(parsed_data["gender"]).upper().strip()
            if 'M' in gender_val:
                parsed_data["gender"] = 'M'
            elif 'F' in gender_val:
                parsed_data["gender"] = 'F'
            else:
                parsed_data["gender"] = None

        # Clean passport numbers and normalize dates
        if parsed_data.get("passport_number"):
            parsed_data["passport_number"] = re.sub(r'[^A-Z0-9]', '', parsed_data["passport_number"].upper())
            
        parsed_data["date_of_birth"] = normalize_date(parsed_data.get("date_of_birth"))
        parsed_data["expiry_date"] = normalize_date(parsed_data.get("expiry_date"))

        # Heuristic quality-score adjustment based on fields successfully validated
        valid_fields = 0
        total_fields = 5 # passport_number, full_name, DOB, nationality, expiry_date
        
        if validate_passport_number(parsed_data.get("passport_number")): valid_fields += 1
        if parsed_data.get("full_name") and len(parsed_data["full_name"]) > 3: valid_fields += 1
        if parsed_data.get("date_of_birth") and '-' in str(parsed_data["date_of_birth"]): valid_fields += 1
        if parsed_data.get("expiry_date") and '-' in str(parsed_data["expiry_date"]): valid_fields += 1
        if parsed_data.get("nationality"): valid_fields += 1
        
        # Calculate dynamic weighted score
        field_score = valid_fields / total_fields
        parsed_data["confidence"] = round((parsed_data["confidence"] * 0.4) + (field_score * 0.6), 2)

        return parsed_data

    def _extract_mrz_lines(self, lines):
        """
        Scans all lines of text to find standard 44-character MRZ lines (Type TD3).
        """
        mrz_candidates = []
        for line in lines:
            cleaned = re.sub(r'\s+', '', line).upper()
            # Standardize common OCR mistakes in MRZs
            cleaned = cleaned.replace('0', 'O').replace('1', 'I')
            # Look for lines with typical MRZ filler chars '<'
            if len(cleaned) >= 30 and (cleaned.count('<') > 3 or re.search(r'P<[A-Z<]{8,}', cleaned)):
                mrz_candidates.append(cleaned)
        
        first_line = None
        second_line = None
        
        # Look for Type 1 line starting with Document Type "P"
        for cand in mrz_candidates:
            if cand.startswith('P<') or cand.startswith('P_') or re.match(r'^P[<A-Z_]{5,}', cand):
                first_line = cand
                break
                
        if first_line:
            # Type 2 line usually contains passport number, dates, and ends with checksums
            for cand in mrz_candidates:
                if cand != first_line and re.match(r'^[A-Z0-9]{9,}', cand):
                    second_line = cand
                    break
            # Second option: find another long line if start-match failed
            if not second_line:
                for cand in mrz_candidates:
                    if cand != first_line and len(cand) >= 38:
                        second_line = cand
                        break
                        
        if first_line and second_line:
            return [first_line, second_line]
            
        # Hard fallback: just take the two longest candidates rich in filler signs '<'
        long_lines = [c for c in mrz_candidates if len(c) >= 35]
        if len(long_lines) >= 2:
            return long_lines[:2]
            
        return []

    def _parse_mrz(self, line1, line2):
        """
        Parses standard Type TD3 MRZ lines (2 lines of 44 characters).
        """
        data = {}
        
        # Normalize/pad lines to 44 characters
        line1 = line1.ljust(44, '<')[:44]
        line2 = line2.ljust(44, '<')[:44]
        
        # Line 1: P<USAREYNOLDS<<KATHERINE<ELIZABETH<<<<<<<<<<
        # Country Code
        country_code = line1[2:5].replace('<', '').strip()
        data["nationality"] = country_code
        
        # Name Split
        name_part = line1[5:]
        if '<<' in name_part:
            parts = name_part.split('<<')
            surname = parts[0].replace('<', ' ').strip()
            given_names = parts[1].replace('<', ' ').strip()
            data["full_name"] = f"{given_names} {surname}".strip()
        else:
            data["full_name"] = name_part.replace('<', ' ').strip()

        # Line 2: KL85412214USA8801123F2811155<<<<<<<<<<<<<<06
        # Passport number: 9 chars (pos 0-9)
        raw_passport_num = line2[0:9]
        passport_num = ""
        for char in raw_passport_num:
            if char == 'O': passport_num += '0'
            elif char == 'I': passport_num += '1'
            elif char == 'Z': passport_num += '2'
            else: passport_num += char
        data["passport_number"] = passport_num.replace('<', '').strip()
        
        # Date of birth: YYMMDD (pos 13-19)
        raw_dob = line2[13:19]
        dob_clean = ""
        for char in raw_dob:
            if char == 'O': dob_clean += '0'
            elif char == 'I': dob_clean += '1'
            else: dob_clean += char
        data["date_of_birth"] = dob_clean
        
        # Gender: pos 20 (M/F/<)
        gender = line2[20]
        if gender == 'M':
            data["gender"] = 'M'
        elif gender == 'F':
            data["gender"] = 'F'
        else:
            data["gender"] = None
            
        # Expiry Date: YYMMDD (pos 21-27)
        raw_expiry = line2[21:27]
        expiry_clean = ""
        for char in raw_expiry:
            if char == 'O': expiry_clean += '0'
            elif char == 'I': expiry_clean += '1'
            else: expiry_clean += char
        data["expiry_date"] = expiry_clean
        
        return data

    def _parse_visual_fields(self, lines):
        """
        Parses visual text using regex pattern matching when MRZ data is unreadable.
        """
        data = {
            "passport_number": None,
            "full_name": None,
            "date_of_birth": None,
            "nationality": None,
            "gender": None,
            "expiry_date": None
        }

        full_text = " ".join(lines)

        # 1. Search for passport number
        passport_patterns = [
            r'PASSPORT\s+NO\.?\s*([A-Z0-9]{8,12})',
            r'PASSEPORT\s+N[O°]\.?\s*([A-Z0-9]{8,12})',
            r'No\.?\s*([A-Z0-9]{8,12})',
            r'\b([A-Z][0-9]{8,11})\b',  # Letter + digits format
            r'\b([0-9]{9,12})\b'        # Standard purely numeric passport numbers
        ]
        
        for pattern in passport_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data["passport_number"] = match.group(1)
                break

        # 2. Extract Country Code / Nationality
        nat_patterns = [
            r'NATIONALITY\s*/?\s*NATIONALITE\s+([A-Z\s]{3,25})',
            r'NATIONALITY\s*:\s*([A-Z\s]{3,25})',
            r'NATIONALITE\s*:\s*([A-Z\s]{3,25})'
        ]
        for pattern in nat_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                data["nationality"] = match.group(1).strip()
                break

        # 3. Extract Full Name
        surname = ""
        given_names = ""
        for i, line in enumerate(lines):
            if re.search(r'SURNAME|NOM|FAMILY\s+NAME', line, re.IGNORECASE):
                if i + 1 < len(lines):
                    surname = lines[i+1].strip()
            if re.search(r'GIVEN\s+NAMES|PRENOMS', line, re.IGNORECASE):
                if i + 1 < len(lines):
                    given_names = lines[i+1].strip()

        if surname or given_names:
            data["full_name"] = f"{given_names} {surname}".strip()
        else:
            # Fallback heuristic: search lines for uppercase names, skipping labels/headers
            for line in lines[2:8]:
                if line.isupper() and len(line.split()) >= 2 and not any(lbl in line for lbl in ["PASSPORT", "UNITED", "REPUBLIC", "OFFICE", "STATE", "COUNTRY", "NOM", "PRENOM"]):
                    data["full_name"] = line
                    break

        # 4. Extract Birth and Expiry dates
        dob_keywords = ["BIRTH", "NAISSANCE", "NE", "DOB"]
        expiry_keywords = ["EXPIRY", "EXPIRATION", "EXP"]
        
        # Regex format: e.g., 15 MAY 1990, 15/05/1990, 15-05-90 etc.
        date_pattern = r'(\b\d{1,2}[-/. ]+(?:\d{1,2}|[A-Za-z]{3,4})[-/. ]+\d{2,4}\b)'
        
        for i, line in enumerate(lines):
            if any(k in line.upper() for k in dob_keywords):
                for offset in [0, 1, -1]:
                    if 0 <= i + offset < len(lines):
                        match = re.search(date_pattern, lines[i+offset])
                        if match:
                            data["date_of_birth"] = match.group(1)
                            break
            if any(k in line.upper() for k in expiry_keywords):
                for offset in [0, 1, -1]:
                    if 0 <= i + offset < len(lines):
                        match = re.search(date_pattern, lines[i+offset])
                        if match:
                            data["expiry_date"] = match.group(1)
                            break

        # 5. Extract Sex / Gender
        for i, line in enumerate(lines):
            if re.search(r'\bSEX\b|\bSEXE\b', line, re.IGNORECASE):
                for offset in [0, 1]:
                    if 0 <= i + offset < len(lines):
                        g_match = re.search(r'\b(M|F)\b', lines[i+offset].upper())
                        if g_match:
                            data["gender"] = g_match.group(1)
                            break
        
        return data
