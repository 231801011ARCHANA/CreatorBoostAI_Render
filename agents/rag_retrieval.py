from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from workflow.state import CreatorState


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
# RAG RETRIEVAL AGENT
# --------------------------------------------------

def rag_retrieval_agent(state: CreatorState):
    niche = state["niche"].lower()
    goal = state.get("goal", "").strip()

    query = f"""
    Find useful knowledge for creating content about {niche}.

    The user's goal is:
    {goal}

    Focus on knowledge that helps achieve this goal, including:
    - common beginner problems
    - useful content formats
    - important topics
    - practical recommendations
    - audience needs
    - content opportunities
    """

    print("\nRAG QUERY:")
    print(query)

    documents_with_scores = vectorstore.similarity_search_with_score(
        query,
        k=3,
        filter={"niche": niche}
    )

    rag_context = []

    for rank, (document, score) in enumerate(
        documents_with_scores,
        start=1
    ):

        rag_context.append({
            "document_id": document.metadata.get(
                "document_id"
            ),
            "niche": document.metadata.get(
                "niche"
            ),
            "source": document.metadata.get(
                "source"
            ),
            "rank": rank,
            "similarity_score": round(
                float(score),
                4
            ),
            "content": document.page_content
        })

    # --------------------------------------------------
    # PRINT RETRIEVAL RESULTS
    # --------------------------------------------------

    print("\n========== RAG RETRIEVAL ==========")

    print(
        f"Niche: {state['niche']}"
    )

    print(
        f"Documents retrieved: {len(rag_context)}"
    )

    for item in rag_context:

        print(
            f"\nRank: {item['rank']}"
        )

        print(
            f"Document ID: {item['document_id']}"
        )

        print(
            f"Source: {item['source']}"
        )

        print(
            f"Similarity score: "
            f"{item['similarity_score']}"
        )

        print(
            item["content"]
        )

    print("===================================")

    # --------------------------------------------------
    # RETURN RAG CONTEXT
    # --------------------------------------------------

    return {
        "rag_context": rag_context
    }