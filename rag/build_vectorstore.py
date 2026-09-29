from pathlib import Path

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


KNOWLEDGE_DIR = Path("knowledge")
VECTORSTORE_DIR = "data/chroma"

SUPPORTED_NICHES = [
    "fitness",
    "gardening",
    "cooking"
]


documents = []

# Keep a separate counter for each niche
niche_counters = {
    niche: 0
    for niche in SUPPORTED_NICHES
}


for file_path in sorted(KNOWLEDGE_DIR.glob("*.txt")):

    filename = file_path.stem.lower()

    # Determine which niche the file belongs to
    niche = None

    for supported_niche in SUPPORTED_NICHES:
        if filename.startswith(supported_niche + "_"):
            niche = supported_niche
            break

    if niche is None:
        print(
            f"Skipping unsupported file: {file_path.name}"
        )
        continue

    # Generate sequential document ID
    niche_counters[niche] += 1

    document_id = (
        f"{niche}_{niche_counters[niche]:03d}"
    )

    text = file_path.read_text(
        encoding="utf-8"
    ).strip()

    if not text:
        print(
            f"Skipping empty file: {file_path.name}"
        )
        continue

    document = Document(
        page_content=text,
        metadata={
            "niche": niche,
            "document_id": document_id,
            "source": file_path.name
        }
    )

    documents.append(document)


print("\n========== RAG DOCUMENTS ==========")

for document in documents:
    print(
        "Loaded:",
        document.metadata["document_id"],
        "| Niche:",
        document.metadata["niche"],
        "| Source:",
        document.metadata["source"]
    )

print("\nTotal documents:", len(documents))


print("\nLoading embedding model...")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


print("\nCreating vector database...")

vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory=VECTORSTORE_DIR,
    ids=[
        document.metadata["document_id"]
        for document in documents
    ]
)


print("\n========== RAG COMPLETE ==========")

print(
    "Vector database saved to:",
    VECTORSTORE_DIR
)

print("\nDocuments by niche:")

for niche in SUPPORTED_NICHES:

    count = niche_counters[niche]

    print(
        f"- {niche}: {count}"
    )

print("\n==================================")