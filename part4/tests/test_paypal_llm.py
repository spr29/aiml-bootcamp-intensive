#!/usr/bin/env python3
"""
Test PayPal CosmosAI LLM endpoint connectivity
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get PayPal LLM credentials
base_url = os.getenv('LLM_BASE_URL')
api_key = os.getenv('LLM_API_KEY')
model = os.getenv('LLM_MODEL')

print("="*80)
print("PAYPAL COSMOSAI LLM CONNECTIVITY TEST")
print("="*80)
print()

print(f"Base URL: {base_url}")
print(f"Model: {model}")
print(f"API Key: {api_key[:20]}..." if api_key else "API Key: NOT SET")
print()

# Test 1: LLM Generation
print("Test 1: LLM Text Generation")
print("-" * 40)

try:
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Say 'Hello from PayPal CosmosAI' in one sentence."
            }
        ],
        max_tokens=100,
        temperature=0.1
    )

    print("[OK] LLM works!")
    print(f"    Response: {response.choices[0].message.content}")
    print(f"    Model used: {response.model}")
    print(f"    Tokens - Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens}")

    llm_works = True

except Exception as e:
    print(f"[FAILED] {e}")
    llm_works = False

print()

# Test 2: Embeddings
print("Test 2: Embeddings")
print("-" * 40)

try:
    embed_model = os.getenv('EMBED_MODEL', 'text-embedding-3-large')

    response = client.embeddings.create(
        model=embed_model,
        input="What is your return policy?"
    )

    embedding = response.data[0].embedding

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
    print("SUCCESS! Both LLM and Embeddings working")
    print()
    print("Configuration for notebooks:")
    print(f"  LLM Model: {model}")
    print(f"  Embedding Model: {embed_model}")
    print(f"  Base URL: {base_url}")
elif llm_works:
    print("PARTIAL SUCCESS! LLM works but embeddings failed")
    print("You can still use LLM for generation, may need different endpoint for embeddings")
else:
    print("FAILED! Could not connect to PayPal CosmosAI endpoint")
    print("Check your credentials and network access")

print("="*80)
