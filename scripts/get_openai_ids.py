"""
Get your OpenAI Vector Store ID and Assistant ID.
Run this to find the IDs you need for your .env file.

Usage:
    export OPENAI_API_KEY=your-key-here
    python scripts/get_openai_ids.py
"""
import os
import sys
from openai import OpenAI

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("\nUsage:")
        print("  export OPENAI_API_KEY=your-key-here")
        print("  python scripts/get_openai_ids.py")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print("=" * 60)
    print("🔍 FINDING YOUR OPENAI RESOURCES")
    print("=" * 60)

    # List Vector Stores
    print("\n📦 Vector Stores:")
    try:
        vector_stores = client.beta.vector_stores.list()
        if vector_stores.data:
            for vs in vector_stores.data:
                print(f"\n  Name: {vs.name}")
                print(f"  ID: {vs.id}")
                print(f"  Files: {vs.file_counts.total if hasattr(vs, 'file_counts') else 'N/A'}")

                # Check if this is "Clarity Storage"
                if "clarity" in vs.name.lower():
                    print(f"  ✓ This looks like your Clarity Storage!")
                    print(f"\n  Add to .env:")
                    print(f"  OPENAI_VECTOR_STORE_ID={vs.id}")
        else:
            print("  No vector stores found")
    except Exception as e:
        print(f"  Error: {e}")

    # List Assistants
    print("\n\n🤖 Assistants:")
    try:
        assistants = client.beta.assistants.list()
        if assistants.data:
            for asst in assistants.data:
                print(f"\n  Name: {asst.name}")
                print(f"  ID: {asst.id}")
                print(f"  Model: {asst.model}")

                # Check if this is "Clarity"
                if "clarity" in asst.name.lower():
                    print(f"  ✓ This looks like your Clarity assistant!")
                    print(f"\n  Add to .env:")
                    print(f"  OPENAI_ASSISTANT_ID={asst.id}")
        else:
            print("  No assistants found")
            print("\n  💡 Don't worry! The app will create one automatically using your vector store.")
    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("✅ DONE")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Copy the IDs above to apps/api/.env")
    print("2. Set USE_ASSISTANTS_API=true")
    print("3. Set DEV_MODE=false")
    print("4. Restart your API server")

if __name__ == "__main__":
    main()
