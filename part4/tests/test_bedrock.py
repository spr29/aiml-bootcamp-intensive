#!/usr/bin/env python3
"""
Test Bedrock connectivity and find working Claude model
"""

import boto3
import json
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load environment variables
load_dotenv()

# Get AWS credentials
aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

print("="*80)
print("BEDROCK CONNECTIVITY TEST")
print("="*80)
print()

# Test 1: AWS Connection
print("Test 1: AWS Connection")
print("-" * 40)
try:
    sts = boto3.client('sts', region_name=aws_region)
    identity = sts.get_caller_identity()
    print(f"[OK] Connected to AWS")
    print(f"    Account: {identity['Account']}")
    print(f"    User ARN: {identity['Arn']}")
except Exception as e:
    print(f"[FAILED] {e}")
    exit(1)

print()

# Test 2: List Available Claude Models
print("Test 2: List Available Claude Models")
print("-" * 40)
try:
    bedrock = boto3.client('bedrock', region_name=aws_region)
    response = bedrock.list_foundation_models()

    claude_models = []
    for model in response['modelSummaries']:
        if 'claude' in model['modelId'].lower():
            claude_models.append(model['modelId'])

    print(f"[OK] Found {len(claude_models)} Claude models")
    for model_id in sorted(claude_models):
        print(f"    - {model_id}")
except Exception as e:
    print(f"[FAILED] {e}")
    exit(1)

print()

# Test 3: Try Different Claude Models
print("Test 3: Testing Claude Models")
print("-" * 40)

# Models to test (in order of preference)
models_to_test = [
    'anthropic.claude-3-5-sonnet-20240620-v1:0',  # Claude 3.5 Sonnet v1
    'anthropic.claude-3-haiku-20240307-v1:0',      # Claude 3 Haiku
    'anthropic.claude-3-sonnet-20240229-v1:0',    # Claude 3 Sonnet
]

bedrock_runtime = boto3.client('bedrock-runtime', region_name=aws_region)

working_model = None

for model_id in models_to_test:
    print(f"\nTesting: {model_id}")

    try:
        # Prepare request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'Hello from Bedrock' in one sentence."
                }
            ],
            "temperature": 0.1
        }

        # Invoke model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )

        # Parse response
        response_body = json.loads(response['body'].read())
        response_text = response_body['content'][0]['text']

        print(f"[OK] Model works!")
        print(f"    Response: {response_text}")
        print(f"    Input tokens: {response_body.get('usage', {}).get('input_tokens', 'N/A')}")
        print(f"    Output tokens: {response_body.get('usage', {}).get('output_tokens', 'N/A')}")

        working_model = model_id
        break  # Found a working model, stop testing

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"[FAILED] {error_code}: {error_msg}")
    except Exception as e:
        print(f"[FAILED] {e}")

print()
print("="*80)

if working_model:
    print(f"SUCCESS! Working Claude model: {working_model}")
    print()
    print("Update your notebook to use this model:")
    print(f"    model_id = '{working_model}'")
else:
    print("FAILED! No working Claude models found.")
    print()
    print("Try requesting model access at:")
    print("https://console.aws.amazon.com/bedrock/home#/modelaccess")

print("="*80)
