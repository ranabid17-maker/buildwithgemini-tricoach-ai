# Copyright 2026 Google LLC
# RAG Retrieval Tool for Vertex AI Serverless Corpus
import vertexai
from vertexai.preview import rag

PROJECT_ID = "qwiklabs-gcp-01-11b4cbda191e"
LOCATION = "us-central1"


def consult_herbal_rag_corpus(query: str) -> str:
    """Search the Culpeper Herbal RAG corpus and return relevant passages for herbal remedies, plants, or ailments.

    Args:
        query: Search query string (e.g., 'cough', 'rosemary', 'digestive remedies').

    Returns:
        Formatted passages retrieved from the Culpeper Herbal corpus.
    """
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        corpora = list(rag.list_corpora())
        corpus_name = None
        for c in corpora:
            if getattr(c, "display_name", "") == "culpeper-herbal-corpus":
                corpus_name = c.name
                break

        if not corpus_name and corpora:
            corpus_name = corpora[0].name

        if not corpus_name:
            return "No RAG corpus found in Vertex AI."

        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
        contexts = getattr(resp.contexts, "contexts", [])
        passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
        return "\n\n---\n\n".join(passages) or "No relevant passages found in Culpeper Herbal corpus."
    except Exception as e:
        return f"Herbal RAG retrieval error: {str(e)}"
