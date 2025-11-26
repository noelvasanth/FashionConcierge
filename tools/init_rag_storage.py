"""Initialise the local RAG index storage."""

from __future__ import annotations

import argparse
from pathlib import Path

from tools.rag import WardrobeRAG


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialise wardrobe RAG storage")
    parser.add_argument(
        "--database",
        default="data/rag_index.db",
        help="Path to the SQLite database for the RAG index.",
    )
    args = parser.parse_args()

    db_path = Path(args.database)
    rag = WardrobeRAG(database_path=db_path)
    rag._ensure_tables()  # Ensure table exists when run standalone.
    print(f"RAG index ready at {db_path}")


if __name__ == "__main__":
    main()
