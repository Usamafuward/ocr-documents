import base64
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from typing import Union, BinaryIO

load_dotenv()

def setup_gemini_pdf(api_key: str):
    """Initialize Gemini client for PDF processing"""
    return genai.Client(api_key=api_key)

def pdf_file_to_base64(uploaded_pdf: Union[bytes, BinaryIO]) -> str:
    """Convert uploaded PDF file or bytes to base64 string"""
    if isinstance(uploaded_pdf, bytes):
        return base64.b64encode(uploaded_pdf).decode("utf-8")
    else:
        content = uploaded_pdf.read()
        uploaded_pdf.seek(0)  # Reset pointer for reuse
        return base64.b64encode(content).decode("utf-8")

def extract_vehicle_info_from_pdf(uploaded_pdf: Union[bytes, BinaryIO]) -> dict:
    """
    Extract vehicle information from uploaded PDF using Gemini and return structured dictionary
    """
    client = setup_gemini_pdf(os.getenv("GEMINI_API_KEY"))
    model = "gemini-2.0-flash"
    encoded_pdf = pdf_file_to_base64(uploaded_pdf)

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type="application/pdf",
                    data=base64.b64decode(encoded_pdf),
                ),
                types.Part.from_text(text=""),
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=0,
        response_mime_type="application/json",
        response_schema=types.Schema(
            required=["Engine No", "Chassis No"],
            type=types.Type.OBJECT,
            properties={
                "Engine No": types.Schema(type=types.Type.STRING),
                "Chassis No": types.Schema(type=types.Type.STRING),
                "Registration No": types.Schema(type=types.Type.STRING),
                "Invoice No": types.Schema(type=types.Type.STRING),
                "Year": types.Schema(type=types.Type.STRING),
            },
        ),
        system_instruction=[
            types.Part.from_text(text="""
    You are a text extraction expert. Your task is to extract the following fields from the given text:

    1. **Registration Number**: Consists of uppercase letters followed by a dash and exactly 4 digits at the end. Only the last 4 characters should be digits (e.g., AB CDE-1234 or AB CD-1234).
    2. **Chassis Number**
    3. **Engine Number**
    4. **Year**
    5. **Invoice No**: This may appear under alternate names like 'Reg No'.

    Return the extracted values in a clear and structured JSON format. Only include a field if it is confidently found in the text. Do not include keys for values that are not present.

    Example output:
    {
      "Registration Number": "...",
      "Chassis Number": "...",
      "Engine Number": "...",
      "Year": "...",
      "Invoice No": "..."
    }
    """
),
        ],
    )

    try:
        full_response = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            full_response += chunk.text

        # Extract JSON from response
        json_start = full_response.find('{')
        json_end = full_response.rfind('}') + 1
        json_str = full_response[json_start:json_end]
        return json.loads(json_str)

    except Exception as e:
        raise ValueError(f"Failed to parse Gemini response: {str(e)}")

def process_gemini_vehicle_pdf(uploaded_pdf: Union[bytes, BinaryIO]) -> dict:
    """
    Main function to process uploaded PDF and return structured data
    """
    if uploaded_pdf:
        # Extract structured information
        vehicle_info = extract_vehicle_info_from_pdf(uploaded_pdf)

        # Transform keys to presentation format (e.g., "engine_no" → "Engine No")
        transformed_dict = {
            ' '.join(word.capitalize() for word in key.replace('_', ' ').split()): value
            for key, value in vehicle_info.items()
        }

        # Convert uploaded PDF to base64 for frontend use
        encoded_pdf = pdf_file_to_base64(uploaded_pdf)

        return {
            "pdf_data": encoded_pdf,
            "extracted_info": transformed_dict
        }

    raise ValueError("No PDF file provided")
