from openai import OpenAI

from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from pathlib import Path
from playsound import playsound
import base64
import requests

import os


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def extract_pages_with_complex_content(pdf_path, output_folder, page_start):
    page_end = int(page_start) + 1
    # Read the PDF file
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        num_pages = len(reader.pages)

        # Loop through each page
        for page_num in range(page_start, page_end):
            page = reader.pages[page_num]
            text = page.extract_text()
            print(text)
            # Convert the page to an image
            images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)

            # Save the image
            for img in images:
                img_path = os.path.join(output_folder, f'page_{page_num + 1}.png')
                img.save(img_path, 'PNG')

                print(f'Saved image of page {page_num + 1} at {img_path}')
    return text


def pdf_to_speech(pdf_path, page, output_image_folder='images'):
    os.makedirs(output_image_folder, exist_ok=True)
    pdftext = extract_pages_with_complex_content(pdf_path, output_image_folder, int(page))
    messageText = """Analyze the image as a page from a 'Probability and Random Variables' Textbook.
                      Imagine you are reading aloud from a textbook. Your task is to describe and explain the 
                      content in a way that is clear and understandable, especially focusing on equations, figures, and 
                      complex topics. Assume the reader is listening to this as an audio book and does not have
                      visual access to the content. This means you should explain figures and equations verbatim, in a way 
                      that an audio reader might describe them. As for text, attempt to remain as close to verbatim as possible,
                      keeping the train of thought from page-to-page. 
                      Symbols need to be replaced with text descriptions. For example xᵢ may need to be repesented as "x sub i" 
                      and η may need to be represented as "eta", and so on.
                      Speak in the POV that you are the text. Do not reference "The Text" 
                      Please try to structure your response similar to the text. Please do your best. 
                      This is very important for my career.""" \
                  + "Here is some extracted text from the textbook [N.B. it may be noisy and incorrect at points]: " + pdftext

    client = OpenAI()
    image_path = "images/" + str(page + 1) + ".png"
    base64_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": messageText,
                     },
                    {

                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        max_tokens=4000,
    )

    print(response.choices[0].message.content)
    speech_file_path = f"./audio/{page + 1}.mp3"
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=response.choices[0].message.content
    )
    print(response)
    print("Streaming Audio to file: ", speech_file_path)
    response.stream_to_file(speech_file_path)
    playsound(speech_file_path)
    return response


if __name__ == "__main__":
    pdf_path = "probabilitytextbook.pdf"
    page = 100
    pdf_to_speech(pdf_path, page)
    print('done')
