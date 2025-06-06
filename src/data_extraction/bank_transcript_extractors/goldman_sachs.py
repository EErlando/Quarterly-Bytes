import re
import pandas as pd

from ...constants import BankType

from .base import BaseTranscriptExtractor


class GoldmanSachsTranscriptExtractor(BaseTranscriptExtractor):
    def __init__(self, transcript_file_text: str, quarter: int, year: int):
        self.transcript_file_text = transcript_file_text
        self.participants = self._extract_participants(self.transcript_file_text)
        self._quarter = quarter
        self._year = year

    def _extract_participants(self, text: str):
        """
        Extracts both 'Company Participants' and 'Conference Call Participants' sections from the given text.

        Args:
            text (str): The input text.

        Returns:
            dict: A dictionary with keys 'company_participants' and 'conference_call_participants',
                each containing a dictionary where the key is the participant's name and the value is a list of their roles.
        """
        participants = {}

        def parse_participants(section_text):
            parsed = {}
            for line in section_text.split("\n"):
                if " - " in line:
                    name, roles = line.split(" - ", 1)
                    parsed[name.strip()] = ", ".join(sorted([
                        role.strip() for role in re.split(r"&|and", roles)
                    ]))
            return parsed

        # Extract Company Participants
        company_match = re.search(
            r"Company Participants(.*?)(?:Conference Call Participants|Operator)",
            text,
            re.DOTALL,
        )
        if company_match:
            company_section = company_match.group(1)
            participants["company_participants"] = parse_participants(company_section)
        else:
            participants["company_participants"] = {}

        # Extract Conference Call Participants
        conference_match = re.search(
            r"Conference Call Participants(.*?)(?:Operator)", text, re.DOTALL
        )
        if conference_match:
            conference_section = conference_match.group(1)
            participants["conference_call_participants"] = parse_participants(
                conference_section
            )
        else:
            participants["conference_call_participants"] = {}

        return participants

    def _extract_qna_section(self, text: str) -> str:
        """
        Extracts the Question-and-Answer Session from the given text.

        Args:
            text (str): The input text.

        Returns:
            str: The extracted Question-and-Answer Session text.
        """
        qna_start = "Question-and-Answer Session"
        qna_section = text.split(qna_start, 1)[-1] if qna_start in text else ""
        return qna_section.strip()

    def _split_qna_section(self, qna_text):
        """
        Splits the Q&A section into a structured format with questions and answers.

        Args:
            qna_text (str): The Q&A section text.

        Returns:
            dict: A nested dictionary where each Q&A group is represented as:
                {group_index: {entry_index: {"content_type": "question" | "answer",
                                            "content": "the message",
                                            "speaker": "Speaker Name"}}}
        """
        qna_groups = {}
        current_group = {}
        group_index = 0
        entry_index = 0
        current_speaker = None
        content_type = None
        lines = qna_text.splitlines()

        all_participants = set(
            self.participants["conference_call_participants"].keys()
        ) | set(self.participants["company_participants"].keys())

        for line in lines:
            line = line.strip().lower()
            if not line:
                continue

            # Check if the line is the "Operator" line, which separates groups
            if line.strip().lower() == "operator":
                if current_group:
                    qna_groups[group_index] = current_group
                    group_index += 1
                    current_group = {}
                    entry_index = 0
                    content_type = None
                    current_speaker = None
                continue

            # Check if the line starts with a participant's name
            if line in (name.lower() for name in all_participants):
                if current_group:
                    entry_index += 1
                # Get next speaker
                current_speaker = next(
                    name for name in all_participants if line == name.strip().lower()
                )
                role = self.participants["company_participants"].get(current_speaker, None)
                company =  self.participants["conference_call_participants"].get(current_speaker, None) or BankType.GOLDMAN_SACHS.value
                # Get next content type by participant
                content_type = (
                    "question"
                    if current_speaker
                    in self.participants["conference_call_participants"]
                    else "answer"
                )
                
                current_group[entry_index] = {
                    "content_type": content_type,
                    "content": "",
                    "speaker": current_speaker,
                    "role": role,
                    "company": company,
                }
            else:
                if current_speaker:
                    current_group[entry_index]["content"] += f" {line}"

        # Add the last group if it exists
        if current_group:
            qna_groups[group_index] = current_group

        return qna_groups

    def _extract_management_discussion(self, text: str):
        """
        Extracts the management discussion section from the PDF text.
        """
        internal_participants = list(self.participants["company_participants"].keys())
        management_discussion_end = "Question-and-Answer Session"
        # Split the text into lines for easier processing
        lines = text.splitlines()

        # Initialize variables
        management_discussion_section = []
        is_past_operator_intro = False
        is_in_discussion = False

        # Iterate through the lines
        for line in lines:
            if not is_past_operator_intro:
                if line.strip().lower() == "operator":
                    is_past_operator_intro = True
                continue

            if is_past_operator_intro:
                if (
                    any(participant == line for participant in internal_participants)
                    and not is_in_discussion
                ):
                    # Start capturing the discussion after the operator's introduction
                    is_in_discussion = True

                if is_in_discussion:
                    if management_discussion_end in line:
                        break
                    management_discussion_section.append(line)

        # Join the captured lines into a single string
        management_discussion_section = "\n".join(management_discussion_section)

        return management_discussion_section.strip()

    def _split_management_discussion_section(self, management_discussion_text):
        """
        Splits the management discussion section into a structured format.

        Args:
            management_discussion_text (str): The management discussion section text.

        Returns:
            dict: A dictionary where each entry is represented as:
                {entry_index: {"content_type": "management_discussion",
                                "content": "the message",
                                "speaker": "Speaker Name"}}
        """
        management_discussion = {}
        entry_index = 0
        current_speaker = None
        lines = management_discussion_text.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if the line starts with a participant's name
            if line in self.participants["company_participants"].keys():
                current_speaker = line
                if management_discussion:
                    entry_index += 1

                management_discussion[entry_index] = {
                    "content": "",
                    "speaker": current_speaker,
                    "role": self.participants["company_participants"][current_speaker],
                    "company": BankType.GOLDMAN_SACHS.value,
                }
            else:
                if current_speaker:
                    management_discussion[entry_index]["content"] += f" {line}"

        return management_discussion

    def get_qna(self):
        """
        Extracts the Question-and-Answer Session from the transcript text and structures it.

        Returns:
            dict: A nested dictionary with structured Q&A data.
        """
        return self._split_qna_section(
            self._extract_qna_section(self.transcript_file_text)
        )

    def get_discussion(self):
        """
        Extracts the management discussion section from the transcript text and structures it.

        Returns:
            dict: A dictionary with structured management discussion data.
        """
        return self._split_management_discussion_section(
            self._extract_management_discussion(self.transcript_file_text)
        )

    def get_qna_df(self):
        """
        Extracts the Question-and-Answer Session from the transcript text and structures it.

        Returns:
            dict: A nested dictionary with structured Q&A data.
        """
        extracted_qna = self.get_qna()

        formatted_qna = {
            "question_order": [],
            "question_answer_group_id": [],
            "speaker": [],
            "role": [],
            "company": [],
            "content_type": [],
            "content": [],
            "quarter": [],
            "year": [],
        }

        for question_answer_group_id, qnas in extracted_qna.items():
            for question_order, single_qna_dict in qnas.items():
                formatted_qna["question_order"].append(question_order)
                formatted_qna["question_answer_group_id"].append(
                    question_answer_group_id
                )
                formatted_qna["speaker"].append(single_qna_dict["speaker"])
                formatted_qna["role"].append(single_qna_dict["role"])
                formatted_qna["company"].append(single_qna_dict["company"])
                formatted_qna["content_type"].append(single_qna_dict["content_type"])
                formatted_qna["content"].append(single_qna_dict["content"])
                formatted_qna["quarter"].append(self._quarter)
                formatted_qna["year"].append(self._year)

        # Delete where we only have single question_answer_group_id as this is not useful for q_a (singular question or answer)
        df = pd.DataFrame(formatted_qna)
        counts = df["question_answer_group_id"].value_counts()
        df = df[df["question_answer_group_id"].isin(counts[counts > 1].index)]
        return df
    
    def get_discussion_df(self) -> pd.DataFrame:
        """
        Extracts the management discussion section from the transcript text and structures it.

        Returns:
            pd.DataFrame: A DataFrame with structured management discussion data.
        """
        extracted_management_discussion = self.get_discussion()

        formatted_discussion = {
            "speaker": [],
            "role": [],
            "company": [],
            "content": [],
            "quarter": [],
            "year": [],
        }

        for entry_index, single_discussion_dict in extracted_management_discussion.items():
            formatted_discussion["speaker"].append(single_discussion_dict["speaker"])
            formatted_discussion["role"].append(
                single_discussion_dict["role"]
            )
            formatted_discussion["company"].append(
                single_discussion_dict["company"]
            )
            formatted_discussion["content"].append(single_discussion_dict["content"])
            formatted_discussion["quarter"].append(self._quarter)
            formatted_discussion["year"].append(self._year)

        return pd.DataFrame(formatted_discussion) 
