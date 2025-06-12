from typing import Optional
from datetime import date
from pydantic import BaseModel, Field
import google.generativeai as genai
import base64
from dotenv import load_dotenv
import os
import json
from google.generativeai.types import content_types
import PIL.Image
from io import BytesIO
from app.models.drlicence import LicenceInfo

load_dotenv()

def setup_gemini(api_key: str):
    """Initialize Gemini with API key"""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def extract_licence_info(uploaded_image) -> LicenceInfo:
    """
    Extract licence information using Gemini vision model and validate with Pydantic
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
    First, determine if the provided image is a Driving licence. If the image is not a Driving licence, return null for all fields in the JSON structure.

    If the image is a Driving licence, analyze it carefully and provide the information in valid JSON format with the following fields:
    {
        "name": "1,2. full name",
        "licence_number": "5. number",
        "nic_number": "4d. number or 4c. number, Example : 123456789 V - old format, 123456789012 - new format",
        "address": "8. complete address",
        "date_of_birth": "3.YYYY-MM-DD",
        "date_of_issue": "4a. YYYY-MM-DD",
        "date_of_expiry": "4b. YYYY-MM-DD",
        "blood_group": "group if available, null if not Example : A+, B-"
    }
    
    Ensure all dates are in YYYY-MM-DD format and the response is valid JSON.
    """
    
    # Generate response using Gemini
    response = model.generate_content([prompt, image])
    
    print(response.text)
    
    # Extract JSON from response
    try:
        # Clean up the response text to get only the JSON part
        response_text = response.text
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        json_str = response_text[json_start:json_end]
        
        # Parse JSON and create LicenceInfo object
        licence_data = json.loads(json_str)
        return LicenceInfo(**licence_data)
    except Exception as e:
        raise ValueError(f"Failed to parse Gemini response: {str(e)}")

def process_gemini_licence(uploaded_image) -> dict:
    """
    Main function to process licence image and return structured data
    """
    if uploaded_image:
        # Extract information
        licence_info = extract_licence_info(uploaded_image)
        
        # Convert to dictionary for JSON serialization
        licence_dict = licence_info.dict()
        
        # Convert dates to strings for JSON serialization
        licence_dict['date_of_birth'] = str(licence_dict['date_of_birth'])
        licence_dict['date_of_issue'] = str(licence_dict['date_of_issue'])
        licence_dict['date_of_expiry'] = str(licence_dict['date_of_expiry'])
        
        transformed_dict = {
            ' '.join(word.capitalize() for word in key.split('_')): value
            for key, value in licence_dict.items()
        }
        
        # Handle image data for base64 conversion
        if isinstance(uploaded_image, bytes):
            image_data = base64.b64encode(uploaded_image).decode('utf-8')
        else:
            image_data = base64.b64encode(uploaded_image.read()).decode('utf-8')
            uploaded_image.seek(0)  # Reset file pointer
            
        if "Licence Number" not in transformed_dict:
            return {
                "image_data": image_data,
                "extracted_info": {}
            }
        
        return {
            "image_data": image_data,
            "extracted_info": transformed_dict
        }
    
    raise ValueError("No image provided")
