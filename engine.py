import ocrmypdf
import os
import sys


def ocr_pdf(input_path: str, output_path: str, language_code: str):
    """
    Takes an input PDF, performs OCR, and saves a new searchable PDF.

    Args:
        input_path (str): The full path to the source PDF file.
        output_path (str): The full path where the output PDF will be saved.
        language_code (str): The 3-letter language code for OCR (e.g., 'eng', 'fra', 'tur').
    """
    print(f"Starting OCR process for '{input_path}'...")
    print(f"Language specified: '{language_code}'")

    # Check if the input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at '{input_path}'", file=sys.stderr)
        return

    try:
        # The core OCRmyPDF function call
        result = ocrmypdf.ocr(
            input_path,
            output_path,
            language=language_code,
            deskew=True,       # Automatically straightens skewed pages
            force_ocr=True,    # Forces OCR even if text is detected
            progress_bar=True, # Shows a progress bar in the console
        )

        if result == ocrmypdf.ExitCode.ok:
            print(f"✅ Success! Searchable PDF saved to: '{output_path}'")
        elif result == ocrmypdf.ExitCode.already_ocrd:
            print(f"ℹ️ Skipped: The PDF already had a text layer. Output file is a copy.")
        else:
            # For other potential exit codes, refer to OCRmyPDF documentation
            print(f"⚠️ Warning/Error: OCR process finished with code: {result}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)


# --- This is where we run the script ---
if __name__ == "__main__":
    # Define the files and language
    INPUT_FILE = "input_pdfs/sample.pdf"
    OUTPUT_FILE = "output_pdfs/sample_searchable.pdf"
    LANGUAGE = "eng" # English

    # Create the output directory if it doesn't exist
    os.makedirs("output_pdfs", exist_ok=True)

    # Call our function to perform the OCR
    ocr_pdf(input_path=INPUT_FILE, output_path=OUTPUT_FILE, language_code=LANGUAGE)

    # --- EXAMPLE FOR TURKISH ---
    # To run this for Turkish, you would comment out the English part above
    # and uncomment the lines below. Make sure you have the Turkish language
    # pack installed for Tesseract!
    #
    # print("\n--- Running Turkish Example ---")
    # INPUT_FILE_TR = "input_pdfs/sample_turkish.pdf" # You would need a Turkish sample file
    # OUTPUT_FILE_TR = "output_pdfs/sample_turkish_searchable.pdf"
    # LANGUAGE_TR = "tur"
    # ocr_pdf(input_path=INPUT_FILE_TR, output_path=OUTPUT_FILE_TR, language_code=LANGUAGE_TR)