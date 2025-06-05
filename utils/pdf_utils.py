import PyPDF2
import logging

logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        str: The extracted text from the PDF, or an empty string if an error occurs.
    """
    extracted_text = ""
    if not pdf_path:
        logging.error("PDF path cannot be empty.")
        return extracted_text

    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            if reader.is_encrypted:
                try:
                    reader.decrypt('')
                except PyPDF2.errors.FileNotDecryptedError:
                    logging.error(f"PDF '{pdf_path}' is encrypted and cannot be decrypted without a password.")
                    return extracted_text
                except Exception as e:
                    logging.error(f"Error during PDF decryption of '{pdf_path}': {e}")
                    return extracted_text

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n" 
                else:
                    logging.warning(f"Could not extract text from page {page_num + 1} of '{pdf_path}'. It might contain images or scanned content.")

    except FileNotFoundError:
        logging.error(f"PDF file not found at: '{pdf_path}'")
    except PyPDF2.errors.PdfReadError as e:
        logging.error(f"Error reading PDF file '{pdf_path}'. It might be corrupted or not a valid PDF: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while processing '{pdf_path}': {e}")

    return extracted_text.strip()