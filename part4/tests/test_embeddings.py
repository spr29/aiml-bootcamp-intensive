#!/usr/bin/env python3
"""
Test Bedrock embedding models
"""

import boto3
import json
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

print("="*80)
print("TESTING EMBEDDING MODELS")
print("="*80)
print()

bedrock = boto3.client('bedrock', region_name=aws_region)
response = bedrock.list_foundation_models()

# Find embedding models
embedding_models = []
for model in response['modelSummaries']:
    model_id = model['modelId']
    if 'embed' in model_id.lower():
        embedding_models.append(model_id)

print(f"Found {len(embedding_models)} embedding models:")
for model_id in sorted(embedding_models):
    print(f"  - {model_id}")

print()
print("Testing embedding models...")
print("-" * 80)

bedrock_runtime = boto3.client('bedrock-runtime', region_name=aws_region)

# Models to test (in order of preference)
models_to_test = [
    'amazon.titan-embed-text-v2:0',
    'amazon.titan-embed-text-v1',
    'cohere.embed-english-v3',
    'cohere.embed-multilingual-v3',
]

working_embed_model = None

for model_id in models_to_test:
    if model_id not in embedding_models:
        print(f"\nSkipping {model_id} (not in available models)")
        continue

    print(f"\nTesting: {model_id}")

    try:
        # Different request formats for different models
        if 'titan' in model_id.lower():
            request_body = {"inputText": "What is your return policy?"}
        elif 'cohere' in model_id.lower():
            request_body = {
                "texts": ["What is your return policy?"],
                "input_type": "search_query"
            }

        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())

        # Extract embedding based on model
        if 'titan' in model_id.lower():
            embedding = response_body['embedding']
        elif 'cohere' in model_id.lower():
            embedding = response_body['embeddings'][0]

        print(f"[OK] Model works!")
        print(f"    Dimensions: {len(embedding)}")
        print(f"    Sample values: {embedding[:5]}")
        print(f"    Range: [{min(embedding):.4f}, {max(embedding):.4f}]")

        working_embed_model = model_id
        break

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"[FAILED] {error_code}: {error_msg[:100]}")
    except Exception as e:
        print(f"[FAILED] {str(e)[:100]}")

print()
print("="*80)

if working_embed_model:
    print(f"SUCCESS! Working embedding model: {working_embed_model}")
    print()
    print("Update your notebook to use this model:")
    print(f"    embed_model_id = '{working_embed_model}'")
else:
    print("FAILED! No working embedding models found.")

print("="*80)
