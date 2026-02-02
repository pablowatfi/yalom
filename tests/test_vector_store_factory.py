"""
Test script for vector store factory and adapters.
"""
import os
import sys

# Set test environment
os.environ['VECTOR_STORE'] = 'qdrant'
os.environ['QDRANT_URL'] = 'http://localhost:6333'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.vectorization.factory import VectorStoreFactory
from src.vectorization.simple_embeddings import SimpleSentenceTransformerEmbeddings


def test_vector_store():
    """Test vector store factory and basic operations."""

    print("=" * 60)
    print("Testing Vector Store Factory")
    print("=" * 60)

    # Create vector store (from environment)
    print(f"\n1. Creating vector store from environment...")
    print(f"   VECTOR_STORE={os.getenv('VECTOR_STORE')}")

    try:
        store = VectorStoreFactory.create()
        print(f"   ✅ Created: {store.provider_name}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Check if collection exists
    print(f"\n2. Checking collection...")
    try:
        exists = store.collection_exists()
        print(f"   Collection exists: {exists}")

        if not exists:
            print(f"   Creating collection...")
            store.create_collection(dimension=384)
            print(f"   ✅ Collection created")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # Get stats
    print(f"\n3. Getting statistics...")
    try:
        stats = store.get_stats()
        print(f"   Provider: {stats.get('provider')}")
        print(f"   Vectors: {stats.get('vectors_count', 0)}")
    except Exception as e:
        print(f"   ⚠️  Warning: {e}")

    # Test embeddings + search
    print(f"\n4. Testing search...")
    try:
        embeddings = SimpleSentenceTransformerEmbeddings()
        query_vector = embeddings.embed_query("test query")
        print(f"   Query vector dimension: {len(query_vector)}")

        results = store.search(query_vector=query_vector, top_k=3)
        print(f"   Found {len(results)} results")

        if results:
            print(f"   Top result score: {results[0].score:.3f}")
    except Exception as e:
        print(f"   ⚠️  Warning: {e}")
        print(f"   (This is expected if no data is indexed yet)")

    print(f"\n" + "=" * 60)
    print("✅ Vector store test complete!")
    print("=" * 60)

    return True


if __name__ == '__main__':
    success = test_vector_store()
    sys.exit(0 if success else 1)
