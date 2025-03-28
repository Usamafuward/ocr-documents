import openai
from dotenv import load_dotenv
import os
import json
import base64
from app.models.drlicence import LicenceInfo

load_dotenv()

def setup_openai(api_key: str):
    """Initialize OpenAI client with API key"""
    return openai.OpenAI(api_key=api_key)

def extract_licence_info(uploaded_image) -> LicenceInfo:
    """
    Extract licence information using OpenAI model and validate with Pydantic
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
    First, determine if the provided image is a Driving licence. If the image is not a Driving licence, return null for all fields in the JSON structure.

    If the image is a Driving licence, analyze it carefully and provide the information in valid JSON format with the following fields:
    {
        "name": "1,2. full name",
        "licence_number": "5. number",
        "nic_number": "4d. number or Example : 123456789 V - old format, 123456789012 - new format",
        "address": "8. complete address",
        "date_of_birth": "3.YYYY-MM-DD",
        "date_of_issue": "4a. YYYY-MM-DD",
        "date_of_expiry": "4b. YYYY-MM-DD",
        "blood_group": "group if available, null if not Example : A+, B-"
    }
    
    Ensure all dates are in YYYY-MM-DD format and the response is valid JSON.
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
        
        # Parse JSON and create LicenceInfo object
        licence_data = json.loads(json_str)
        return LicenceInfo(**licence_data)
    except Exception as e:
        raise ValueError(f"Failed to parse OpenAI response: {str(e)}\nResponse text: {response_text}")

def process_openai_licence(uploaded_image) -> dict:
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
        
        return {
            "image_data": image_data,
            "extracted_info": transformed_dict
        }
    
    raise ValueError("No image provided")