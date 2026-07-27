import re


def sanitise_input(text: str, max_length: int = 2000) -> str:
    """Sanitise user input."""
    return text[:max_length].strip()

def extract_mentions(text: str) -> list:
    """Extract user mentions from text."""
    pattern = r'@(\w+)'
    return re.findall(pattern, text)
