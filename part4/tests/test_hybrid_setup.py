#!/usr/bin/env python3
"""
Test Hybrid Setup: PayPal LLM + Bedrock Embeddings
"""

import os
import json
import boto3
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("="*80)
print("HYBRID RAG SETUP TEST")
print("PayPal CosmosAI (LLM) + AWS Bedrock Titan (Embeddings)")
print("="*80)
print()

# Test 1: PayPal LLM
print("Test 1: PayPal CosmosAI LLM (gpt-4o)")
print("-" * 40)

try:
    llm_client = OpenAI(
        base_url=os.getenv('LLM_BASE_URL'),
        api_key=os.getenv('LLM_API_KEY')
    )

    response = llm_client.chat.completions.create(
        model=os.getenv('LLM_MODEL'),
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        max_tokens=50
    )

    print(f"[OK] LLM works!")
    print(f"    Model: {response.model}")
    print(f"    Response: {response.choices[0].message.content}")
    print(f"    Tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out")
    llm_works = True

except Exception as e:
    print(f"[FAILED] {e}")
    llm_works = False

print()

# Test 2: AWS Bedrock Titan Embeddings
print("Test 2: AWS Bedrock Titan Embeddings")
print("-" * 40)

try:
    bedrock_runtime = boto3.client(
        'bedrock-runtime',
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )

    embed_model = os.getenv('EMBED_MODEL')
    test_text = "What is your return policy?"

    request_body = {"inputText": test_text}

    response = bedrock_runtime.invoke_model(
        modelId=embed_model,
        body=json.dumps(request_body)
    )

    response_body = json.loads(response['body'].read())
    embedding = response_body['embedding']

    print(f"[OK] Embeddings work!")
    print(f"    Model: {embed_model}")
    print(f"    Dimensions: {len(embedding)}")
    print(f"    Sample values: {embedding[:5]}")
    print(f"    Range: [{min(embedding):.4f}, {max(embedding):.4f}]")
    embed_works = True

except Exception as e:
    print(f"[FAILED] {e}")
    embed_works = False

print()
print("="*80)

if llm_works and embed_works:
    print("SUCCESS! Hybrid setup working perfectly")
    print()
    print("RAG Stack Configuration:")
    print(f"  LLM: PayPal CosmosAI gpt-4o")
    print(f"  Embeddings: AWS Bedrock Titan v2 (1024 dimensions)")
    print(f"  Vector Store: FAISS (local) or S3 + Bedrock KB")
    print()
    print("Ready to build RAG application!")
else:
    print("FAILED! Check the errors above")
    if not llm_works:
        print("  - LLM: Check PayPal CosmosAI credentials and network access")
    if not embed_works:
        print("  - Embeddings: Check AWS credentials and Bedrock access")

print("="*80)
