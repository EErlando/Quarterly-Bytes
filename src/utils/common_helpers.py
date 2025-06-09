import yaml
import os

def read_yaml_file(filepath: str) -> dict:
    """
    Reads and parses a YAML file from the given filepath.

    Args:
        filepath (str): The full or relative path to the YAML file.

    Returns:
        dict: A dictionary containing the data from the YAML file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        yaml.YAMLError: If there is an error parsing the YAML content.
        Exception: For any other unexpected errors during file reading.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"YAML file not found at: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        return data
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file {filepath}: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred while reading {filepath}: {e}")
    


def read_list_from_text_file(filepath: str) -> list[str]:
    """
    Reads a list of strings from a plain text file,
    treating each non-empty, non-comment line as an item.

    Lines starting with '#' are considered comments and ignored.
    Leading/trailing whitespace is stripped from each item.

    Args:
        filepath (str): The full or relative path to the text file.

    Returns:
        list[str]: A list of strings read from the file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        Exception: For any other unexpected errors during file reading.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Text file not found at: {filepath}")

    items = []
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith('#'):
                    items.append(stripped_line)
        return items
    except Exception as e:
        raise Exception(f"An unexpected error occurred while reading {filepath}: {e}")