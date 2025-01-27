from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import logging
from io import BytesIO
from passporteye import read_mrz
import pandas as pd
import base64

# Initialize logging and PaddleOCR
logging.getLogger('ppocr').setLevel(logging.ERROR)
ocr = PaddleOCR(lang='en')

# Load country data
try:
    country_df = pd.read_csv('countries.csv')
    country_dict = dict(zip(country_df['ISO Code'], country_df['Country']))
except:
    country_dict = {}  # Fallback if CSV not found

def extract_passport_info(image_bytes):
    """
    Extract passport information using both PassportEye and PaddleOCR
    """
    # Convert bytes to PIL Image for OCR
    image = Image.open(BytesIO(image_bytes))
    
    # Extract MRZ data
    mrz_data = extract_mrz_data(BytesIO(image_bytes))
    
    # Extract additional text using PaddleOCR
    image_array = np.array(image)
    result = ocr.ocr(image_array, rec=True)
    ocr_text = " ".join([line[1][0] for line in result[0]])
    
    # Combine and return all extracted data
    return mrz_data, "passport" in ocr_text.lower()

def extract_mrz_data(image_stream):
    """Extract MRZ data from passport image"""
    try:
        mrz = read_mrz(image_stream, save_roi=True)
        if mrz is None:
            return {
                "Name": None,
                "Surname": None,
                "Nic Number": None,
                "Passport Number": None,
                "Country": None,
                "Sex": None,
                "Type": None,
                "MRZ Code": None,
                "Date Of Expiry": None,
                "Date Of Issue": None,
                "Date Of Birth": None
            }
        
        mrz_data = mrz.to_dict()
        
        # Clean and format data
        cleaned_data = {
            "Name": mrz_data.get('names', '').replace('<', ' ').strip() or None,
            "Surname": mrz_data.get('surname', '').replace('<', ' ').strip() or None,
            "Nic Number": mrz_data.get('personal_number', '').replace('<', '') or None,
            "Passport Number": mrz_data.get('number', '').replace('<', '') or None,
            "Country": country_dict.get(mrz_data.get('nationality', '').replace('<', ''), None),
            "Sex": 'Female' if mrz_data.get('sex', '') == 'F' else 'Male' if mrz_data.get('sex', '') == 'M' else None,
            "Type": mrz_data.get('type', '') or None,
            "MRZ Code": mrz_data.get('raw_text', '') or None,
            "Date Of Expiry": None,
            "Date Of Issue": None,
            "Date Of Birth": None
        }
        
        # Format dates
        expiration = mrz_data.get('expiration_date', '')
        if len(expiration) == 6 and expiration.isdigit():
            year, month, day = expiration[:2], expiration[2:4], expiration[4:]
            cleaned_data['Date Of Expiry'] = f"20{year}-{month}-{day}"
            issue_year = str(int("20" + year) - 10)
            cleaned_data['Date Of Issue'] = f"{issue_year}-{month}-{day}"
        
        dob = mrz_data.get('date_of_birth', '')
        if len(dob) == 6 and dob.isdigit():
            year, month, day = dob[:2], dob[2:4], dob[4:]
            year_prefix = "19" if "V" in (cleaned_data['Nic Number'] or '') else "20"
            cleaned_data['Date Of Birth'] = f"{year_prefix}{year}-{month}-{day}"
        
        return cleaned_data
    except Exception as e:
        print(f"Error extracting MRZ data: {e}")
        return {
            "Name": None,
            "Surname": None,
            "Nic Number": None,
            "Passport Number": None,
            "Country": None,
            "Sex": None,
            "Type": None,
            "MRZ Code": None,
            "Date Of Expiry": None,
            "Date Of Issue": None,
            "Date Of Birth": None
        }

def process_ocr_passport(uploaded_image):
    """Process OCR and extract information"""
    if uploaded_image:
        try:
            # Extract information
            extracted_info, is_passport = extract_passport_info(uploaded_image)
            
            # Convert image for display
            image_data = base64.b64encode(uploaded_image).decode('utf-8')
            
            return dict(
                image_data=image_data,
                extracted_info=extracted_info,
                is_passport=is_passport
            )
        except Exception as e:
            print(f"Error processing image: {e}")
            return dict(
                image_data=None,
                extracted_info={
                    "Name": None,
                    "Surname": None,
                    "Nic Number": None,
                    "Passport Number": None,
                    "Country": None,
                    "Sex": None,
                    "Type": None,
                    "MRZ Code": None,
                    "Date Of Expiry": None,
                    "Date Of Issue": None,
                    "Date Of Birth": None
                },
                is_passport=False
            )
    else:
        return dict(
            image_data=None,
            extracted_info={
                "Name": None,
                "Surname": None,
                "Nic Number": None,
                "Passport Number": None,
                "Country": None,
                "Sex": None,
                "Type": None,
                "MRZ Code": None,
                "Date Of Expiry": None,
                "Date Of Issue": None,
                "Date Of Birth": None
            },
            is_passport=False
        )