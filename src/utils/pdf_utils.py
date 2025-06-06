from typing import Tuple, Optional

from ..data_extraction.bank_transcript_extractors import GoldmanSachsTranscriptExtractor, JpMorganTranscriptExtractor
import PyPDF2
import logging
import re
import os
import pandas as pd
from ..constants import BankType

logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")


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
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except PyPDF2.errors.FileNotDecryptedError:
                    logging.error(
                        f"PDF '{pdf_path}' is encrypted and cannot be decrypted without a password."
                    )
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
                    logging.warning(
                        f"Could not extract text from page {page_num + 1} of '{pdf_path}'. It might contain images or scanned content."
                    )

    except FileNotFoundError:
        logging.error(f"PDF file not found at: '{pdf_path}'")
    except PyPDF2.errors.PdfReadError as e:
        logging.error(
            f"Error reading PDF file '{pdf_path}'. It might be corrupted or not a valid PDF: {e}"
        )
    except Exception as e:
        logging.error(
            f"An unexpected error occurred while processing '{pdf_path}': {e}"
        )

    return extracted_text.strip()


def extract_participants_sections(text):
    """
    Extracts both 'Company Participants' and 'Conference Call Participants' sections from the given text.

    Args:
        text (str): The input text.

    Returns:
        dict: A dictionary with keys 'company_participants' and 'conference_call_participants',
              each containing a list of participants.
    """
    participants = {}

    # Extract Company Participants
    company_match = re.search(
        r"Company Participants(.*?)(?:Conference Call Participants|Operator)",
        text,
        re.DOTALL,
    )
    if company_match:
        company_section = company_match.group(1)
        participants["company_participants"] = [
            line.strip() for line in company_section.split("\n") if line.strip()
        ]
    else:
        participants["company_participants"] = []

    # Extract Conference Call Participants
    conference_match = re.search(
        r"Conference Call Participants(.*?)(?:Operator)", text, re.DOTALL
    )
    if conference_match:
        conference_section = conference_match.group(1)
        participants["conference_call_participants"] = [
            line.strip() for line in conference_section.split("\n") if line.strip()
        ]
    else:
        participants["conference_call_participants"] = []

    return participants


def extract_quarter_and_year_from_filename(
    filename: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts the quarter and full year from a given filename based on the
    pattern "QqYY_".

    Examples of expected filenames:
    - "1q22_earnings_transcript.pdf"
    - "4q23_report.docx"
    - "2q25_analysis.txt"

    Args:
        filename (str): The name of the file (or full path) from which to extract
                        the quarter and year.

    Returns:
        Tuple[Optional[str], Optional[str]]: A tuple containing:
            - The extracted quarter string (e.g., "1q", "2q"), or None if not found.
            - The extracted full year string (e.g., "2022", "2023"), or None if not found.
            Returns (None, None) if the pattern is not found.
    """
    # Regex pattern:
    # (\d{1})    - Captures a single digit (1-4) for the quarter. This is Group 1.
    # q          - Matches the literal 'q'.
    # (\d{2})    - Captures exactly two digits for the year. This is Group 2.
    # _          - Matches the literal underscore immediately following the year.
    # re.IGNORECASE - Makes the 'q' match both 'q' and 'Q'.
    pattern = re.compile(r"(\d{1})q(\d{2})[_-]", re.IGNORECASE)


    match = pattern.search(filename)

    if match:
        quarter_num = match.group(1) # e.g., '1', '2'
        year_short = match.group(2)  # e.g., '22', '23'

        # Construct the quarter string (e.g., "1q", "2q")
        # quarter_str = f"{quarter_num}q"

        # Convert two-digit year to four-digit year.
        # This assumes all years are in the 21st century (2000-2099).
        try:
            year_int = int(year_short)
            if 0 <= year_int <= 99:
                full_year = f"20{year_short}"
            else:
                # Fallback for unexpected 2-digit years outside typical range, though unlikely with your pattern
                full_year = f"19{year_short}" if year_int > 50 else f"20{year_short}" # Basic heuristic
                # A more robust solution might involve passing a century or using a cutoff year
        except ValueError:
            # Should not happen if regex matches \d{2}, but good for robustness
            full_year = None

        return quarter_num, full_year
    else:
        return None, None
    
def extract_transcripts_pdf_df_from_dir(transcripts_dir: str, bank_type: BankType) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extracts financial transcript data from PDF files within a specified directory
    and organizes it into two Pandas DataFrames: one for Q&A sections and one
    for discussion sections. The extraction logic varies based on the bank type.

    Args:
        transcripts_dir (str): The path to the directory containing the PDF
                               transcript files.
        bank_type (BankType): An enumeration member indicating the type of bank
                              (e.g., BankType.GOLDMAN_SACHS, BankType.JPMORGAN_CHASE)
                              to determine the correct parsing strategy.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: A tuple containing two Pandas DataFrames:
                                           - qna_df: Contains extracted Q&A data.
                                           - discussion_df: Contains extracted discussion data.
                                           Returns (None, None) if no PDFs are processed
                                           or if no data is extracted for the given bank type.
    """
    pdf_files_path = [os.path.join(transcripts_dir, file) for file in os.listdir(transcripts_dir) if file.endswith('.pdf')]

    qna_df = None
    discussion_df = None
    for pdf_file_path in pdf_files_path:
        quarter, year = extract_quarter_and_year_from_filename(os.path.basename(pdf_file_path))
        extracted_text = extract_text_from_pdf(pdf_file_path)

        match bank_type:
            case BankType.GOLDMAN_SACHS:
                extractor = GoldmanSachsTranscriptExtractor(extracted_text, quarter, year)
                qna_df = extractor.get_qna_df() if qna_df is None else pd.concat([qna_df, extractor.get_qna_df()], ignore_index=True)
                discussion_df = extractor.get_discussion_df() if discussion_df is None else pd.concat([discussion_df, extractor.get_discussion_df()], ignore_index=True)

            case BankType.JPMORGAN:
                extractor = JpMorganTranscriptExtractor(extracted_text, quarter, year)
                qna_df_cur, discussion_df_cur = extractor.parse_transcript_to_dataframes()

                discussion_df_cur["year"] = year
                discussion_df_cur["quarter"] = quarter
                qna_df_cur["year"] = year
                qna_df_cur["quarter"] = quarter
                qna_df = pd.concat([qna_df, qna_df_cur], ignore_index=True)
                discussion_df = pd.concat([discussion_df, discussion_df_cur], ignore_index=True)

                misspelt_roles_dict = {
                    "  ": " ",
                    ' ,': ',',
                    'Of ficer': 'Officer',
                    'Financ ial': 'Financial',
                    'Morg an': 'Morgan',
                    'Finan cial': 'Financial',
                    'Fina ncial': 'Financial',
                    'Fin ancial': 'Financial',
                    'Analy st': 'Analyst',
                    'Cha irman': 'Chairman',
                    'JPMo rgan': 'JPMorgan',
                    'JPMorganChase': 'JPMorgan Chase & Co.',
                    'JPMorga n': 'JPMorgan',
                    'JP Morgan': 'JPMorgan',
                    'Off icer': 'Officer',
                    'JPMor gan': 'JPMorgan',
                    'JPM organ': 'JPMorgan',
                    'Chair man': 'Chairman',
                    'Membe r': 'Member',
                    '-O': 'O',
                    'Membe rOperating': 'Member Operating',
                    'M ember': 'Member',
                    'Offi cer': 'Officer',
                    '& C o': '& Co',
                    'Chas e': 'Chase',
                    'C hief': 'Chief',
                    'Oper ating': 'Operating',
                    'Comm ittee': 'Committee',
                    'Execut ive': 'Executive',
                    'Financia l': 'Financial',
                    'Ch ief': 'Chief',
                    'Co .': 'Co.',
                    'Officer ,': 'Officer,',
                    'Financi al': 'Financial',
                    'M ember': 'Member',
                    'MemberOperating': 'Member Operating',
                    'Chie f': 'Chief',
                    'Mor gan': 'Morgan',
                    'M organ': 'Morgan',
                    'C apital': 'Capital',
                    'Ev ercore': 'Evercore',
                    'Ever core': 'Evercore',
                    'Evercor e': 'Evercore',
                    'Ame rica': 'America',
                    'Amer ica': 'America',
                    'P ortales': 'Portales',
                    'Po rtales': 'Portales',
                    'Seapor t': 'Seaport',
                    'Seap ort': 'Seaport',
                    'Farg o': 'Fargo',
                    'Ca pital': 'Capital',
                    'Ba nk': 'Bank',
                    'Amer ica': 'America',
                    'Secur ities': 'Securities',
                    'Well s': 'Wells',
                    'In c': 'Inc',
                    'Autono mous': 'Autonomous',
                    'Auton omous': 'Autonomous',
                    'S ecurities': 'Securities',
                    'M errill': 'Merrill',
                    'Inc .': 'Inc.',
                    'Deutsc he': 'Deutsche',
                    'Chief Financial Officer & Member Operating Committee, JPMorgan Chase & Co.': 'Chief Financial Officer, JPMorgan Chase & Co.'
                }


                def correct_roles(role):
                    for misspelt_role in misspelt_roles_dict.keys():
                        if misspelt_role in role:
                            role = role.replace(misspelt_role, misspelt_roles_dict[misspelt_role])
                            break
                    return role
                
                discussion_df['role'] = discussion_df['role'].apply(correct_roles)
                discussion_df['role'].unique()
                
                qna_df.sort_values(by=['year', 'quarter', 'question_answer_group_id'], ascending=True, inplace=True)
                qna_df.reset_index(drop=True, inplace=True)

                discussion_df.sort_values(by=['year', 'quarter'], ascending=True, inplace=True)
                discussion_df.reset_index(drop=True, inplace=True)
                
    return qna_df, discussion_df
