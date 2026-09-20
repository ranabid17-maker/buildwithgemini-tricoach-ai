# Copyright 2026 Google LLC
# Create Serverless Vertex AI RAG Corpus
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr
import vertexai

PROJECT_ID = "qwiklabs-gcp-01-11b4cbda191e"
LOCATION = "us-central1"
GCS_PATH = "gs://simple-agent-media-11b4cbda191e/rag/culpeper_herbal.txt"

PARSING_PROMPT = (
    "Extract the individual useful facts, medicinal uses, and herbal remedies described in this text. "
    "Ignore and omit all metadata, Gutenberg license boilerplate, and page headers. "
    "Output clean, self-contained prose."
)

print(f"Initializing Vertex AI for project {PROJECT_ID} in {LOCATION}...")
vertexai.init(project=PROJECT_ID, location=LOCATION)

print("Updating RAG engine config to serverless mode...")
cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
rag.update_rag_engine_config(
    rag_engine_config=rag.RagEngineConfig(
        name=cfg,
        rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
    )
)

print("Creating RAG corpus with text-embedding-005...")
corpus = rag.create_corpus(
    display_name="culpeper-herbal-corpus",
    embedding_model_config=rag.EmbeddingModelConfig(
        publisher_model="publishers/google/models/text-embedding-005"
    ),
)
print(f"CREATED_CORPUS_NAME: {corpus.name}")

print(f"Importing and indexing {GCS_PATH}...")
resp = rag.import_files(
    corpus_name=corpus.name,
    paths=[GCS_PATH],
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
    ),
    llm_parser=rag.LlmParserConfig(
        model_name="gemini-3.6-flash",
        custom_parsing_prompt=PARSING_PROMPT,
    ),
)
print(f"IMPORTED_FILES_COUNT: {resp.imported_rag_files_count}")
