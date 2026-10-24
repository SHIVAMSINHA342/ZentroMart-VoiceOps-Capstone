"""Parse Markdown documents and inherit document-level policy metadata."""

import re
from .data_loader import load_knowledge_base


def parse_knowledge_sections():
    sections = []

    for document in load_knowledge_base():
        filename = document["filename"]
        content = document["text"]

        # Read simple YAML-style front matter between --- delimiters.
        metadata = {}
        front = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", content, re.S)
        if front:
            for line in front.group(1).splitlines():
                match = re.match(r"^\s*([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$", line)
                if match:
                    metadata[match.group(1).lower()] = match.group(2).strip().strip('"').strip("'")

        headings = list(re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", content))
        if not headings and content.strip():
            sections.append({
                "filename": filename,
                "doc_type": metadata.get("doc_type", "unknown"),
                "status": metadata.get("status", "unknown"),
                "effective_from": metadata.get("effective_from") or metadata.get("effective date"),
                "superseded_by": metadata.get("superseded_by"),
                "section_id": filename.removesuffix(".md"),
                "heading": filename,
                "text": content.strip(),
            })
            continue

        for index, match in enumerate(headings):
            start = match.start()
            end = headings[index + 1].start() if index + 1 < len(headings) else len(content)
            section_text = content[start:end].strip()
            heading = match.group(1).strip()

            id_match = re.search(r"\[([A-Za-z0-9._-]+)\]", heading)
            section_id = id_match.group(1) if id_match else f"{filename}#{index + 1}"

            # Section-level values override inherited document-level values.
            status_match = re.search(r"(?im)^\s*(?:status|policy status)\s*:\s*(.+?)\s*$", section_text)
            date_match = re.search(r"(?im)^\s*(?:effective from|effective date)\s*:\s*(.+?)\s*$", section_text)

            sections.append({
                "filename": filename,
                "doc_type": metadata.get("doc_type", "unknown"),
                "status": status_match.group(1).strip() if status_match else metadata.get("status", "unknown"),
                "effective_from": date_match.group(1).strip() if date_match else metadata.get("effective_from") or metadata.get("effective date"),
                "superseded_by": metadata.get("superseded_by"),
                "section_id": section_id,
                "heading": heading,
                "text": section_text,
            })

    return sections
