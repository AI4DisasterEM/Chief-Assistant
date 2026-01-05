import boto3
import json
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Get Qdrant credentials
secrets = boto3.client('secretsmanager', region_name='us-east-1')
response = secrets.get_secret_value(SecretId='chief/qdrant-credentials')
creds = json.loads(response['SecretString'])

client = QdrantClient(url=creds['url'], api_key=creds['api_key'])

# Create collections
collections = [
    ("conversations", 1536),  # For chat history
    ("notes", 1536),          # For note sessions
    ("documents", 1536),      # For RAG documents
    ("contacts", 1536),       # For relationship context
]

for name, size in collections:
    try:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=size, distance=Distance.COSINE)
        )
        print(f"✅ Created collection: {name}")
    except Exception as e:
        if "already exists" in str(e):
            print(f"⏭️  Collection exists: {name}")
        else:
            print(f"❌ Error with {name}: {e}")

print("\n🎉 Qdrant setup complete!")
