import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from playsound import playsound
from pdf2image import convert_from_path
import os
from openai import OpenAI
from vision import extract_pages_with_complex_content, encode_image
import threading

MAX_PAGES = 292
START_PAGE = 100


def play_sound(audio_file_path):
    try:
        playsound(audio_file_path)
    except Exception as e:
        print(f"Error playing sound: {e}")


class PDFReaderApp:
    def __init__(self, master, pdf_path):
        self.master = master
        self.current_page = START_PAGE
        self.image_width = 1000  # Width of the canvas
        self.image_height = 400  # Height of the canvas
        self.pdf_path = pdf_path
        self.pages_cache = {}  # Cache for storing pre-converted pages
        self.num_cached_pages = 20
        self.pre_cache_radius = 10  # Number of pages to pre-cache around the current page
        self.canvas_image = None  # Placeholder for the canvas image

        master.title("PDF Reader")
        master.geometry(f'{self.image_width + 30}x{self.image_height + 100}')  # Window size

        threading.Thread(target=self.update_cache, args=(self.current_page,), daemon=True).start()

        # Frame for Canvas and Scrollbar
        self.canvas_frame = tk.Frame(master)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Create a Canvas with Scrollbar inside the frame
        self.canvas = tk.Canvas(self.canvas_frame, width=self.image_width, height=self.image_height)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.canvas.bind('<MouseWheel>', self.on_mousewheel)  # For Windows
        self.canvas.bind('<Button-4>', self.on_mousewheel)  # For Linux
        self.canvas.bind('<Button-5>', self.on_mousewheel)  # For Linux

        # Loading Indicator
        self.loading_label = ttk.Label(master, text="Loading...", font=("Arial", 20))
        self.loading_label.pack(fill=tk.BOTH, expand=True)

        # Page Number Display
        self.page_number_label = ttk.Label(master, text="", font=("Arial", 12))
        self.page_number_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Navigation Frame
        self.nav_frame = ttk.Frame(master)
        self.nav_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.prev_button = ttk.Button(self.nav_frame, text="Previous", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.play_button = ttk.Button(self.nav_frame, text="Play Audio", command=self.play_audio)
        self.play_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.next_button = ttk.Button(self.nav_frame, text="Next", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=10, pady=10)

        # Display the first page
        self.display_page(self.current_page)

    def on_canvas_configure(self, event):
        # Set the scroll region to encompass the image
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_image(self, photo):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo  # Keep a reference
        self.loading_label.pack_forget()
        self.canvas.configure(scrollregion=self.canvas.bbox(tk.ALL))

    def pre_cache_page(self, page_number):
        try:
            pages = convert_from_path(self.pdf_path, first_page=page_number + 1, last_page=page_number + 1)
            image = pages[0]
            photo = ImageTk.PhotoImage(image)
            self.pages_cache[page_number] = photo
        except Exception as e:
            print(f"Error pre-caching page {page_number}: {e}")

    def display_page(self, page_number):
        if page_number in self.pages_cache:
            self.update_image(self.pages_cache[page_number])
            self.loading_label.pack_forget()
        else:
            self.loading_label.pack(fill=tk.BOTH, expand=True)
            threading.Thread(target=self.convert_page, args=(page_number,), daemon=True).start()
        self.update_page_number_display(page_number)

    def next_page(self):
        if self.current_page < MAX_PAGES:
            self.current_page += 1
            self.display_page(self.current_page)
            threading.Thread(target=self.update_cache, args=(self.current_page,), daemon=True).start()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_page(self.current_page)
            threading.Thread(target=self.update_cache, args=(self.current_page,), daemon=True).start()

    def convert_page(self, page_number):
        try:
            pages = convert_from_path(self.pdf_path, first_page=page_number + 1, last_page=page_number + 1)
            image = pages[0]
            photo = ImageTk.PhotoImage(image)
            self.pages_cache[page_number] = photo
            self.master.after(0, self.update_image, photo)
        except Exception as e:
            print(f"Error converting page {page_number}: {e}")

    def update_page_number_display(self, page_number):
        self.page_number_label.config(text=f"Page {page_number + 1} of {MAX_PAGES}")

    def on_mousewheel(self, event):
        """Handles mouse wheel scrolling."""
        if event.num == 4 or event.delta > 0:  # Scroll up
            self.canvas.yview_scroll(-1, 'units')
        elif event.num == 5 or event.delta < 0:  # Scroll down
            self.canvas.yview_scroll(1, 'units')

    def update_cache(self, current_page):
        total_pages = MAX_PAGES
        start_page = max(0, current_page - self.pre_cache_radius)
        end_page = min(current_page + self.pre_cache_radius, total_pages)
        print(
            "attempting to update cache. Current page:" + str(current_page) + " Start page: " + \
            str(start_page) + " End page: " + str(end_page))

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
        messageText = """Analyze the image as a page from a Textbook.
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
    app = PDFReaderApp(root, r"textbook.pdf")
    root.mainloop()


if __name__ == "__main__":
    main()
