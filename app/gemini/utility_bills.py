import google.generativeai as genai
import base64
import json
from io import BytesIO
import PIL.Image
from dotenv import load_dotenv
import os
import fitz  # PyMuPDF

load_dotenv()

def setup_gemini(api_key: str):
    """Initialize Gemini with API key"""
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash')

def process_utility_bill(uploaded_file, bill_type):
    """Process utility bills (electricity/water) handling both images and PDFs"""
    model = setup_gemini(os.getenv("GEMINI_API_KEY"))
    
    try:
        # Read file content and detect PDF
        if isinstance(uploaded_file, bytes):
            file_content = uploaded_file
        else:
            file_content = uploaded_file.read()
            uploaded_file.seek(0)
        
        is_pdf = file_content.startswith(b'%PDF-')
        
        result = {
            "image_data": None,
            "extracted_info": None
        }

        if is_pdf:
            # PDF processing with PyMuPDF
            with fitz.open(stream=file_content, filetype="pdf") as doc:
                # Get first page as high-quality image
                first_page = doc.load_page(0)
                pix = first_page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
                preview_image = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Prepare base64 PDF data
            result["image_data"] = base64.b64encode(file_content).decode()
            
            # Gemini processing with image only
            prompt = f"""
            Analyze this {bill_type} bill document image and return JSON with:
            {{
                "name": "Account holder's name",
                "address": "Service address without asterik",
                "current_charge": "Current month charges (number only)",
                "previous_due": "Previous balance/arrears (number only)",
                "outstanding_due": "Outstanding Amount (number only) / Dues Previous month (with +/- sign)",
                "total_due": "Total amount due (number only)",
            }}

            Rules:
1. Extract information directly from the document image
2. Convert amounts to numbers without currency symbols and two decimal point
3. If field not found, set to null
4. Handle both Sinhala/English text
5. Address should only contain text and numbers(house numbers like 25/1 or 26,)
6. Names and addresses should be exact matches from the document
            """
            response = model.generate_content([prompt, preview_image])
        else:
            # Direct image processing
            image = PIL.Image.open(BytesIO(file_content))
            result["image_data"] = base64.b64encode(file_content).decode()
            
            prompt = f"""
            Analyze this {bill_type} bill and return JSON with:
            {{
                "name": "Account holder's name",
                "address": "Service address",
                "current_charge": "Current month charges",
                "previous_due": "Previous balance/arrears",
                "outstanding_due": "Outstanding Amount",
                "total_due": "Total amount due",
            }}
            Rules same as PDF version
            """
            response = model.generate_content([prompt, image])

        # Process response
        response_text = response.text
        json_str = response_text[response_text.find('{'):response_text.rfind('}')+1]
        bill_data = json.loads(json_str)

        result["extracted_info"] = {
            "Name": bill_data.get("name"),
            "Address": bill_data.get("address"),
            "Current Charge": bill_data.get("current_charge"),
            "Outstanding due": bill_data.get("outstanding_due"),
            # "Previous Due": bill_data.get("previous_due"),
            "Total Due": bill_data.get("total_due")
        }

        return result

    except Exception as e:
        error_msg = f"Processing error: {str(e)}"
        if 'response_text' in locals():
            error_msg += f"\nResponse: {response_text}"
        raise ValueError(error_msg)
