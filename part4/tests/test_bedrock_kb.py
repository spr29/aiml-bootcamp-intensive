#!/usr/bin/env python3
"""
Test Bedrock Knowledge Base Retrieval

Usage: python test_bedrock_kb.py
"""

import os
import json
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
KNOWLEDGE_BASE_ID = "XVIAYNVNB2"
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

print("="*80)
print("BEDROCK KNOWLEDGE BASE RETRIEVAL TEST")
print("="*80)
print()

# Initialize Bedrock Agent Runtime client
bedrock_agent = boto3.client(
    'bedrock-agent-runtime',
    region_name=AWS_REGION
)

print(f"Knowledge Base ID: {KNOWLEDGE_BASE_ID}")
print(f"Region: {AWS_REGION}")
print()

# Test queries
test_queries = [
    "What is your return policy?",
    "How long does shipping take?",
    "Do you offer free shipping?",
    "What items cannot be returned?",
    "How do I track my order?"
]

print("Testing Knowledge Base Retrieval...")
print("="*80)
print()

for i, query in enumerate(test_queries, 1):
    print(f"Query {i}: {query}")
    print("-" * 80)

    try:
        # Retrieve relevant documents
        response = bedrock_agent.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 3  # Get top 3 results
                }
            }
        )

        # Display results
        results = response.get('retrievalResults', [])

        if results:
            print(f"[OK] Found {len(results)} relevant chunks\n")

            for idx, result in enumerate(results, 1):
                content = result.get('content', {}).get('text', 'No content')
                score = result.get('score', 0)
                location = result.get('location', {})
                s3_location = location.get('s3Location', {})
                uri = s3_location.get('uri', 'Unknown')

                print(f"  Result {idx} (Score: {score:.4f}):")
                print(f"  Source: {uri}")
                print(f"  Content: {content[:150]}...")
                print()
        else:
            print("[WARNING] No results found")
            print()

    except Exception as e:
        print(f"[FAILED] Error: {e}")
        print()

    print()

print("="*80)
print("TEST COMPLETE")
print()
print("If you see results above, your Knowledge Base is working correctly!")
print()
print("Next steps:")
print("1. Review the retrieval results and scores")
print("2. Adjust numberOfResults if needed (default: 3)")
print("3. Ready to build Notebook 02 for baseline RAG implementation")
print("="*80)
