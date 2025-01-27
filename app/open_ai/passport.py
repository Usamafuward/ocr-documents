import openai
from dotenv import load_dotenv
import os
import json
import base64
from models.passport import PassportInfo

load_dotenv()

def setup_openai(api_key: str):
    """Initialize OpenAI client with API key"""
    return openai.OpenAI(api_key=api_key)

def extract_passport_info(uploaded_image) -> PassportInfo:
    """
    Extract passport information using OpenAI model and validate with Pydantic
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
    First, determine if the provided image is a Passport. If the image is not a Passport, return null for all fields in the JSON structure.

    If the image is a Passport, analyze it carefully and provide the information in valid JSON format with the following fields:
    {
        "surname": "family name/surname",
        "name": "other names (excluding surname)",
        "passport_number": "passport number",
        "nic_number": "national ID number if available, null if not found",
        "nationality": "country of nationality",
        "sex": "Give Male or Female if M or F is visible",
        "document_type": "type of passport (e.g. PA-Regular, PB-Diplomatic)",
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
        max_tokens=1000,
        temperature=0.1,
    )
    
    # Extract JSON from response
    try:
        response_text = response.choices[0].message.content
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        json_str = response_text[json_start:json_end]
        
        # Parse JSON and create PassportInfo object
        passport_data = json.loads(json_str)
        return PassportInfo(**passport_data)
    except Exception as e:
        raise ValueError(f"Failed to parse OpenAI response: {str(e)}\nResponse text: {response_text}")

def process_openai_passport(uploaded_image) -> dict:
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
            
        if "Passport Number" not in transformed_dict:
            return {
                "image_data": image_data,
                "extracted_info": {}
            }
        
        return {
            "image_data": image_data,
            "extracted_info": transformed_dict
        }
    
    raise ValueError("No image provided")