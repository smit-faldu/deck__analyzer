import os
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from io import BytesIO
from pptx import Presentation
from PIL import Image, ImageDraw
import re
import tempfile
from datetime import datetime

# Set the Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def save_debug_image(img, prefix="debug"):
    """Save image to temporary directory for debugging"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = tempfile.gettempdir()
    filename = f"{prefix}_{timestamp}.png"
    filepath = os.path.join(temp_dir, filename)
    img.save(filepath)
    print(f"Debug image saved to: {filepath}")
    return filepath

async def convert_pdf_to_images(file_content, scale=300/72):
    """
    Converts PDF pages to images, but only for pages that require OCR.
    Returns a tuple of (images, text_pages) where text_pages contains directly extracted text.
    """
    doc = fitz.open(stream=file_content, filetype="pdf")
    images = []
    text_pages = []

    for i in range(len(doc)):
        page = doc.load_page(i)
        
        # Try to extract text directly first
        text = page.get_text()
        if text.strip():  # If we got text directly
            print(f"\nDirect text extracted from page {i+1}:")
            print("="*50)
            print(text.strip())
            print("="*50)
            text_pages.append(text.strip())
            continue
            
        # If no text was extracted, convert to image for OCR
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append((i, img))  # Store page number with image
        
        # Save and print debug image for the last page
        if i == len(doc) - 1:
            debug_path = save_debug_image(img, f"last_page_{i+1}")
            print(f"\nLast page ({i+1}) converted to image and saved for OCR")

    return images, text_pages

def extract_text_from_images(images):
    """
    Extracts text from images using OCR, preserving page order.
    """
    text_pages = []
    for page_num, img in images:
        # Pre-process image for better OCR results
        img = preprocess_image(img)
        
        # Save preprocessed image for debugging
        if page_num == len(images) - 1:  # For the last image
            debug_path = save_debug_image(img, f"preprocessed_page_{page_num+1}")
            print(f"\nPreprocessed last page ({page_num+1}) for OCR")
        
        # Extract text with improved OCR settings
        text = pytesseract.image_to_string(
            img,
            config='--psm 1 --oem 3'  # Automatic page segmentation with LSTM OCR Engine
        )
        print(f"\nOCR text extracted from page {page_num+1}:")
        print("="*50)
        print(text.strip())
        print("="*50)
        text_pages.append((page_num, text.strip()))
    
    return text_pages

def preprocess_image(img):
    """
    Pre-processes image to improve OCR accuracy.
    """
    # Convert to grayscale
    img = img.convert('L')
    
    # Enhance contrast
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    
    return img

async def extract_text_from_pdf(file_content):
    """
    Extracts text from PDF using a combination of direct text extraction and OCR.
    Returns text with preserved page order and structure.
    """
    print("\nStarting PDF text extraction process...")
    
    # Get both direct text and images for OCR
    images, direct_text_pages = await convert_pdf_to_images(file_content)
    
    # Process images with OCR if needed
    ocr_text_pages = extract_text_from_images(images) if images else []
    
    # Combine all text pages in correct order
    all_pages = direct_text_pages + ocr_text_pages
    all_pages.sort(key=lambda x: x[0] if isinstance(x, tuple) else 0)
    
    # Format the final text
    formatted_pages = []
    for page in all_pages:
        if isinstance(page, tuple):
            page_num, text = page
            formatted_pages.append(f"--- Page {page_num + 1} ---\n{text}")
        else:
            formatted_pages.append(page)
    
    final_text = "\n\n".join(formatted_pages)
    print("\nFinal extracted text:")
    print("="*50)
    print(final_text)
    print("="*50)
    
    return final_text

def slide_to_image(slide, width=1280, height=720):
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    for shape in slide.shapes:
        if hasattr(shape, "text") and shape.text.strip():
            draw.text((50, 50 + 30 * slide.shapes.index(shape)), shape.text.strip(), fill='black')

    return img

async def extract_text_from_pptx(file_content):
    """
    Extracts text directly from PPTX shapes, preserving structure and formatting.
    This method is significantly faster and more accurate than the previous OCR-based approach.
    """
    print("\nStarting PPTX text extraction process...")
    prs = Presentation(BytesIO(file_content))
    all_text_pages = []

    for slide_number, slide in enumerate(prs.slides):
        slide_text = []
        
        # Process each shape in the slide
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
                
            # Process each paragraph in the text frame
            for paragraph in shape.text_frame.paragraphs:
                paragraph_text = []
                # Process each run in the paragraph
                for run in paragraph.runs:
                    if run.text.strip():  # Only add non-empty text
                        paragraph_text.append(run.text.strip())
                
                if paragraph_text:  # Only add non-empty paragraphs
                    slide_text.append(' '.join(paragraph_text))
        
        # Add slide number and join text with proper spacing
        if slide_text:  # Only add slides that have text
            slide_content = f"--- Slide {slide_number + 1} ---\n" + "\n".join(slide_text)
            print(f"\nExtracted from Slide {slide_number + 1}:")
            print("="*50)
            print(slide_content)
            print("="*50)
            all_text_pages.append(slide_content)

    # Join all slides with double newlines for better readability
    final_text = "\n\n".join(all_text_pages)
    print("\nFinal extracted text:")
    print("="*50)
    print(final_text)
    print("="*50)
    
    return final_text