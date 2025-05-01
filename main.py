import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from ocr import extract_text_from_pdf, extract_text_from_pptx
from agent import analyze_presentation_content

app = FastAPI(title="Pitch Deck Analyzer API")

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://app.govertx.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

@app.post("/analyze/", response_class=JSONResponse)
async def analyze_pitch_deck(file: UploadFile = File(...)):
    try:
        # Check file size
        file_size = 0
        file_content = b""
        while chunk := await file.read(1024):
            file_size += len(chunk)
            file_content += chunk
            if file_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="File size exceeds maximum limit of 10MB"
                )

        # Get file extension
        file_extension = os.path.splitext(file.filename)[1].lower()

        # Validate file type
        if file_extension not in ['.pptx', '.pdf']:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please provide a .pptx or .pdf file"
            )

        # Extract text based on file type
        if file_extension == '.pptx':
            extracted_text = await extract_text_from_pptx(file_content)
        else:  # .pdf
            extracted_text = await extract_text_from_pdf(file_content)

        # Validate extracted text
        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the file. Please ensure the file contains readable text."
            )

        # Analyze the extracted text
        analysis_result = await analyze_presentation_content(extracted_text)
        return JSONResponse(content=analysis_result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the file: {str(e)}"
        )

@app.get("/")
async def root():
    return {
        "message": "Welcome to Pitch Deck Analyzer API",
        "usage": "POST /analyze/ with a PDF or PPTX file to analyze your pitch deck",
        "supported_formats": ["PDF", "PPTX"],
        "max_file_size": "10MB"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)