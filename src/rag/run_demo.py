from src.rag.pipeline import RAGPipeline

rag = RAGPipeline()

while True:
    q = input("\nSoru: ")
    if q.lower() in ["exit", "quit"]:
        break

    answer = rag.answer(q)
    print("\n--- CEVAP ---")
    print(answer)
    print("-------------")
