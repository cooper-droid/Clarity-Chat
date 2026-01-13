"""
Document approval script.
Approves all draft documents so they can be retrieved.
"""
import os
import sys
import requests
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

API_URL = os.getenv("API_URL", "http://localhost:8000")


def get_all_documents():
    """Get all documents from the database."""
    # This is a simple version - in a real app you'd have a GET /admin/documents endpoint
    # For now, we'll just try to approve documents 1-100
    return list(range(1, 101))


def approve_document(doc_id: int):
    """Approve a single document."""
    try:
        response = requests.post(f"{API_URL}/admin/approve/{doc_id}")

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Approved: {data['title']} (ID: {data['document_id']})")
            return True
        elif response.status_code == 404:
            # Document doesn't exist, skip silently
            return False
        else:
            print(f"✗ Failed to approve document {doc_id}: {response.text}")
            return False

    except Exception as e:
        # Silently skip errors (likely just non-existent document IDs)
        return False


def main():
    """Approve all draft documents."""
    print(f"Fiat Clarity Chat - Document Approval")
    print(f"====================================\n")

    # Try to approve documents 1-100
    doc_ids = get_all_documents()
    approved_count = 0

    for doc_id in doc_ids:
        if approve_document(doc_id):
            approved_count += 1

    print(f"\n✅ Approval complete!")
    print(f"   Approved: {approved_count} document(s)")
    print(f"\nDocuments are now available for retrieval in the chat.")


if __name__ == "__main__":
    main()
