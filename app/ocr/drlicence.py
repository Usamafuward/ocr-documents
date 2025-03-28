from paddleocr import PaddleOCR
import logging
import re
import base64

# Initialize PaddleOCR
ocr = PaddleOCR(lang='en')
logging.getLogger('ppocr').setLevel(logging.ERROR)

def extract_licence_info(ocr_text):
    """
    Extract all relevant information from OCR text using regex patterns.
    """
    # Initialize results dictionary
    info = {
        "Name": None,
        "Licence Number": None,
        "Nic Number": None,
        "Address": None,
        "Date Of Birth": None,
        "Date Of Issue": None,
        "Date Of Expiry": None,
        "Blood Group": None
    }
    
    # Split text into lines
    lines = ocr_text.split("\n")
    
    # Extract Name
    name_pattern = r"^(1,2\.|1\.2\.|12\.|,2|\.2|1,2,|1\.2,)\s*.+$"
    for i, line in enumerate(lines):
        if re.search(name_pattern, line):
            name = re.sub(r'\d+', '', line)
            name = re.sub(r'[,.]', '', name).strip()
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if not re.search(r'^(8\.|B\.|SL)', next_line):
                    name += f" {next_line}"
            info["Name"] = name.strip()
            break
    
    # Extract Driving Licence Number
    licence_match = re.search(r'5\.\s*(B|8)?\d{5,}', ocr_text)
    if licence_match:
        info["Licence Number"] = licence_match.group().replace("5.", "").strip()
    
    # Extract NIC Number
    nic_pattern = r'4[Cd]\.\d{9,}[A-Za-z]*|\d{9,}[A-Za-z]*'
    nic_match = re.search(nic_pattern, ocr_text)
    if nic_match:
        nic = nic_match.group().strip()
        if nic.startswith('4d.') or nic.startswith('4C.'):
            nic = nic[3:]
        if len(nic) == 9:
            nic = nic + 'V'
        info["Nic Number"] = nic
    
    # Extract Address
    for i, line in enumerate(lines):
        if re.search(r'^(8|B)\.', line):
            address = line[2:].strip()
            temp_list = []
            for j in range(i+1, min(i+3, len(lines))):
                next_line = lines[j].strip()
                if 'SL' not in next_line and not re.match(r'^(3|5)\.\d{2}\.\d{2}\.\d{4}', next_line):
                    temp_list.append(next_line)
            info["Address"] = ' '.join([address] + temp_list).strip()
            break
    
    # Extract Dates
    for line in lines:
        if re.search(r'^(3|5)\.\d{2}\.\d{2}\.\d{4}', line):
            info["Date Of Birth"] = line.split('.', 1)[1].strip()
        elif re.search(r'^4(a|s)\.\d{2}\.\d{2}\.\d{4}', line):
            info["Date Of Issue"] = line.split('.', 1)[1].strip()
        elif re.search(r'^4(b|6)\.\d{2}\.\d{2}\.\d{4}', line):
            info["Date Of Expiry"] = line.split('.', 1)[1].strip()
    
    # Extract Blood Group
    for i, line in enumerate(lines):
        if re.search(r'^Blood', line, re.IGNORECASE):
            blood_group = line.strip()
            if i + 1 < len(lines) and '+' in lines[i + 1]:
                blood_group += f" {lines[i + 1].strip()}"
            info["Blood Group"] = blood_group.split()[-1]
            break
    
    return info

def process_ocr_licence(uploaded_image):
    """Process OCR and extract information"""
    
    if uploaded_image:
        # Perform OCR
        result = ocr.ocr(uploaded_image, rec=True)
        
        # Extract text from OCR results
        ocr_text = "\n".join([line[1][0] for page in result for line in page])
        
        # Extract structured information
        extracted_info = extract_licence_info(ocr_text)
        
        # Convert image for display
        image_data = base64.b64encode(uploaded_image).decode('utf-8')
        
        return {"image_data": image_data, "extracted_info": extracted_info}