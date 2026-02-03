"""ChromaDB query operations — retrieves similar verticals and plays."""

from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.graph.state import HistoricalPlay

logger = logging.getLogger(__name__)

COLLECTION_PLAYS = "sales_plays"
COLLECTION_CLIENTS = "client_profiles"


def _get_client(persist_dir: str) -> chromadb.ClientAPI:
    """Get or create a ChromaDB persistent client."""
    return chromadb.PersistentClient(
        path=persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def _get_or_create_collection(
    client: chromadb.ClientAPI, name: str
) -> chromadb.Collection:
    """Get or create a ChromaDB collection."""
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def query_similar_verticals(
    persist_dir: str,
    vertical: str,
    domain: str,
    n_results: int = 5,
) -> list[HistoricalPlay]:
    """Find clients in similar verticals from ChromaDB.
    
    Args:
        persist_dir: ChromaDB storage directory
        vertical: Client's industry vertical
        domain: Client's specific domain
        n_results: Max results to return
        
    Returns:
        List of historical plays from similar clients
    """
    try:
        client = _get_client(persist_dir)
        collection = _get_or_create_collection(client, COLLECTION_CLIENTS)

        if collection.count() == 0:
            logger.info("No historical client data yet — cold start.")
            return []

        results = collection.query(
            query_texts=[f"{vertical} {domain}"],
            n_results=min(n_results, collection.count()),
        )

        plays = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                plays.append(HistoricalPlay(
                    client_name=metadata.get("client_name", "Unknown"),
                    vertical=metadata.get("vertical", vertical),
                    play_summary=doc,
                    outcome=metadata.get("outcome", ""),
                    similarity_score=1.0 - distance,  # Convert distance to similarity
                ))

        logger.info("Found %d similar vertical matches", len(plays))
        return plays

    except Exception as e:
        logger.warning("ChromaDB vertical query failed: %s", e)
        return []


def query_similar_plays(
    persist_dir: str,
    vertical: str,
    research_summary: str,
    n_results: int = 5,
) -> list[HistoricalPlay]:
    """Find similar successful sales plays from ChromaDB.
    
    Args:
        persist_dir: ChromaDB storage directory
        vertical: Client's vertical for context
        research_summary: Summary of the current client research
        n_results: Max results to return
        
    Returns:
        List of similar historical plays
    """
    try:
        client = _get_client(persist_dir)
        collection = _get_or_create_collection(client, COLLECTION_PLAYS)

        if collection.count() == 0:
            logger.info("No historical plays yet — cold start.")
            return []

        query_text = f"{vertical}: {research_summary[:500]}"
        results = collection.query(
            query_texts=[query_text],
            n_results=min(n_results, collection.count()),
        )

        plays = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                plays.append(HistoricalPlay(
                    client_name=metadata.get("client_name", "Unknown"),
                    vertical=metadata.get("vertical", vertical),
                    play_summary=doc,
                    outcome=metadata.get("outcome", ""),
                    similarity_score=1.0 - distance,
                ))

        logger.info("Found %d similar play matches", len(plays))
        return plays

    except Exception as e:
        logger.warning("ChromaDB plays query failed: %s", e)
        return []
