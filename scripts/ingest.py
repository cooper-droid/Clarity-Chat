"""
Document ingestion script.
Reads markdown files from data/import and ingests them into the database.
"""
import os
import sys
import requests
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

API_URL = os.getenv("API_URL", "http://localhost:8000")
IMPORT_DIR = Path(__file__).parent.parent / "data" / "import"


def ingest_file(file_path: Path):
    """Ingest a single markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title from filename or first line
        title = file_path.stem.replace('-', ' ').replace('_', ' ').title()

        # Try to extract date from filename (YYYY-MM-DD format)
        published_date = None
        parts = file_path.stem.split('-')
        if len(parts) >= 3:
            try:
                year, month, day = parts[0:3]
                if len(year) == 4 and year.isdigit():
                    published_date = f"{year}-{month}-{day}"
            except:
                pass

        # Send to API
        response = requests.post(
            f"{API_URL}/admin/ingest",
            json={
                "title": title,
                "content": content,
                "source_url": f"file://{file_path}",
                "source_type": "markdown",
                "published_date": published_date,
            }
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Ingested: {title}")
            print(f"  Document ID: {data['document_id']}")
            print(f"  Chunks: {data['chunk_count']}")
            print(f"  Status: {data['status']}")
            return data['document_id']
        else:
            print(f"✗ Failed to ingest {title}: {response.text}")
            return None

    except Exception as e:
        print(f"✗ Error ingesting {file_path}: {e}")
        return None


def main():
    """Ingest all markdown files from import directory."""
    print(f"Fiat Clarity Chat - Document Ingestion")
    print(f"======================================\n")
    print(f"Looking for files in: {IMPORT_DIR}\n")

    if not IMPORT_DIR.exists():
        print(f"Error: Import directory not found: {IMPORT_DIR}")
        return

    # Find all markdown files
    md_files = list(IMPORT_DIR.glob("*.md"))

    if not md_files:
        print("No markdown files found in import directory.")
        return

    print(f"Found {len(md_files)} markdown file(s)\n")

    # Ingest each file
    doc_ids = []
    for md_file in md_files:
        doc_id = ingest_file(md_file)
        if doc_id:
            doc_ids.append(doc_id)
        print()

    print(f"\n✅ Ingestion complete!")
    print(f"   Processed: {len(md_files)} files")
    print(f"   Successful: {len(doc_ids)} files")
    print(f"\nNext step: Run 'python scripts/approve.py' to approve documents for retrieval.")


if __name__ == "__main__":
    main()
