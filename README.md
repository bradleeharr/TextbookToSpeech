# TextbookToSpeech
A simple python application using GPT4-V to convert pdf pages of textbooks into AI-read audiobooks

## Features
- Converts textbook PDFs into spoken words using GPT-4-V.
- Navigable interface to move between pages of the textbook.
- Caches pages for faster access and reduced processing.
- Descriptions of images for complex content like equations and figures.
- Simple GUI built with Tkinter for easy navigation and use.

# Examples 
GUI picture:
![image](https://github.com/bradleeharr/TextbookToSpeech/assets/56418392/38729c3c-bccb-4549-a9d4-f4d091b85b33)

Text to Speech Demo: [download the video here](https://github.com/bradleeharr/TextbookToSpeech/blob/main/2023-11-27%2022-21-11.mkv).

## Installation
To set up TextbookToSpeech, you need Python installed on your system. Then, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/bradleeharr/TextbookToSpeech.git
   ```
2. Navigate to the project directory:
   ```
   cd TextbookToSpeech
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the application:

1. Place your PDF textbook file in the project directory.
2. Rename the file to `textbook.pdf` or modify the code in `main()` to use your file's name.
3. Run the script:
   ```
   python TextbookToSpeech.py
   ```
4. Use the GUI to navigate through the textbook, view pages, and listen to the AI-generated audio.

## Configuration
- `MAX_PAGES`: Set the maximum number of pages in the PDF.
- `START_PAGE`: Configure the starting page of the textbook.

## Dependencies
- Tkinter
- PIL (Pillow)
- playsound
- pdf2image
- OpenAI's GPT-4-V API


## Contributing
Contributions are welcome. 

## License
MIT License
