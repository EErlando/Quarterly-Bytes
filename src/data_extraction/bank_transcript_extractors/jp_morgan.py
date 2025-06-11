import re
import pandas as pd

from ...constants import BankType

from .base import BaseTranscriptExtractor


class JpMorganTranscriptExtractor(BaseTranscriptExtractor):
    def __init__(self, transcript_file_text: str, quarter: int, year: int):
        self.transcript_file_text = transcript_file_text
        self._quarter = quarter
        self._year = year

        ## Dictionary of misspelt roles in the transcripts
        self._misspelt_roles_dict = {
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
            'Chief Financial Officer & Member Operating Committee, JPMorgan Chase & Co.': 'Chief Financial Officer, JPMorgan Chase & Co.',
            'Chairman & Chief Executive Officer': 'Chief Executive Officer'
        }

    def _extract_blocks_from_section(self, processed_text):
        # Define the separator pattern (newline, dots, newline)
        separator_regex = r"\.{10,}"

        # Split the text into blocks using the separator
        blocks = re.split(separator_regex, processed_text)

        # Filter out any empty blocks that might result from splitting
        blocks = [block.strip() for block in blocks if block.strip()]
        cleaned_blocks = []

        for block in blocks:
            lines = block.split("\n")
            lines = [
                line.strip() for line in lines if line.strip()
            ]  # Clean empty lines within the block
            lines = [
                line for line in lines if not line.isdigit()
            ]  # Clean lines with page number

            if not lines:
                continue  # Skip empty blocks

            cleaned_blocks.append("\n".join(lines))

        return cleaned_blocks

    def _correct_role_spelling(self, role_name) -> str:
        """
        Corrects any spelling or pdf conversion issues in the roles of the speaker

        Returns:
            str: correctly spelled role.
        """
        role_name = role_name.strip()
        for misspelt_role in self._misspelt_roles_dict.keys():
            if misspelt_role in role_name:
                role_name = role_name.replace(misspelt_role, self._misspelt_roles_dict[misspelt_role])
        return role_name.strip()

    def get_qna(self, full_text):
        """
        Parses a Q&A transcript into a list of speaker, role, and text dictionaries,
        assuming speaker name is line 1, role is line 2, and text is subsequent lines.
        Handles the special 'Operator' case.

        Args:
            full_text (str): The complete transcript text.

        Returns:
            pd.DataFrame: A DataFrame with 'question_answer_group_id', 'speaker', 'role', and 'content' columns.
        """
        entries = []

        # Add an implicit separator at the end to ensure the last block is captured
        processed_text = re.sub(
            r"^\s*QUESTION AND ANSWER SECTION\s*\n+",
            "",
            full_text,
            flags=re.MULTILINE,
        ).strip()
        processed_text += "\n........................................................................................"

        blocks = self._extract_blocks_from_section(processed_text)

        # Initialise the question group index
        question_group_index = 0
        question_order = 0

        for block in blocks:
            lines = block.split("\n")
            lines = [
                line.strip() for line in lines if line.strip()
            ]  # Clean empty lines within the block
            lines = [
                line for line in lines if not line.isdigit()
            ]  # Clean lines with page number

            speaker_name = "N/A"
            role_name = "N/A"
            text_content = ""

            if not lines:
                continue  # Skip empty blocks

            # Some/most operator lines are one liners, and has some formatting issues so we'll use 'in' check instead of startswith
            if len(lines) == 1 or any('operator:' in line.replace(" ", '').lower() for line in lines):
                if any('operator:' in line.replace(" ", '').lower() for line in lines):
                    question_group_index = question_group_index + 1
                    question_order = 0
                continue

            if lines[0].startswith("."):
                start_index = 1
                
            # Handle the disclaimer at the end
            if lines[0].startswith("Disclaimer"):
                continue

            else:  # Standard speaker: Name on line 1, Role on line 2, Text after
                if len(lines) >= 1:
                    speaker_name = lines[0]
                if len(lines) >= 2:
                    role_name = lines[1]
                    # Final cleanup for the role
                    role_name = self._correct_role_spelling(role_name)
                    # Remove optional Q/A from role
                    role_name = re.sub(r"\s*(Q|A)$", "", role_name).strip()
                    role_name, company_name = (
                        role_name.split(",")[0].strip(),
                        role_name.split(",")[-1].strip(),
                    )
                    company_name = (
                        BankType.JPMORGAN.value
                        if "morgan" in company_name.lower()
                        and "jp".lower() in company_name.lower()
                        else company_name
                    )
                if len(lines) > 2:
                    text_content = "\n".join(lines[2 :])

            # Final cleanup for text content (e.g., removing any leading/trailing blank lines)
            text_content = text_content.strip()

            entries.append(
                {
                    "question_order": question_order,
                    "question_answer_group_id": question_group_index,
                    "speaker": speaker_name,
                    "role": role_name,
                    "company": company_name,
                    "content": text_content,
                }
            )

            question_order += 1

        return entries

    def get_discussion(self, full_text):
        """
        Parses the Management Discussion section from a transcript into a pandas dataframe
        with 'speaker', 'role', 'content' columns.

        Args:
            full_text (str): The complete transcript text.

        Returns:
            List: A list of objects that contain the speaker, role, company and content.
        """
        entries = []

        # Add an implicit separator at the end to ensure the last block is captured
        processed_text = full_text.strip()
        processed_text += "\n........................................................................................"

        blocks = self._extract_blocks_from_section(processed_text)

        for block in blocks:
            lines = block.split("\n")
            lines = [
                line.strip() for line in lines if line.strip()
            ]  # Clean empty lines within the block
            lines = [
                line for line in lines if not line.isdigit()
            ]  # Clean lines with page number

            speaker_name = "N/A"
            role_name = "N/A"
            text_content = ""

            if not lines:
                continue  # Skip empty blocks

            # Handle the Operator case: Speaker and start of text are on the first line
            if lines[0].startswith("Operator"):
                continue

            else:  # Standard speaker: Name on line 1, Role on line 2, Text after
                if len(lines) >= 1:
                    speaker_name = lines[0]
                if len(lines) >= 2:
                    role_name = lines[1]
                    role_name = self._correct_role_spelling(role_name)
                    role_name, company_name = (
                        role_name.split(",")[0].strip(),
                        role_name.split(",")[-1].strip(),
                    )
                    company_name = (
                        BankType.JPMORGAN.value
                        if "morgan" in company_name.lower()
                        and "jp".lower() in company_name.lower()
                        else company_name
                    )
                if len(lines) > 2:
                    text_content = "\n".join(lines[2:])

            # Final cleanup for text content (e.g., removing any leading/trailing blank lines)
            text_content = text_content.strip()

            entries.append(
                {
                    "speaker": speaker_name,
                    "role": role_name,
                    "company": company_name,
                    "content": text_content,
                }
            )

        return entries

    def get_qna_df(self, full_text) -> pd.DataFrame:
        """
        Extracts the Question-and-Answer Session from the transcript text and structures it.

        Returns:
            dict: A nested dictionary with structured Q&A data.
        """
        extracted_qna = self.get_qna(full_text)
        return pd.DataFrame(extracted_qna)

    def get_discussion_df(self, full_text) -> pd.DataFrame:
        """
        Extracts the management discussion section from the transcript text and structures it.

        Returns:
            pd.DataFrame: A DataFrame with structured management discussion data.
        """
        extracted_discussion = self.get_discussion(full_text)
        return pd.DataFrame(extracted_discussion)

    def parse_transcript_to_dataframes(self):
        """Parses a raw transcript text into a DataFrame of speaking turns."""

        # Initial Cleaning
        # Remove source tags
        text = re.sub(r"\\", "", self.transcript_file_text)
        # Condense multiple newlines
        text = re.sub(r"\n{2,}", "\n", text).strip()

        # Section Segmentation
        sections = re.split(
            r"(MANAGEMENT DISCUSSION SECTION|QUESTION AND ANSWER SECTION)", text
        )
        sections = [section.strip() for section in sections if section.strip()]
        current_section_name = (
            "INTRO"  # Default for anything before first section header
        )

        df_q_and_a = pd.DataFrame()
        df_presentation = pd.DataFrame()

        # Iterate through the sections and their content
        for i, part in enumerate(sections):
            # skip if the part is empty
            if not part.strip():
                continue

            # Store the section name then move onto the content of the section
            if part in ["MANAGEMENT DISCUSSION SECTION", "QUESTION AND ANSWER SECTION"]:
                current_section_name = part
                continue

            # If we're looking at the Q&A section, then parse to the Q&A dataframe
            if current_section_name == "QUESTION AND ANSWER SECTION":
                df_q_and_a = self.get_qna_df(part)

            # If we're looking at the Q&A section, then parse to the Q&A dataframe
            if current_section_name == "MANAGEMENT DISCUSSION SECTION":
                df_presentation = self.get_discussion_df(part)

        return df_q_and_a, df_presentation
