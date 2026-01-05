"""Test Document RAG with Citations"""
import sys
sys.path.insert(0, '.')

from src.agent.document_rag import DocumentRAG, seed_sample_documents

def main():
    print("CHIEF Document RAG Test")
    print("=" * 40)
    
    # Create RAG instance (docs already indexed from previous run)
    rag = DocumentRAG()
    
    # List documents
    print("\n1. Indexed documents:")
    docs = rag.list_documents()
    for doc in docs:
        print(f"   - {doc['title']} ({doc['doc_type']})")
    
    # Test search
    print("\n2. Searching for 'overtime'...")
    results = rag.search("overtime compensation", top_k=3)
    for r in results:
        print(f"   [{r['rank']}] {r['title']} (score: {r['score']:.3f})")
        print(f"       {r['text'][:80]}...")
    
    # Test query with answer
    print("\n3. Asking: 'How is overtime distributed?'")
    response = rag.query_with_answer("How is overtime distributed according to the CBA?")
    print(f"\n   Answer: {response['answer']}")
    
    # Test another query
    print("\n4. Asking: 'What are the drone requirements?'")
    response2 = rag.query_with_answer("What certifications are needed for drone operations?")
    print(f"\n   Answer: {response2['answer']}")
    
    # Test CRR query
    print("\n5. Asking: 'How many home safety visits per month?'")
    response3 = rag.query_with_answer("How many home safety visits should be done per month?")
    print(f"\n   Answer: {response3['answer']}")
    
    print("\n✅ Document RAG test complete!")

if __name__ == "__main__":
    main()
