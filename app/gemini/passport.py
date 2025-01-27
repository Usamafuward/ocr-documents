import google.generativeai as genai
import base64
from dotenv import load_dotenv
import os
import json
import PIL.Image
from io import BytesIO
from app.models.passport import PassportInfo

load_dotenv()

def setup_gemini(api_key: str):
    """Initialize Gemini with API key"""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash-exp')

def extract_passport_info(uploaded_image) -> PassportInfo:
    """
    Extract passport information using Gemini vision model and validate with Pydantic
    """
    model = setup_gemini(os.getenv("GEMINI_API_KEY"))
    
    # Convert bytes to PIL Image using BytesIO
    try:
        # If uploaded_image is already in bytes
        if isinstance(uploaded_image, bytes):
            image = PIL.Image.open(BytesIO(uploaded_image))
        # If uploaded_image is a file-like object
        else:
            image_data = uploaded_image.read()
            image = PIL.Image.open(BytesIO(image_data))
            # Reset file pointer for later use
            uploaded_image.seek(0)
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")
    
    # Prepare the prompt for Gemini
    prompt = """
    First, determine if the provided image is a Passport. If the image is not a Passport, return null for all fields in the JSON structure.

    If the image is a Passport, analyze it carefully and provide the information in valid JSON format with the following fields:
    {
        "surname": "family name/surname",
        "name": "other names (excluding surname)",
        "passport_number": "passport number",
        "nic_number": "national ID number if available, null if not found Example : 123456789 V - old format, 123456789012 - new format",
        "nationality": "country of nationality",
        "sex": "Give Male or Female if M or F is visible",
        "document_type": "type of passport (e.g., PA-Regular, PB-Diplomatic)",
        "date_of_birth": "YYYY-MM-DD",
        "date_of_issue": "YYYY-MM-DD",
        "date_of_expiry": "YYYY-MM-DD",
        "mrz_code": "MRZ code line by line break the code if visible, null if not visible"
    }
    
    Important instructions:
    1. Extract text from both the main part and the MRZ (Machine Readable Zone) at the bottom
    2. For dates, convert to YYYY-MM-DD format
    3. Ensure name and surname are properly separated
    4. Check both visual and MRZ parts to ensure accuracy
    5. Return exact text as shown, do not correct or modify spellings
    6. If a field is not visible or cannot be determined, set it to null
    
    Ensure the response is valid JSON format.
    """
    
    # Generate response using Gemini
    response = model.generate_content([prompt, image])
    
    # Extract JSON from response
    try:
        # Clean up the response text to get only the JSON part
        response_text = response.text
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        json_str = response_text[json_start:json_end]
        
        # Parse JSON and create PassportInfo object
        passport_data = json.loads(json_str)
        return PassportInfo(**passport_data)
    except Exception as e:
        raise ValueError(f"Failed to parse Gemini response: {str(e)}\nResponse text: {response_text}")

def process_gemini_passport(uploaded_image) -> dict:
    """
    Main function to process passport image and return structured data
    """
    if uploaded_image:
        # Extract information
        passport_info = extract_passport_info(uploaded_image)
        
        # Convert to dictionary for JSON serialization
        passport_dict = passport_info.dict()
        
        # Convert dates to strings for JSON serialization
        passport_dict['date_of_birth'] = str(passport_dict['date_of_birth'])
        passport_dict['date_of_issue'] = str(passport_dict['date_of_issue'])
        passport_dict['date_of_expiry'] = str(passport_dict['date_of_expiry'])
        
        transformed_dict = {
            ' '.join(word.capitalize() for word in key.split('_')): value
            for key, value in passport_dict.items()
        }
        
        # Handle image data for base64 conversion
        if isinstance(uploaded_image, bytes):
            image_data = base64.b64encode(uploaded_image).decode('utf-8')
        else:
            image_data = base64.b64encode(uploaded_image.read()).decode('utf-8')
            uploaded_image.seek(0)  # Reset file pointer
        
        return {
            "image_data": image_data,
            "extracted_info": transformed_dict
        }
    
    raise ValueError("No image provided")