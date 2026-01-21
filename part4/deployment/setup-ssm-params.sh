#!/bin/bash

# =============================================================================
# Store Secrets in AWS SSM Parameter Store
# =============================================================================

set -e

AWS_REGION="${AWS_REGION:-us-east-1}"

echo "=============================================="
echo "Storing Secrets in SSM Parameter Store"
echo "=============================================="
echo ""

# Load from .env file if it exists
if [ -f "../.env" ]; then
    echo "Loading values from .env file..."
    source ../.env
fi

# Prompt for values if not set
if [ -z "$KNOWLEDGE_BASE_ID" ]; then
    read -p "Enter KNOWLEDGE_BASE_ID: " KNOWLEDGE_BASE_ID
fi

if [ -z "$LLM_BASE_URL" ]; then
    read -p "Enter LLM_BASE_URL: " LLM_BASE_URL
fi

if [ -z "$LLM_API_KEY" ]; then
    read -sp "Enter LLM_API_KEY: " LLM_API_KEY
    echo ""
fi

if [ -z "$LLM_MODEL" ]; then
    read -p "Enter LLM_MODEL [gpt-4o]: " LLM_MODEL
    LLM_MODEL="${LLM_MODEL:-gpt-4o}"
fi

echo ""
echo "Storing parameters..."

# Store KNOWLEDGE_BASE_ID
aws ssm put-parameter \
    --name "/ecommerce-rag/KNOWLEDGE_BASE_ID" \
    --value "${KNOWLEDGE_BASE_ID}" \
    --type "SecureString" \
    --overwrite \
    --region ${AWS_REGION}
echo "[OK] Stored KNOWLEDGE_BASE_ID"

# Store LLM_BASE_URL
aws ssm put-parameter \
    --name "/ecommerce-rag/LLM_BASE_URL" \
    --value "${LLM_BASE_URL}" \
    --type "SecureString" \
    --overwrite \
    --region ${AWS_REGION}
echo "[OK] Stored LLM_BASE_URL"

# Store LLM_API_KEY
aws ssm put-parameter \
    --name "/ecommerce-rag/LLM_API_KEY" \
    --value "${LLM_API_KEY}" \
    --type "SecureString" \
    --overwrite \
    --region ${AWS_REGION}
echo "[OK] Stored LLM_API_KEY"

# Store LLM_MODEL
aws ssm put-parameter \
    --name "/ecommerce-rag/LLM_MODEL" \
    --value "${LLM_MODEL}" \
    --type "String" \
    --overwrite \
    --region ${AWS_REGION}
echo "[OK] Stored LLM_MODEL"

echo ""
echo "=============================================="
echo "SSM Parameters stored successfully!"
echo "=============================================="
echo ""
echo "Parameters created:"
echo "  /ecommerce-rag/KNOWLEDGE_BASE_ID (SecureString)"
echo "  /ecommerce-rag/LLM_BASE_URL (SecureString)"
echo "  /ecommerce-rag/LLM_API_KEY (SecureString)"
echo "  /ecommerce-rag/LLM_MODEL (String)"
echo ""
