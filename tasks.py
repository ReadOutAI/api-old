from docx import Document
import fitz
import edge_tts
import os
from config import conversions, CONVERTED_PATH
import asyncio

def read_docx(file_path):
    doc = Document(file_path)
    return ' '.join([paragraph.text for paragraph in doc.paragraphs])

def read_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""

    for page in doc:
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda block: -block[1])  # sort y-coordinate (top to bottom)

        for block in blocks:
            text = block[4] + text

    return text

async def convert_to_audio(file_path, output_path, language, sid):
    
    conversions[sid] = { 'status' : 'processing' , 'message' : 'File is being processed'}
    
    try:
        if file_path.endswith('.docx'):
            text = read_docx(file_path)
        elif file_path.endswith('.pdf'):
            text = read_pdf(file_path)
        else:
            raise ValueError('Unsupported file format')

        communicate = edge_tts.Communicate(text, language)
        duration = 0

        await communicate.save(output_path)  # Run the coroutine

        # Move the processed file to the converted directory
        os.rename(output_path, os.path.join(CONVERTED_PATH, os.path.basename(output_path)))

        # Update conversion status
        conversions[sid] = {'status': 'success', 'duration': duration, 'path': f"{CONVERTED_PATH}/{sid}"}
    except Exception as e:
        # Update conversion status
        conversions[sid] = {'status': 'error', 'message': str(e)}

# Use asyncio.run to execute the asynchronous function
def convert_to_audio_sync(file_path, output_path, language, sid):
    asyncio.run(convert_to_audio(file_path, output_path, language, sid))

