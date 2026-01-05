"""Document RAG with Citations for CHIEF"""
import os
import json
import boto3
import hashlib
from datetime import datetime
from anthropic import Anthropic
import openai


def get_secret(secret_id):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_id)
    return json.loads(response['SecretString'])


def get_dynamodb():
    return boto3.resource('dynamodb', region_name='us-east-1')


def get_qdrant_client():
    from qdrant_client import QdrantClient
    creds = get_secret('chief/qdrant-credentials')
    return QdrantClient(url=creds['url'], api_key=creds['api_key'])


def get_embedding(text):
    """Get embedding using OpenAI"""
    creds = get_secret('chief/openai-api-key')
    client = openai.OpenAI(api_key=creds['api_key'])
    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


class DocumentRAG:
    def __init__(self, user_id="steven"):
        self.user_id = user_id
        self.dynamodb = get_dynamodb()
        self.docs_table = self.dynamodb.Table('chief_documents')
        self.qdrant = get_qdrant_client()
        self.collection = "documents"
    
    def chunk_text(self, text, chunk_size=500, overlap=50):
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def add_document(self, title, content, doc_type, source_file=None):
        """Add a document to the RAG system"""
        doc_id = hashlib.md5(f"{title}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
        
        chunks = self.chunk_text(content)
        
        self.docs_table.put_item(Item={
            'PK': f'DOC#{doc_id}',
            'SK': 'META',
            'GSI1PK': f'TYPE#{doc_type}',
            'GSI1SK': f'DATE#{datetime.utcnow().isoformat()[:10]}',
            'title': title,
            'doc_type': doc_type,
            'source_file': source_file,
            'chunk_count': len(chunks),
            'created_at': datetime.utcnow().isoformat(),
            'user_id': self.user_id
        })
        
        from qdrant_client.models import PointStruct
        
        points = []
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            point_id = int(hashlib.md5(f"{doc_id}{i}".encode()).hexdigest()[:8], 16)
            
            points.append(PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    'doc_id': doc_id,
                    'title': title,
                    'doc_type': doc_type,
                    'chunk_index': i,
                    'chunk_text': chunk,
                    'user_id': self.user_id
                }
            ))
        
        self.qdrant.upsert(collection_name=self.collection, points=points)
        
        return {
            'doc_id': doc_id,
            'title': title,
            'chunks': len(chunks),
            'status': 'indexed'
        }
    
    def search(self, query, doc_type=None, top_k=5):
        """Search documents and return relevant chunks with citations"""
        query_embedding = get_embedding(query)
        
        search_filter = None
        if doc_type:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            search_filter = Filter(
                must=[FieldCondition(key="doc_type", match=MatchValue(value=doc_type))]
            )
        
        # Use query instead of search for newer qdrant-client
        results = self.qdrant.query_points(
            collection_name=self.collection,
            query=query_embedding,
            query_filter=search_filter,
            limit=top_k
        )
        
        citations = []
        for i, result in enumerate(results.points):
            citations.append({
                'rank': i + 1,
                'score': result.score,
                'doc_id': result.payload['doc_id'],
                'title': result.payload['title'],
                'doc_type': result.payload['doc_type'],
                'chunk_index': result.payload['chunk_index'],
                'text': result.payload['chunk_text']
            })
        
        return citations
    
    def query_with_answer(self, question, doc_type=None):
        """Search docs and generate answer with citations"""
        citations = self.search(question, doc_type=doc_type, top_k=5)
        
        if not citations:
            return {
                'answer': "I couldn't find any relevant documents to answer that question.",
                'citations': []
            }
        
        context = "\n\n".join([
            f"[Source {i+1}: {c['title']}]\n{c['text']}"
            for i, c in enumerate(citations)
        ])
        
        creds = get_secret('chief/anthropic-api-key')
        client = Anthropic(api_key=creds['api_key'])
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system="""You are CHIEF, answering questions based on provided documents.
Always cite your sources using [Source N] format.
If the documents don't contain the answer, say so.
Be concise and direct.""",
            messages=[{
                "role": "user",
                "content": f"""Based on these documents, answer the question.

DOCUMENTS:
{context}

QUESTION: {question}

Provide a clear answer with citations."""
            }]
        )
        
        return {
            'answer': response.content[0].text,
            'citations': citations
        }
    
    def list_documents(self, doc_type=None):
        """List all indexed documents"""
        if doc_type:
            response = self.docs_table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :type',
                ExpressionAttributeValues={':type': f'TYPE#{doc_type}'}
            )
        else:
            response = self.docs_table.scan(
                FilterExpression='SK = :meta',
                ExpressionAttributeValues={':meta': 'META'}
            )
        
        return response.get('Items', [])


def seed_sample_documents():
    """Add sample documents for testing"""
    rag = DocumentRAG()
    
    cba_content = """
    COLLECTIVE BARGAINING AGREEMENT
    Between City of Sunrise and IAFF Local 2928
    
    ARTICLE 12 - OVERTIME
    Section 12.1 - Overtime shall be compensated at one and one-half times the regular rate.
    Section 12.2 - Overtime shall be distributed equitably among qualified employees.
    Section 12.3 - Employees may bank overtime as compensatory time up to 480 hours.
    Section 12.4 - Mandatory overtime shall be assigned by inverse seniority.
    
    ARTICLE 15 - LEAVE
    Section 15.1 - Annual leave accrual: 0-5 years: 8 hours/month, 5-10 years: 10 hours/month.
    Section 15.2 - Sick leave accrual: 8 hours per month for all employees.
    Section 15.3 - Kelly Day schedule shall provide one additional day off per 9-day cycle.
    """
    
    result1 = rag.add_document(
        title="IAFF Local 2928 CBA",
        content=cba_content,
        doc_type="cba"
    )
    print(f"Added: {result1['title']} ({result1['chunks']} chunks)")
    
    sop_content = """
    STANDARD OPERATING PROCEDURE: Community Risk Reduction
    SOP Number: CRR-001
    Effective Date: January 1, 2025
    
    PURPOSE: Establish procedures for community risk reduction activities.
    
    SCOPE: All personnel assigned to the CRR Division.
    
    PROCEDURE:
    1. Risk Assessment - Conduct annual community risk assessment using NFPA 1730 standards.
    2. Home Safety Visits - Complete minimum 50 home safety visits per month.
    3. Public Education - Deliver fire safety education to all elementary schools quarterly.
    4. Smoke Alarm Program - Install smoke alarms in at-risk residences upon request.
    5. Data Collection - Document all activities in the CRR database within 24 hours.
    
    REPORTING: Monthly reports due to Division Chief by the 5th of each month.
    """
    
    result2 = rag.add_document(
        title="CRR Division SOP",
        content=sop_content,
        doc_type="sop"
    )
    print(f"Added: {result2['title']} ({result2['chunks']} chunks)")
    
    policy_content = """
    CITY OF SUNRISE ADMINISTRATIVE POLICY
    Policy: AP-2024-15 - Drone Operations
    
    The City of Sunrise authorizes the use of unmanned aerial systems (drones) for:
    1. Search and rescue operations
    2. Fire scene documentation
    3. Damage assessment following disasters
    4. Training exercises
    
    All drone operators must maintain FAA Part 107 certification.
    Flight logs must be maintained and submitted monthly.
    Drones shall not be operated within 5 miles of FLL without FAA authorization.
    """
    
    result3 = rag.add_document(
        title="Drone Operations Policy",
        content=policy_content,
        doc_type="policy"
    )
    print(f"Added: {result3['title']} ({result3['chunks']} chunks)")
    
    print("\n✅ Sample documents indexed!")
    return rag
