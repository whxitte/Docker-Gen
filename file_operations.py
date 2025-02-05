# file_operations.py
import logging
from pathlib import Path
from error_handling import handle_errors

@handle_errors
def write_config(output_dir: str, filename: str, content: str, force: bool = False) -> None:
    """Safely write content to a file with conflict resolution."""
    output_path = Path(output_dir) / filename
    if output_path.exists() and not force:
        raise FileExistsError(f"{output_path} exists. Use --force to overwrite.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    logging.info(f"Generated: {output_path}")
