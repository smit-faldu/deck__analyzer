import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from ocr import convert_pdf_to_images, extract_text_from_images, extract_text_from_pptx
from agent import analyze_presentation_content

app = FastAPI(title="Pitch Deck Analyzer API")

@app.post("/analyze/", response_class=JSONResponse)
async def analyze_pitch_deck(file: UploadFile = File(...)):
    try:
        # Read file content
        file_content = await file.read()
        file_extension = os.path.splitext(file.filename)[1].lower()

        # Extract text based on file type
        if file_extension == '.pptx':
            extracted_text = await extract_text_from_pptx(file_content)
        elif file_extension == '.pdf':
            images = await convert_pdf_to_images(file_content)
            extracted_text = extract_text_from_images(images)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please provide a .pptx or .pdf file")

        # Analyze the extracted text
        analysis_result = await analyze_presentation_content(extracted_text)
        return JSONResponse(content=analysis_result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to Pitch Deck Analyzer API", 
            "usage": "POST /analyze/ with a PDF or PPTX file to analyze your pitch deck"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)