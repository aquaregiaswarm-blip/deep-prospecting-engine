"""ChromaDB store operations — saves new plays and client profiles for future use."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, UTC

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.graph.state import ProspectingState, SalesPlay

logger = logging.getLogger(__name__)

COLLECTION_PLAYS = "sales_plays"
COLLECTION_CLIENTS = "client_profiles"


def _get_client(persist_dir: str) -> chromadb.ClientAPI:
    """Get or create a ChromaDB persistent client."""
    return chromadb.PersistentClient(
        path=persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def store_plays(persist_dir: str, state: ProspectingState) -> int:
    """Store refined sales plays into ChromaDB for future retrieval.
    
    Args:
        persist_dir: ChromaDB storage directory
        state: Current prospecting state with refined plays
        
    Returns:
        Number of plays stored
    """
    if not state.refined_plays:
        logger.info("No refined plays to store.")
        return 0

    try:
        client = _get_client(persist_dir)
        collection = client.get_or_create_collection(
            name=COLLECTION_PLAYS,
            metadata={"hnsw:space": "cosine"},
        )

        documents = []
        metadatas = []
        ids = []

        for play in state.refined_plays:
            doc = (
                f"{play['title']}: {play['challenge']} → {play['proposed_solution']} "
                f"→ {play['business_outcome']}"
            )
            documents.append(doc)
            metadatas.append({
                "client_name": state.client_name,
                "vertical": state.client_vertical,
                "domain": state.client_domain,
                "title": play["title"],
                "outcome": play["business_outcome"][:200],
                "confidence_score": str(play.get("confidence_score", 0.0)),
                "created_at": datetime.now(UTC).isoformat(),
            })
            ids.append(str(uuid.uuid4()))

        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        logger.info("Stored %d plays for %s", len(documents), state.client_name)
        return len(documents)

    except Exception as e:
        logger.error("Failed to store plays: %s", e)
        return 0


def store_client_profile(persist_dir: str, state: ProspectingState) -> bool:
    """Store the client profile for vertical matching in future runs.
    
    Args:
        persist_dir: ChromaDB storage directory
        state: Current prospecting state with client info
        
    Returns:
        True if stored successfully
    """
    try:
        client = _get_client(persist_dir)
        collection = client.get_or_create_collection(
            name=COLLECTION_CLIENTS,
            metadata={"hnsw:space": "cosine"},
        )

        doc = (
            f"{state.client_name} - {state.client_vertical} / {state.client_domain}. "
            f"{state.digital_maturity_summary} "
            f"Plays: {', '.join(p['title'] for p in state.refined_plays)}"
        )

        collection.add(
            documents=[doc],
            metadatas=[{
                "client_name": state.client_name,
                "vertical": state.client_vertical,
                "domain": state.client_domain,
                "outcome": f"{len(state.refined_plays)} plays generated",
                "created_at": datetime.now(UTC).isoformat(),
            }],
            ids=[str(uuid.uuid4())],
        )
        logger.info("Stored client profile for %s", state.client_name)
        return True

    except Exception as e:
        logger.error("Failed to store client profile: %s", e)
        return False
