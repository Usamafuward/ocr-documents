import base64
import logging
from fasthtml.common import *
from shad4fast import *
from starlette.responses import FileResponse
from starlette.datastructures import UploadFile
from app.gemini.crbook import process_gemini_cr_book
from app.gemini.drlicence import process_gemini_licence
from app.gemini.passport import process_gemini_passport

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the app    
app, rt = fast_app(
    pico=False,
    hdrs=(
        ShadHead(tw_cdn=True, theme_handle=False),
        Style("""
            :root {
                --background: 240 10% 3.9%;
                --foreground: 0 0% 98%;
                --card: 240 10% 3.9%;
                --card-foreground: 0 0% 98%;
                --popover: 240 10% 3.9%;
                --popover-foreground: 0 0% 98%;
                --primary: 0 0% 98%;
                --primary-foreground: 240 5.9% 10%;
                --secondary: 240 3.7% 15.9%;
                --secondary-foreground: 0 0% 98%;
                --muted: 240 3.7% 15.9%;
                --muted-foreground: 240 5% 64.9%;
                --accent: 240 3.7% 15.9%;
                --accent-foreground: 0 0% 98%;
                --destructive: 0 62.8% 30.6%;
                --destructive-foreground: 0 0% 98%;
                --border: 240 3.7% 15.9%;
                --input: 240 3.7% 15.9%;
                --ring: 240 4.9% 83.9%;
            }

            /* Force dark theme */
            [class="light"] {
                --background: 240 10% 3.9%;
                --foreground: 0 0% 98%;
                --card: 240 10% 3.9%;
                --card-foreground: 0 0% 98%;
                --popover: 240 10% 3.9%;
                --popover-foreground: 0 0% 98%;
                --primary: 0 0% 98%;
                --primary-foreground: 240 5.9% 10%;
                --secondary: 240 3.7% 15.9%;
                --secondary-foreground: 0 0% 98%;
                --muted: 240 3.7% 15.9%;
                --muted-foreground: 240 5% 64.9%;
                --accent: 240 3.7% 15.9%;
                --accent-foreground: 0 0% 98%;
                --destructive: 0 62.8% 30.6%;
                --destructive-foreground: 0 0% 98%;
                --border: 240 3.7% 15.9%;
                --input: 240 3.7% 15.9%;
                --ring: 240 4.9% 83.9%;
            }
            
            [class=""] {
                --background: 240 10% 3.9%;
                --foreground: 0 0% 98%;
                --card: 240 10% 3.9%;
                --card-foreground: 0 0% 98%;
                --popover: 240 10% 3.9%;
                --popover-foreground: 0 0% 98%;
                --primary: 0 0% 98%;
                --primary-foreground: 240 5.9% 10%;
                --secondary: 240 3.7% 15.9%;
                --secondary-foreground: 0 0% 98%;
                --muted: 240 3.7% 15.9%;
                --muted-foreground: 240 5% 64.9%;
                --accent: 240 3.7% 15.9%;
                --accent-foreground: 0 0% 98%;
                --destructive: 0 62.8% 30.6%;
                --destructive-foreground: 0 0% 98%;
                --border: 240 3.7% 15.9%;
                --input: 240 3.7% 15.9%;
                --ring: 240 4.9% 83.9%;
            }

            /* Force dark theme styles */
            body {
                background-color: hsl(var(--background));
                color: hsl(var(--foreground));
            }
            
            @keyframes float {
                0% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
                100% { transform: translateY(0px); }
            }
            
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.5); }
                70% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
                100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
            }
            
            @keyframes fadeOut {
                0% { opacity: 1; }
                70% { opacity: 1; }
                100% { opacity: 0; display: none; }
            }
            
            .float { animation: float 3s ease-in-out infinite; }
            .pulse { animation: pulse 2s infinite; }
            .spinner { animation: spin 1s linear infinite; }
            
            .glass {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            .hover-lift {
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .hover-lift:hover {
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
            
            .copy-tooltip { 
                display: none;
                position: absolute;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 10;
                top: -25px;
                right: 0;
            }
            
            .copy-btn:hover .copy-tooltip {
                display: block;
            }
            
            .copied {
                display: block !important;
                animation: fadeOut 1s forwards;
            }
            
            .htmx-request .processing-btn { display: none; }
            .htmx-request .loading-btn { display: flex; }
            .loading-btn { display: none; }
            .processing-btn { display: flex; }
        """),
        Script("""
            document.documentElement.setAttribute('class', 'dark');       
               
            function copyToClipboard(text, tooltipId) {
                navigator.clipboard.writeText(text).then(() => {
                    const tooltip = document.getElementById(tooltipId);
                    tooltip.textContent = 'Copied!';
                    tooltip.classList.add('copied');
                    setTimeout(() => {
                        tooltip.textContent = 'Copy';
                        tooltip.classList.remove('copied');
                    }, 1000);
                });
            }
        """)
    )
)

# In-memory storage
uploaded_images = {
    "crbook": None,
    "licence": None,
    "passport": None
}

# Add application lifecycle handlers
@app.on_event("startup")
async def startup_event():
    """Handle application startup"""
    logger.info("Starting Document Information Extractor application...")

@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown"""
    logger.info("Shutting down Document Information Extractor application...")
    # Clear any uploaded images
    uploaded_images.clear()

# Add global error handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return Alert(
        AlertTitle("Error"),
        AlertDescription(f"An error occurred: {str(exc)}"),
        variant="destructive",
        cls="mt-4 backdrop-blur-sm bg-white/10 glass"
    )

def get_upload_card(doc_type):
    """Generate the upload card UI with glass effect for different document types"""
    
    icons = {
        "crbook": "car",
        "licence": "id-card", 
        "passport": "book-text"
    }
    titles = {
        "crbook": "CR Book",
        "licence": "Driving Licence", 
        "passport": "Passport"
    }
    colors = {
        "crbook": "emerald",
        "licence": "blue",
        "passport": "purple"
    }
    
    return Card(
        Div(
            Form(
                Div(
                    Div(
                        P(f"Upload your {titles[doc_type]} image and click 'Process' to extract details. For better results, upload, clear, and crop the image before processing",
                        cls="text-sm text-muted-foreground text-center"),
                        cls="space-y-1.5 p-6 items-center justify-center"
                    ),
                    Div(
                        Input(
                            type="file",
                            name=f"{doc_type}_image",
                            accept="image/*",
                            cls="hidden",
                            id=f"file-upload-{doc_type}",
                            hx_post=f"/upload-image/{doc_type}",
                            hx_encoding="multipart/form-data",
                            hx_target=f"#{doc_type}-display",
                            hx_trigger="change"
                        ),
                        Label(
                            Lucide(icons[doc_type], cls=f"w-10 h-10 mb-2 text-{colors[doc_type]}-500 float"),
                            f"Click to upload {titles[doc_type]} image",
                            htmlFor=f"file-upload-{doc_type}",
                            cls=f"flex flex-col items-center justify-center w-full h-40 border-2 border-dashed border-{colors[doc_type]}-500 rounded-lg cursor-pointer hover:bg-{colors[doc_type]}-500/5 backdrop-blur-sm bg-white/10 transition-all duration-200 glass hover-lift"
                        ),
                    ),
                    id=f"upload-container-{doc_type}",
                ),
                Div(
                    Button(
                        Div(
                            "Process",
                            cls="processing-btn"
                        ),
                        Div(
                            Lucide("loader", cls="w-4 h-4 mr-2 spinner"),
                            "Processing... please wait",
                            cls="loading-btn items-center justify-center"
                        ),
                        variant="outline",
                        cls=f"""
                            pulse w-full
                            bg-{colors[doc_type]}-500/10
                            hover:bg-{colors[doc_type]}-500/20
                            border-white/40
                            hover:border-{colors[doc_type]}-500
                        """,
                        hx_post=f"/process-ocr/{doc_type}",
                        hx_target=f"#{doc_type}-display",
                        hx_indicator=f"#process-btn-{doc_type}",
                        id=f"process-btn-{doc_type}"
                    ),
                    Button(
                        "Clear",
                        variant="outline",
                        cls=f"""
                            w-full
                            bg-red-500/10
                            hover:bg-red-500/20
                            border-red-500/30
                            hover:border-red-500
                        """,
                        hx_post=f"/clear/{doc_type}",
                        hx_target=f"#{doc_type}-display"
                    ),
                    cls="gap-6 mt-6 grid w-full grid-cols-2 items-center justify-center"
                ),
            ),
            cls="p-6 pt-0"
        ),
        cls="max-w-7xl mx-auto rounded-lg border-2 bg-card/20 backdrop-blur-sm text-card-foreground shadow-lg",
        standard=True
    )
    
def get_document_display(doc_type, image_data=None, extracted_info=None, padding=True, ocr_method="Gemini"):
    """Generate the document display area with glass effect and modern styling"""
    
    icons = {
        "crbook": "car",
        "licence": "id-card",
        "passport": "book-text"
    }
    titles = {
        "crbook": "CR Book",
        "licence": "Driving Licence",
        "passport": "Passport"
    }
    colors = {
        "crbook": "green",
        "licence": "blue",
        "passport": "purple"
    }
    placeholder = {
        "crbook": "https://placehold.co/600x400?text=Upload+CR+Book+Image",
        "licence": "https://placehold.co/600x400?text=Upload+Licence+Image",
        "passport": "https://placehold.co/600x400?text=Upload+Passport+Image"
    }
    
    return Div(
        Div(
            H3(f"{titles[doc_type]} Image", cls="text-2xl font-semibold leading-none tracking-tight"),
            P("Uploaded image for processing.", cls="text-gray-500 text-sm mb-6"),
            Div(
                Img(
                    src=f"data:image/jpeg;base64,{image_data}" if image_data else placeholder[doc_type],
                    alt=titles[doc_type],
                    cls="rounded-lg object-contain w-full h-auto"
                ),
                cls=f"""
                    block w-full
                    border-2 border-dashed rounded-xl cursor-pointer
                    border-{colors[doc_type]}-500
                    hover:bg-{colors[doc_type]}-500/5
                    glass hover-lift
                    p-5
                """ 
            ),
            Alert(
                AlertTitle(f"✅ {titles[doc_type]} Detected" if extracted_info and "Error" not in extracted_info else f"❌ No {titles[doc_type]} Detected") if extracted_info else None,
                cls="mt-4 backdrop-blur-sm bg-white/10 glass"
            ) if image_data and extracted_info else None,
            cls="w-full md:w-1/2 border-2 rounded-lg p-6"
        ),
        Div(
            H3(f"{titles[doc_type]} Information", cls="text-2xl font-semibold leading-none tracking-tight"),
            P(f"Extracted information from the uploaded image using {ocr_method.capitalize()} OCR.",
              cls="text-gray-500 text-sm mb-6"),
            Div(
                *[
                    Div(
                        Div(
                            P(key + ":", cls=f"font-semibold text-{colors[doc_type]}-500" if not key == "Error" else "text-red-500"),
                            *[
                                P(item or "Not found", cls="ml-2 text-white" + (" mb-2" if isinstance(value, list) else ""))
                                for item in (value if isinstance(value, list) else [value])
                            ],
                            cls="flex-grow"
                        ),
                        Button(
                            Div(
                                Lucide("copy", cls="w-4 h-4"),
                                Div("Copy", cls="copy-tooltip", id=f"tooltip-{key.lower().replace(' ', '-')}"),
                                cls="relative copy-btn"
                            ),
                            onclick=f"copyToClipboard('{value or ''}', 'tooltip-{key.lower().replace(' ', '-')}')",
                            variant="ghost",
                            cls=f"p-2 hover:bg-{colors[doc_type]}-500/20"
                        ),
                        cls=f"""
                            flex items-center justify-between mb-4 p-4 
                            border border-{colors[doc_type]}-500/30 rounded-lg 
                            bg-gradient-to-br from-{colors[doc_type]}-500/10 to-{colors[doc_type]}-500/5 
                            hover:from-{colors[doc_type]}-500/20 hover:to-{colors[doc_type]}-500/10 
                            transition-all duration-300 
                            hover:border-{colors[doc_type]}-500/50 
                            hover-lift
                        """ if not key == "Error" else f"""
                            flex items-center justify-between mb-4 p-4 
                            border border-red-500/30 rounded-lg 
                            bg-gradient-to-br from-red-500/10 to-red-500/5 
                            hover:from-red-500/20 hover:to-red-500/10 
                            transition-all duration-300 
                            hover:border-red-500/50 
                            hover-lift
                        """
                    )
                    for key, value in (extracted_info or {}).items()
                ] if extracted_info else [
                    P(f"Upload and process an image to see extracted information for {titles[doc_type]}.",
                      cls="text-gray-500")
                ],
                cls="space-y-4"
            ),
            cls="w-full md:w-1/2 border-2 rounded-lg p-6"
        ),
        id=f"{doc_type}-display",
        cls="flex flex-col md:flex-row gap-6 mx-auto max-w-7xl w-full justify-center"
    )

def get_tabs():
    """Generate the Tabs component for different document types"""
    return Tabs(
        TabsList(
            TabsTrigger(
                Div(Lucide("id-card", cls="w-4 h-4 mr-2"), "Licence", cls="flex items-center"),
                value="licence",
            ),
            TabsTrigger(
                Div(Lucide("car", cls="w-4 h-4 mr-2"), "CR Book", cls="flex items-center"),
                value="crbook",
            ),
            TabsTrigger(
                Div(Lucide("book-text", cls="w-4 h-4 mr-2"), "Passport", cls="flex items-center"),
                value="passport",
            ),
            cls="grid w-full grid-cols-3 bg-gray-100/50 rounded-lg gap-1"
        ),
        TabsContent(
            get_upload_card("licence"),
            get_document_display(doc_type="licence"),
            value="licence",
            cls="space-y-7 transition-all duration-500 ease-in-out"
        ),
        TabsContent(
            get_upload_card("crbook"),
            get_document_display(doc_type="crbook"),
            value="crbook",
            cls="space-y-7 transition-all duration-500 ease-in-out"
        ),
        TabsContent(
            get_upload_card("passport"),
            get_document_display(doc_type="passport"),
            value="passport",
            cls="space-y-7 transition-all duration-500 ease-in-out"
        ),
        default_value="licence",
        cls="w-full max-w-7xl mx-auto space-y-7 my-8"
    )

@rt('/')
def get():
    """Render the main page"""
    return Title("Document Information Extractor"), Body(
        Section(
            H1(
                "Document Information Extractor",
                cls="text-4xl font-bold tracking-tight text-center mb-6"
            ),
            cls="container max-w-full mx-auto my-8"
        ),
        Section(
            get_tabs(),
            cls="container max-w-7xl mx-auto px-4 space-y-8 mb-8"
        ),
        cls="min-h-screen bg-background"
    )

@rt('/upload-image/{doc_type}')
async def upload_image(req: Request, doc_type: str):
    """Handle image upload for different document types"""
    if req.method != "POST":
        logger.warning(f"Invalid method {req.method} for upload")
        return Alert(
            AlertTitle("Error"),
            AlertDescription("Method not allowed"),
            variant="destructive"
        ), 405
    
    try:
        form = await req.form()
        image_field_name = f"{doc_type}_image"
        
        if image_field_name not in form:
            return "No file field found in form", 400
            
        image = form[image_field_name]
        
        if not isinstance(image, UploadFile):
            return "Invalid file upload", 400
            
        if not image.filename:
            return "No file selected", 400
            
        # Read the file content
        content = await image.read()
        if not content:
            return "Empty file", 400
            
        # Store the image content
        uploaded_images[doc_type] = content
        logger.info(f"Successfully uploaded {doc_type} image: {image.filename}")
        
        return Div(
            Script(f"document.getElementById('upload-container-{doc_type}').style.display = 'none';"),
            get_document_display(doc_type=doc_type, image_data=base64.b64encode(content).decode())
        )
            
    except Exception as e:
        logger.error(f"Upload error for {doc_type}: {str(e)}", exc_info=True)
        return Alert(
            AlertTitle("Upload Failed"),
            AlertDescription(str(e)),
            variant="destructive",
            cls="mt-4"
        ), 500

@rt('/process-ocr/{doc_type}')
async def process_ocr(req: Request, doc_type: str):
    """Process OCR for different document types with validation"""
    try:
        if not uploaded_images[doc_type]:
            raise ValueError(f"No {doc_type} image uploaded")
        
        result = process_gemini_cr_book(uploaded_images[doc_type]) if doc_type == "crbook" else (
            process_gemini_licence(uploaded_images[doc_type]) if doc_type == "licence" else process_gemini_passport(uploaded_images[doc_type])
        )
             
        image_data = result['image_data']
        extracted_info = result['extracted_info']
        
        print(extracted_info)
        
        # Validate the extracted information based on document type
        if doc_type == "licence" and ("Licence Number" not in extracted_info or extracted_info["Licence Number"] == None or extracted_info["Nic Number"] == None):
            extracted_info = { "Error": "Upload valid Driving Licence image" }
        elif doc_type == "passport" and ("Passport Number" not in extracted_info or extracted_info["Passport Number"] == None or extracted_info["Nic Number"] == None):
            extracted_info = { "Error": "Upload valid Passport image" }
        elif doc_type == "crbook" and ("Registration Number" not in extracted_info or extracted_info["Registration Number"] == None):
            extracted_info = { "Error": "Upload valid CR book image" }
        
        return Div(
            get_document_display(doc_type, image_data=image_data, extracted_info=extracted_info, padding=False),
        )
    
    except Exception as e:
        logger.error(f"Process error for {doc_type}: {str(e)}", exc_info=True)
        return Alert(
            AlertTitle("Processing Failed"),
            AlertDescription(str(e)),
            variant="destructive",
            cls="mt-4"
        ), 500

@rt('/clear/{doc_type}')
async def clear(req: Request, doc_type: str):
    """Clear uploaded image with error handling"""
    try:
        uploaded_images[doc_type] = None
        logger.info(f"Cleared {doc_type} image")
        
        return Div(
            get_document_display(doc_type, padding=False),
            Script(f"""
                document.getElementById('upload-container-{doc_type}').style.display = 'block';
                document.getElementById('file-upload-{doc_type}').value = '';
            """),
            cls="mx-auto justify-center"
        )
    except Exception as e:
        logger.error(f"Clear error for {doc_type}: {str(e)}", exc_info=True)
        return Alert(
            AlertTitle("Clear Failed"),
            AlertDescription(str(e)),
            variant="destructive",
            cls="mt-4"
        ), 500

def run_server():
    """Run the server with proper configuration"""
    import uvicorn
    
    config = uvicorn.Config(
        "main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        workers=1,
        reload=True,
        timeout_keep_alive=65,
        loop="auto"
    )
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    run_server()
else:
    serve()