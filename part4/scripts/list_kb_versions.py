#!/usr/bin/env python3
"""
List all Knowledge Base versions in S3

Usage: python list_kb_versions.py
"""

import os
import json
import boto3
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BUCKET_NAME = "ecom-rag-bucket"
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

# Initialize S3 client
s3_client = boto3.client('s3', region_name=AWS_REGION)

print("="*80)
print("KNOWLEDGE BASE VERSIONS IN S3")
print("="*80)
print()
print(f"Bucket: {BUCKET_NAME}")
print(f"Region: {AWS_REGION}")
print()

try:
    # List all knowledge base folders (top-level folders starting with 'knowledge-base-')
    response = s3_client.list_objects_v2(
        Bucket=BUCKET_NAME,
        Delimiter='/'
    )

    if 'CommonPrefixes' not in response:
        print("No knowledge base folders found in S3")
        exit(0)

    # Filter for knowledge base folders
    kb_folders = [p for p in response['CommonPrefixes']
                  if p['Prefix'].startswith('knowledge-base-')]

    if not kb_folders:
        print("No knowledge base folders found in S3")
        exit(0)

    versions = []
    for prefix in kb_folders:
        folder_name = prefix['Prefix'].rstrip('/')

        # Get metadata for this version
        try:
            manifest_key = f"{prefix['Prefix']}manifest.json"
            manifest_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=manifest_key)
            manifest = json.loads(manifest_obj['Body'].read())

            # Get file count
            files_response = s3_client.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=prefix['Prefix']
            )
            file_count = files_response.get('KeyCount', 0)

            versions.append({
                'folder': folder_name,
                's3_path': f"s3://{BUCKET_NAME}/{folder_name}/",
                'created': manifest.get('created_at', 'Unknown'),
                'total_documents': manifest.get('total_documents', file_count - 1),  # Exclude manifest
                'has_manifest': True
            })
        except:
            # No manifest, just count files
            files_response = s3_client.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=prefix['Prefix']
            )
            file_count = files_response.get('KeyCount', 0)

            versions.append({
                'folder': folder_name,
                's3_path': f"s3://{BUCKET_NAME}/{folder_name}/",
                'created': 'Unknown',
                'total_documents': file_count,
                'has_manifest': False
            })

    if not versions:
        print("No knowledge base versions found")
        exit(0)

    # Sort by folder name (timestamp-based)
    versions.sort(key=lambda x: x['folder'])

    print(f"Found {len(versions)} knowledge base folder(s):")
    print("="*80)
    print()

    for idx, v in enumerate(versions, 1):
        print(f"Folder {idx}: {v['folder']}")
        print("-"*80)
        print(f"  S3 Location: {v['s3_path']}")
        print(f"  Documents: {v['total_documents']}")
        print(f"  Created: {v['created']}")
        print(f"  Has Manifest: {'Yes' if v['has_manifest'] else 'No'}")
        print()

    # Show latest folder
    latest = versions[-1]
    print("="*80)
    print(f"LATEST FOLDER: {latest['folder']}")
    print(f"  {latest['s3_path']}")
    print("="*80)
    print()
    print("Use this S3 URI when creating your Bedrock Knowledge Base")

except Exception as e:
    print(f"[FAILED] Error listing versions: {e}")
    exit(1)
