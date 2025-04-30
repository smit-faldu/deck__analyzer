import os
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
from io import BytesIO
from pptx import Presentation
from PIL import Image, ImageDraw

# Set the Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

async def convert_pdf_to_images(file_content, scale=300/72):
    doc = fitz.open(stream=file_content, filetype="pdf")
    images = []

    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    return images

def extract_text_from_images(images):
    text_pages = []
    for idx, img in enumerate(images):
        text = pytesseract.image_to_string(img)
        text_pages.append(text.strip())
    return "\n\n".join(text_pages)

def slide_to_image(slide, width=1280, height=720):
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    for shape in slide.shapes:
        if hasattr(shape, "text") and shape.text.strip():
            draw.text((50, 50 + 30 * slide.shapes.index(shape)), shape.text.strip(), fill='black')

    return img

async def extract_text_from_pptx(file_content):
    prs = Presentation(BytesIO(file_content))
    all_text = []

    for idx, slide in enumerate(prs.slides):
        image = slide_to_image(slide)
        text = pytesseract.image_to_string(image)
        all_text.append(text.strip())

    return "\n\n".join(all_text)