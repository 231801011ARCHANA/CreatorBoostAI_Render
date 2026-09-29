from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


# --------------------------------------------------
# LOAD EMBEDDINGS
# --------------------------------------------------

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# --------------------------------------------------
# LOAD VECTOR DATABASE
# --------------------------------------------------

vectorstore = Chroma(
    persist_directory="data/chroma",
    embedding_function=embeddings
)


# --------------------------------------------------
# TEST QUESTIONS
# --------------------------------------------------

test_cases = [
    {
        "niche": "gardening",
        "question": "What are common beginner gardening mistakes?"
    },
    {
        "niche": "fitness",
        "question": "What should beginners know about fitness?"
    },
    {
        "niche": "cooking",
        "question": "What are common cooking mistakes?"
    }
]


# --------------------------------------------------
# RUN RETRIEVAL TEST
# --------------------------------------------------

for test_case in test_cases:

    niche = test_case["niche"]
    question = test_case["question"]

    print("\n========================================")

    print("QUESTION:")
    print(question)

    print("\nNICHE:")
    print(niche)

    # --------------------------------------------------
    # RETRIEVE DOCUMENTS WITH SCORES
    # --------------------------------------------------

    documents_with_scores = (
        vectorstore.similarity_search_with_score(
            question,
            k=3,
            filter={"niche": niche}
        )
    )

    print("\nRETRIEVED DOCUMENTS:")

    if not documents_with_scores:

        print("No documents retrieved.")

    else:

        for rank, (document, score) in enumerate(
            documents_with_scores,
            start=1
        ):

            document_id = document.metadata.get(
                "document_id",
                "UNKNOWN"
            )

            source = document.metadata.get(
                "source",
                "UNKNOWN"
            )

            document_niche = document.metadata.get(
                "niche",
                "UNKNOWN"
            )

            print("\n--------------------")

            print(
                f"Rank: {rank}"
            )

            print(
                f"Document ID: {document_id}"
            )

            print(
                f"Niche: {document_niche}"
            )

            print(
                f"Source: {source}"
            )

            print(
                f"Score: {float(score):.4f}"
            )

            print("\nContent:")

            print(
                document.page_content
            )

    print("\n========================================")


print("\nRAG retrieval test completed.")