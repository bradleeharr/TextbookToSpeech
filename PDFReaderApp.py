import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from playsound import playsound
from pdf2image import convert_from_path
import os
from openai import OpenAI
from vision import extract_pages_with_complex_content, encode_image
import threading

MAX_PAGES = 1100
START_PAGE = 390


def play_sound(audio_file_path):
    try:
        playsound(audio_file_path)
    except Exception as e:
        print(f"Error playing sound: {e}")


class PDFReaderApp:
    def __init__(self, master, pdf_path):
        self.master = master
        self.current_page = START_PAGE
        self.image_width = 800
        self.image_height = 1000
        self.pdf_path = pdf_path
        self.pages_cache = {}  # Cache for storing pre-converted pages
        self.num_cached_pages = 20
        self.pre_cache_radius = 10  # Number of pages to pre-cache around the current page
        self.update_cache(self.current_page)

        master.title("PDF Reader")
        master.geometry(str(self.image_width) + 'x' + str(self.image_height))  # Width x Height

        threading.Thread(target=self.update_cache, args=(self.current_page,), daemon=True).start()

        print("INIT")

        # Loading Indicator
        self.loading_label = ttk.Label(master, text="Loading...", font=("Arial", 20))
        self.loading_label.pack(fill=tk.BOTH, expand=True)

        # Page Number Display
        self.page_number_label = ttk.Label(master, text="", font=("Arial", 12))
        self.page_number_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Navigation
        self.nav_frame = ttk.Frame(master)
        self.nav_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.prev_button = ttk.Button(self.nav_frame, text="Previous", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.play_button = ttk.Button(self.nav_frame, text="Play Audio", command=self.play_audio)
        self.play_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.next_button = ttk.Button(self.nav_frame, text="Next", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=10, pady=10)

        # Image
        self.image_label = ttk.Label(master)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        # Display the first page
        self.display_page(self.current_page)

    def pre_cache_page(self, page_number):
        try:
            pages = convert_from_path(self.pdf_path, first_page=page_number + 1, last_page=page_number + 1)
            image = pages[0]
            image_resized = image.resize((self.image_width, self.image_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image_resized)
            self.pages_cache[page_number] = photo
        except Exception as e:
            print(f"Error pre-caching page {page_number}: {e}")

    def display_page(self, page_number):
        if page_number in self.pages_cache:
            self.image_label.config(image=self.pages_cache[page_number])
            self.image_label.image = self.pages_cache[page_number]  # Keep a reference
            self.loading_label.pack_forget()
        else:
            self.loading_label.pack(fill=tk.BOTH, expand=True)
            threading.Thread(target=self.convert_page, args=(page_number,), daemon=True).start()
        self.update_page_number_display(page_number)
        self.update_cache(page_number)

    def next_page(self):
        if self.current_page < MAX_PAGES:
            self.current_page += 1
            self.display_page(self.current_page)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page(self.current_page)

    def convert_page(self, page_number):
        try:
            pages = convert_from_path(self.pdf_path, first_page=page_number + 1, last_page=page_number + 1)
            image = pages[0]
            image_resized = image.resize((self.image_width, self.image_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image_resized)
            self.master.after(0, self.update_image, photo)
        except Exception as e:
            print(f"Error converting page {page_number}: {e}")

    def update_image(self, photo):
        self.image_label.config(image=photo)
        self.image_label.image = photo
        self.loading_label.pack_forget()

    def update_page_number_display(self, page_number):
        total_pages = len(self.pages_cache)
        self.page_number_label.config(text=f"Page {page_number + 1} of {MAX_PAGES}")

    def update_cache(self, current_page):
        print("attempting to update cache")
        total_pages = MAX_PAGES
        start_page = max(0, current_page - self.pre_cache_radius)
        end_page = min(current_page + self.pre_cache_radius, total_pages)

        # Add new pages to the cache
        for page_number in range(start_page, end_page):
            if page_number not in self.pages_cache:
                self.pre_cache_page(page_number)

        # Optionally, remove pages far from the current page from the cache
        keys_to_remove = [key for key in self.pages_cache if key < start_page or key > end_page]
        for key in keys_to_remove:
            del self.pages_cache[key]

    def play_audio(self):
        page_number = self.current_page
        audio_file_path = os.path.abspath(f'audio/{page_number}.mp3')
        print(audio_file_path)
        if not os.path.exists(audio_file_path):
            self.generate_audio_for_page(page_number, audio_file_path)
            audio_file_path = os.path.abspath(f'audio/{page_number}.mp3')

        threading.Thread(target=play_sound, args=(audio_file_path,), daemon=True).start()

    def generate_audio_for_page(self, page_number, audio_file_path):
        print(page_number)
        pdftext = extract_pages_with_complex_content(self.pdf_path, 'images', page_number)
        messageText = """Analyze the image as a page from a 'Probability and Random Variables' Textbook.
                      Imagine you are reading aloud from a textbook. Your task is to describe and explain the 
                      content in a way that is clear and understandable, especially focusing on equations, figures, and 
                      complex topics. Assume the reader is listening to this as an audio book and does not have
                      visual access to the content. This means you should explain figures and equations verbatim, in a way 
                      that an audio reader might describe them. As for text, attempt to remain as close to verbatim as possible,
                      keeping the train of thought from page-to-page. 
                      Symbols need to be replaced with text descriptions. For example xᵢ may need to be repesented as "x sub i" 
                      and η may need to be represented as "eta", and so on.
                      Speak in the POV that you are the text. Do not reference "The Text" or "The Page"
                      Please structure your response similar to the text. Throughout add useful information such as insights,
                    summaries, and educational elaborations or useful applications.
                    Indicate that you are switching to a new paragraph by saying "New Paragraph"
                      Please do your best. 
                      This is very important for my career."""
        client = OpenAI()
        image_path = "images/page_" + str(page_number + 1) + ".png"
        base64_image = encode_image(image_path)

        chat_response = client.chat.completions.create(
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
            max_tokens=4096,
        )
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=chat_response.choices[0].message.content
        )
        print("Streaming Audio to file: ", audio_file_path)
        response.stream_to_file(audio_file_path)


def main():
    print("Test")
    root = tk.Tk()
    app = PDFReaderApp(root, r"C:\Users\bubba\Documents\My Code\gr-GPT\textbooktospeech\probabilitytextbook.pdf")
    root.mainloop()


if __name__ == "__main__":
    main()
