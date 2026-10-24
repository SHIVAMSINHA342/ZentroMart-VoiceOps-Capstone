"""Load ZentroMart synthetic catalog and knowledge-base documents."""

from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
KB_DIR = PROJECT_DIR / "kb"


def load_product_catalog():
    """Load the synthetic product catalog while preserving IDs as strings."""
    path = DATA_DIR / "products.csv"
    if not path.exists():
        raise FileNotFoundError(f"Product catalog not found: {path}")
    return pd.read_csv(path, dtype=str).fillna("")


def load_knowledge_base():
    """Load Markdown knowledge-base files without changing their contents."""
    if not KB_DIR.exists():
        raise FileNotFoundError(f"Knowledge-base directory not found: {KB_DIR}")

    documents = []
    for path in sorted(KB_DIR.glob("*.md")):
        documents.append({
            "filename": path.name,
            "path": str(path),
            "text": path.read_text(encoding="utf-8"),
        })

    if not documents:
        raise RuntimeError(f"No Markdown documents found in {KB_DIR}")

    return documents


def extract_section_id(text):
    """Extract a leading section ID such as [RET-2] when present."""
    import re
    match = re.search(r"^\s*#+\s*\[([A-Za-z0-9._-]+)\]", text)
    return match.group(1) if match else None
