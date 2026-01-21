#!/usr/bin/env python3
"""
Upload Knowledge Base to S3 for Bedrock Knowledge Base
"""

import os
import json
import boto3
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

print("="*80)
print("UPLOAD KNOWLEDGE BASE TO S3 FOR BEDROCK")
print("="*80)
print()

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
)

# Get bucket name from user
print("What is your S3 bucket name?")
print("(The bucket should already exist)")
bucket_name = input("Bucket name: ").strip()

print()
print(f"Using bucket: {bucket_name}")
print()

# Check if bucket exists
try:
    s3_client.head_bucket(Bucket=bucket_name)
    print(f"[OK] Bucket '{bucket_name}' exists and is accessible")
except Exception as e:
    print(f"[FAILED] Cannot access bucket: {e}")
    exit(1)

print()

# Create folder structure for Bedrock Knowledge Base
kb_prefix = "knowledge-base/"

# Load the chunked data
chunks_file = "data/knowledge_base_chunks.json"
print(f"Loading chunks from: {chunks_file}")

with open(chunks_file, 'r') as f:
    chunks = json.load(f)

print(f"[OK] Loaded {len(chunks)} chunks")
print()

# Bedrock Knowledge Base expects documents in specific formats
# We'll create individual text files for each chunk
# and also create metadata files

print("Preparing files for upload...")
print()

# Create temporary directory for formatted files
temp_dir = Path("temp_kb_upload")
temp_dir.mkdir(exist_ok=True)

# Create subdirectories for different sources
(temp_dir / "policies").mkdir(exist_ok=True)
(temp_dir / "faqs").mkdir(exist_ok=True)

files_created = []

# Process policy chunks
policy_chunks = [c for c in chunks if c['source'] != 'faq']
for chunk in policy_chunks:
    filename = f"{chunk['chunk_id']}.txt"
    filepath = temp_dir / "policies" / filename

    with open(filepath, 'w') as f:
        f.write(chunk['text'])

    files_created.append(('policies', filename))

# Process FAQ chunks
faq_chunks = [c for c in chunks if c['source'] == 'faq']
for chunk in faq_chunks:
    filename = f"{chunk['chunk_id']}.txt"
    filepath = temp_dir / "faqs" / filename

    with open(filepath, 'w') as f:
        f.write(chunk['text'])

    files_created.append(('faqs', filename))

print(f"[OK] Created {len(files_created)} text files")
print(f"  Policies: {len(policy_chunks)} files")
print(f"  FAQs: {len(faq_chunks)} files")
print()

# Upload to S3
print("Uploading to S3...")
print("-" * 80)

uploaded = 0
for subfolder, filename in files_created:
    local_path = temp_dir / subfolder / filename
    s3_key = f"{kb_prefix}{subfolder}/{filename}"

    try:
        s3_client.upload_file(
            str(local_path),
            bucket_name,
            s3_key,
            ExtraArgs={'ContentType': 'text/plain'}
        )
        uploaded += 1
        if uploaded % 10 == 0:
            print(f"  Uploaded {uploaded}/{len(files_created)} files...")
    except Exception as e:
        print(f"[FAILED] Could not upload {filename}: {e}")

print(f"[OK] Uploaded {uploaded}/{len(files_created)} files to S3")
print()

# Create a manifest file with metadata
manifest = {
    "knowledge_base_name": "ecommerce-kb",
    "total_documents": len(files_created),
    "sources": {
        "policies": len(policy_chunks),
        "faqs": len(faq_chunks)
    },
    "s3_location": f"s3://{bucket_name}/{kb_prefix}",
    "created_at": "2026-01-17"
}

manifest_path = temp_dir / "manifest.json"
with open(manifest_path, 'w') as f:
    json.dump(manifest, indent=2, fp=f)

s3_client.upload_file(
    str(manifest_path),
    bucket_name,
    f"{kb_prefix}manifest.json",
    ExtraArgs={'ContentType': 'application/json'}
)

print(f"[OK] Uploaded manifest file")
print()

# Cleanup temporary files
import shutil
shutil.rmtree(temp_dir)
print("[OK] Cleaned up temporary files")
print()

print("="*80)
print("SUCCESS! Knowledge base uploaded to S3")
print()
print("S3 Location:")
print(f"  s3://{bucket_name}/{kb_prefix}")
print()
print("File Structure:")
print(f"  s3://{bucket_name}/{kb_prefix}policies/  ({len(policy_chunks)} files)")
print(f"  s3://{bucket_name}/{kb_prefix}faqs/      ({len(faq_chunks)} files)")
print()
print("Next Steps:")
print("1. Go to AWS Bedrock Console: https://console.aws.amazon.com/bedrock/")
print("2. Navigate to 'Knowledge bases' in the left sidebar")
print("3. Click 'Create knowledge base'")
print("4. Configure:")
print(f"   - Name: ecommerce-knowledge-base")
print(f"   - Data source: S3")
print(f"   - S3 URI: s3://{bucket_name}/{kb_prefix}")
print(f"   - Embedding model: {os.getenv('EMBED_MODEL', 'amazon.titan-embed-text-v2:0')}")
print(f"   - Vector store: Create new (or use existing)")
print("5. Click 'Create' and wait for ingestion to complete")
print()
print("The Knowledge Base ID will be needed for Notebook 02")
print("="*80)
