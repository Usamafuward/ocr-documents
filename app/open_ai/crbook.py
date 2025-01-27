from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
import openai
from dotenv import load_dotenv
import os
import json
import base64
import re

load_dotenv()

class CRBookInfo(BaseModel):
    cr_book_number: Optional[str] = Field(..., description="CR book number")
    registration_number: Optional[str] = Field(..., description="Vehicle registration number")
    chassis_number: Optional[str] = Field(..., description="Chassis number of the vehicle")
    engine_number: Optional[str] = Field(..., description="Engine number of the vehicle")
    cylinder_capacity: Optional[str] = Field(..., description="Cylinder capacity of the vehicle")
    class_of_vehicle: Optional[str] = Field(..., description="Class of the vehicle (e.g., Motorcycle, Car)")
    taxation_class: Optional[str] = Field(..., description="Taxation class of the vehicle")
    status_when_registered: Optional[str] = Field(..., description="Status of the vehicle when registered (e.g., Brand New, Reconditioned)")
    fuel_type: Optional[str] = Field(..., description="Fuel type of the vehicle (e.g., Petrol, Diesel)")
    provincial_council: Optional[str] = Field(None, description="Provincial council of registration if available")
    date_of_registration: Optional[date] = Field(None, description="Date of registration in YYYY-MM-DD format")
    owner_name: Optional[str] = Field(None, description="Name of the current owner")
    absolute_owner: Optional[str] = Field(None, description="Name of the absolute owner")
    absolute_owner_reference_date: Optional[date] = Field(None, description="Reference date for absolute owner")
    previous_owners: Optional[int] = Field(None, description="Number of previous owners")
    previous_owner_details: Optional[List[str]] = Field(None, description="List of previous owner details")
    make: Optional[str] = Field(None, description="Make of the vehicle")
    model: Optional[str] = Field(None, description="Model of the vehicle")
    color: Optional[str] = Field(None, description="Color of the vehicle")
    year_of_manufacture: Optional[int] = Field(None, description="Year of manufacture")
    country_of_origin: Optional[str] = Field(None, description="Country of origin of the vehicle")
    wheelbase: Optional[str] = Field(None, description="Wheelbase of the vehicle")
    seating_capacity: Optional[str] = Field(None, description="Seating capacity of the vehicle")
    gross_weight: Optional[str] = Field(None, description="Gross weight of the vehicle")
    unladen_weight: Optional[str] = Field(None, description="Unladen weight of the vehicle")
    type_of_body: Optional[str] = Field(None, description="Type of body of the vehicle")
    overhang: Optional[str] = Field(None, description="Overhang details of the vehicle")
    tire_size_front: Optional[str] = Field(None, description="Front tire size")
    tire_size_rear: Optional[str] = Field(None, description="Rear tire size")
    vehicle_dimensions: Optional[str] = Field(None, description="Vehicle dimensions (length, width, height)")
    printed_date: Optional[date] = Field(None, description="Date printed in YYYY-MM-DD format")

def setup_openai(api_key: str):
    """Initialize OpenAI client with API key"""
    return openai.OpenAI(api_key=api_key)

def extract_crbook_info(uploaded_image) -> CRBookInfo:
    """
    Extract CR book information using OpenAI model and validate with Pydantic
    """
    client = setup_openai(os.getenv("OPENAI_API_KEY"))
    
    # Convert bytes to base64 for OpenAI API
    try:
        if isinstance(uploaded_image, bytes):
            image = uploaded_image
        else:
            image = uploaded_image.read()
            uploaded_image.seek(0)  # Reset file pointer for later use
        
        # Encode image to base64
        base64_image = base64.b64encode(image).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")
    
    # Prepare the prompt for OpenAI
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
        "owner_name": "Name of the current owner if available, null if not found. Example: "Name = Mercantile investments and finance 3, Address = No 236, Galle road, Colombo 03"",
        "absolute_owner": "Name of the absolute owner if available, null if not found. Example: "Name = Mercantile investments and finance 3, Address = No 236, Galle road, Colombo 03"",
        "absolute_owner_reference_date": "Reference date for absolute owner if available, null if not found",
        "previous_owners": "Number of previous owners if available, null if not found",
        "previous_owner_details": "List of string containing previous owner details. Example: '1. Name = Mercantile investments and finance 3, Address = No 236, Galle road, Colombo 03, Transfered Date = 23/11/2016'",
        "make": "Make of the vehicle if available, null if not found",
        "model": "Model of the vehicle if available, null if not found",
        "color": "Color of the vehicle if available, null if not found",
        "year_of_manufacture": "Year of manufacture if available, null if not found",
        "country_of_origin": "Country of origin of the vehicle if available, null if not found",
        "wheelbase": "Wheelbase of the vehicle if available, null if not found",
        "seating_capacity": "Seating capacity of the vehicle if available, null if not found",
        "gross_weight": "Gross weight of the vehicle if available, null if not found",
        "unladen_weight": "Unladen weight of the vehicle in KG if available (Ex. 100 KG), null if not found",
        "type_of_body": "Type of body of the vehicle if available (Ex. OPEN, CLOSED), null if not found",
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
    4. Ensure all fields are properly extracted from image.
    5. Return exact text as shown, do not correct or modify spellings.
    6. If a field is not visible, set it to null.

    Ensure the response is valid JSON format.
    """
    
    # Generate response using OpenAI GPT-4 Vision
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        max_tokens=1500,  # Increase max_tokens for longer responses
        temperature=0.1,
    )
    
    # Extract JSON from response
    try:
        response_text = response.choices[0].message.content
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        json_str = response_text[json_start:json_end]
        
        # Parse JSON and create CRBookInfo object
        crbook_data = json.loads(json_str)
        
        if isinstance(crbook_data.get('previous_owner_details'), str):
            details_string = crbook_data['previous_owner_details']
            crbook_data['previous_owner_details'] = re.findall(
                r'\[.*?\]',
                details_string
            )
        
        return CRBookInfo(**crbook_data)
    except Exception as e:
        raise ValueError(f"Failed to parse OpenAI response: {str(e)}\nResponse text: {response_text}")

def process_openai_cr_book(uploaded_image) -> dict:
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
        
        print(transformed_dict)
        
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