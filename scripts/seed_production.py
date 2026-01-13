"""
Seed production database with retirement planning documents.
Run this after deploying to Render.

Usage:
    python scripts/seed_production.py https://clarity-api.onrender.com
"""
import os
import sys
import requests
import time
from pathlib import Path

def ingest_file(api_url: str, file_path: Path):
    """Ingest a single markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title from filename
        title = file_path.stem.replace('-', ' ').replace('_', ' ').title()

        # Send to API
        print(f"📄 Ingesting: {title}...", end=" ")
        response = requests.post(
            f"{api_url}/admin/ingest",
            json={
                "title": title,
                "content": content,
                "source_url": f"file://{file_path.name}",
                "source_type": "markdown",
                "published_date": None,
            },
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ ({data['chunk_count']} chunks)")
            return data['document_id']
        else:
            print(f"✗ Failed: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def approve_document(api_url: str, doc_id: int):
    """Approve a document for retrieval."""
    try:
        response = requests.post(
            f"{api_url}/admin/documents/{doc_id}/approve",
            timeout=30
        )
        return response.status_code == 200
    except Exception as e:
        print(f"  Error approving document {doc_id}: {e}")
        return False


def main():
    """Seed production database."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/seed_production.py <API_URL>")
        print("Example: python scripts/seed_production.py https://clarity-api.onrender.com")
        sys.exit(1)

    api_url = sys.argv[1].rstrip('/')

    print("=" * 60)
    print("🌱 SEEDING PRODUCTION DATABASE")
    print("=" * 60)
    print(f"API URL: {api_url}\n")

    # Check API health
    print("🔍 Checking API health...", end=" ")
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            print("✓ API is healthy\n")
        else:
            print(f"✗ API returned {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Cannot reach API: {e}")
        sys.exit(1)

    # Find markdown files
    import_dir = Path(__file__).parent.parent / "data" / "import"
    md_files = list(import_dir.glob("*.md"))

    if not md_files:
        print("❌ No markdown files found in data/import/")
        sys.exit(1)

    print(f"📚 Found {len(md_files)} document(s) to ingest\n")

    # Ingest files
    doc_ids = []
    for md_file in md_files:
        doc_id = ingest_file(api_url, md_file)
        if doc_id:
            doc_ids.append(doc_id)
        time.sleep(1)  # Rate limiting

    print(f"\n{'=' * 60}")
    print(f"📋 Ingestion Summary")
    print(f"{'=' * 60}")
    print(f"Total files: {len(md_files)}")
    print(f"Successfully ingested: {len(doc_ids)}")
    print(f"Failed: {len(md_files) - len(doc_ids)}")

    if not doc_ids:
        print("\n❌ No documents were ingested successfully")
        sys.exit(1)

    # Approve documents
    print(f"\n{'=' * 60}")
    print(f"✅ Approving documents for retrieval")
    print(f"{'=' * 60}")

    approved = 0
    for doc_id in doc_ids:
        print(f"Approving document {doc_id}...", end=" ")
        if approve_document(api_url, doc_id):
            print("✓")
            approved += 1
        else:
            print("✗")
        time.sleep(0.5)

    print(f"\n{'=' * 60}")
    print(f"🎉 SEEDING COMPLETE!")
    print(f"{'=' * 60}")
    print(f"✓ {approved}/{len(doc_ids)} documents approved and ready for RAG")
    print(f"\nYour production database is now seeded! 🚀")


if __name__ == "__main__":
    main()
