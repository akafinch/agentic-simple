"""File save tool for the Writer agent."""

from pathlib import Path
from backend.config import OUTPUT_DIR


def save_report(filename: str, content: str) -> str:
    """Save content to the output directory. Returns the relative path."""
    safe_filename = "".join(c if c.isalnum() or c in "-_." else "_" for c in filename)
    if not safe_filename.endswith(".md"):
        safe_filename += ".md"
    filepath = OUTPUT_DIR / safe_filename
    filepath.write_text(content, encoding="utf-8")
    return safe_filename
