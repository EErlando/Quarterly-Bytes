from abc import ABC, abstractmethod
import pandas as pd


class BaseTranscriptExtractor(ABC):
    """
    Abstract Base Class for extracting information from bank transcripts.
    This class defines the common interface and shared logic for all transcript
    extractors.
    """
    @abstractmethod
    def get_qna(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_discussion(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_qna_df(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_discussion_df(self) -> pd.DataFrame:
        pass