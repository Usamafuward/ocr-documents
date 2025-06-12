import google.generativeai as genai
import base64
from dotenv import load_dotenv
import os
import json
from google.generativeai.types import content_types
import PIL.Image
from io import BytesIO
from app.models.crbook import CRBookInfo

load_dotenv()

def setup_gemini(api_key: str):
    """Initialize Gemini with API key"""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def extract_crbook_info(uploaded_image) -> CRBookInfo:
    """
    Extract CR book information using Gemini vision model and validate with Pydantic
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
    First, determine if the provided image is a CR book. If the image is not a CR book, return null for all fields in the JSON structure.

    If the image is a CR book, analyze it carefully and provide the information in valid JSON format with the following fields:
    {
        "cr_book_number": "CR book number",
        "registration_number": "Vehicle registration number",
        "chassis_number": "Chassis number of the vehicle",
        "engine_number": "Engine number of the vehicle",
        "cylinder_capacity": "Cylinder capacity of the vehicle",
        "class_of_vehicle": "Class of the vehicle (e.g., Motorcycle, Car)",
        "taxation_class": "Taxation class of the vehicle",
        "status_when_registered": "Status of the vehicle when registered (e.g., Brand New, Reconditioned)",
        "fuel_type": "Fuel type of the vehicle (e.g., Petrol, Diesel)",
        "provincial_council": "Provincial council of registration if available, null if not found",
        "date_of_registration": "Date of registration in YYYY-MM-DD format if available, null if not found",
        "owner_name": "Name of the current owner if available, null if not found",
        "absolute_owner": "Name of the absolute owner if available, null if not found",
        "absolute_owner_reference_date": "Reference date for absolute owner if available, null if not found",
        "previous_owners": "Number of previous owners if available, null if not found",
        "previous_owner_details": "List of string containing previous owner details it's should be list. Example: '1. Name = Mercantile investments and finance 3, Address = No 236, Galle road, Colombo 03, Transfered Date = 23/11/2016'",
        "make": "Make of the vehicle if available, null if not found",
        "model": "Model of the vehicle if available, null if not found",
        "color": "Color of the vehicle if available, null if not found",
        "year_of_manufacture": "Year of manufacture if available, null if not found",
        "country_of_origin": "Country of origin of the vehicle if available, null if not found",
        "wheelbase": "Wheelbase of the vehicle if available, null if not found",
        "seating_capacity": "Seating capacity of the vehicle if available, null if not found",
        "gross_weight": "Gross weight of the vehicle if available, null if not found",
        "unladen_weight": "Unladen weight of the vehicle in KG if available, null if not found",
        "type_of_body": "Type of body of the vehicle if available, null if not found",
        "overhang": "Overhang details of the vehicle if available, null if not found",
        "tire_size_front": "Front tire size if available, null if not found",
        "tire_size_rear": "Rear tire size if available, null if not found",
        "vehicle_dimensions": "Vehicle dimensions (length = value, width = value, height = value) if available, null if not found",
        "printed_date": "Date of printed in YYYY-MM-DD format if available, null if not found"
    }

    Important instructions:
    1. First, check if the image is a CR book. If not, return null for all fields.
    2. If the image is a CR book, extract text from both the main part and any additional sections.
    3. For dates, convert to YYYY-MM-DD format.
    4. Ensure all fields are properly extracted.
    5. Return exact text as shown, do not correct or modify spellings.
    6. If a field is not visible or cannot be determined, set it to null.

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
        
        # Parse JSON and create CRBookInfo object
        crbook_data = json.loads(json_str)
        return CRBookInfo(**crbook_data)
    except Exception as e:
        raise ValueError(f"Failed to parse Gemini response: {str(e)}\nResponse text: {response_text}")

def process_gemini_cr_book(uploaded_image) -> dict:
    """
    Main function to process CR book image and return structured data
    """
    if uploaded_image:
        # Extract information
        crbook_info = extract_crbook_info(uploaded_image)
        
        # Convert to dictionary for JSON serialization
        crbook_dict = crbook_info.dict()
        
        # Convert dates to strings for JSON serialization
        if crbook_dict['date_of_registration']:
            crbook_dict['date_of_registration'] = str(crbook_dict['date_of_registration'])
        if crbook_dict['printed_date']:
            crbook_dict['printed_date'] = str(crbook_dict['printed_date'])
            
        transformed_dict = {
            ' '.join(word.capitalize() for word in key.split('_')): value
            for key, value in crbook_dict.items()
        }
        
        # Handle image data for base64 conversion
        if isinstance(uploaded_image, bytes):
            image_data = base64.b64encode(uploaded_image).decode('utf-8')
        else:
            image_data = base64.b64encode(uploaded_image.read()).decode('utf-8')
            uploaded_image.seek(0)  # Reset file pointer
            
        if "Cr Book Number" not in transformed_dict:
            return {
                "image_data": image_data,
                "extracted_info": {}
            }
        
        return {
            "image_data": image_data,
            "extracted_info": transformed_dict
        }
    
    raise ValueError("No image provided")
