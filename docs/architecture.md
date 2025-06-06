quarterly_bytes/
├── .git/                      # Git repository metadata (hidden)
├── docs/                      # Project documentation (how-to guides, API docs)
│   └── README.md              # Main project README (or link to it)
│   └── architecture.md        # Example Doc
│   └── installation.md        # Example Doc
│
├── notebooks/    
│   ├── 1_data_extraction_and_processing/       # Code related to raw data extraction
│   │   ├── __init__.py
│   │   └── extract_jp_morgan_transcripts.ipynb 
│   ├── 2_exploratory_data_analysis/       # Code related to EDA
│   │   ├── __init__.py
│   │   └── goldman_sachs_eda.ipynb 
│   ├── 3_modelling       # Code related to EDA
│   │   ├── __init__.py
│   │   ├── topic_modelling_goldman_sachs.ipynb 
│   │   └── topic_modelling_goldman_sachs.ipynb 
│   ├── NotebookMaster.ipynb
│   └── exploratory_analysis.ipynb
│
├── src/                       # Source code for the core application logic
│   ├── __init__.py            # Makes 'src' a Python package
│   │
│   ├── data_extraction/       # Code related to raw data extraction
│   │   ├── __init__.py
│   │   ├── bank_transcript_extractors/ # Your bank-specific extractors
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── goldman_sachs.py
│   │   │   └── jp_morgan.py
│   │   │
│   │   └── raw_data_processor.py # Logic for processing raw extracted data
│   │
│   ├── utils/                 # General utility functions, not specific to core business logic
│   │   ├── __init__.py
│   │   └── pdf_utils.py       # Your `extract_text_from_pdf` and other PDF helpers
│   │   └── common_helpers.py  # Other generic utility functions
│   │
│   └── main_app.py            # Or a script that orchestrates the overall workflow
│
├── data/                      # Data storage (often ignored by Git)
│   ├── raw/                   # Original, immutable raw data (e.g., downloaded PDFs)
│   ├── processed/             # Cleaned or transformed data
│   └── temp/                  # Temporary data files (if needed, good candidate for .gitignore)
│
├── .gitignore                 # Files and directories Git should ignore (e.g., /data/, /temp/, venv/)
├── requirements.txt           # Python dependencies for the project
├── environment.yml            # (Optional) For Conda environments
├── setup.py                   # (Optional) For packaging your project as a Python module
└── README.md                  # Main project README (overview, setup, how to run)
