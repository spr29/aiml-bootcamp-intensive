#!/bin/bash

# =============================================================================
# Setup VPC and Security Group for ECS Fargate
# Uses default VPC or creates minimal networking
# =============================================================================

set -e

AWS_REGION="${AWS_REGION:-us-east-1}"

echo "=============================================="
echo "Setting up VPC and Security Group for Fargate"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# Step 1: Get Default VPC
# -----------------------------------------------------------------------------
echo "[Step 1/3] Getting Default VPC..."

VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=is-default,Values=true" \
    --query 'Vpcs[0].VpcId' \
    --output text \
    --region ${AWS_REGION})

if [ "$VPC_ID" == "None" ] || [ -z "$VPC_ID" ]; then
    echo "[ERROR] No default VPC found. Please create one or specify a VPC ID."
    exit 1
fi

echo "[OK] Using VPC: ${VPC_ID}"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Get Public Subnets
# -----------------------------------------------------------------------------
echo "[Step 2/3] Getting Public Subnets..."

SUBNETS=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=${VPC_ID}" \
    --query 'Subnets[?MapPublicIpOnLaunch==`true`].SubnetId' \
    --output text \
    --region ${AWS_REGION})

if [ -z "$SUBNETS" ]; then
    # If no public subnets, get any subnets
    SUBNETS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=${VPC_ID}" \
        --query 'Subnets[*].SubnetId' \
        --output text \
        --region ${AWS_REGION})
fi

# Convert to comma-separated list
SUBNET_LIST=$(echo $SUBNETS | tr '\t' ',' | tr ' ' ',')

echo "[OK] Found subnets: ${SUBNET_LIST}"
echo ""

# -----------------------------------------------------------------------------
# Step 3: Create Security Group
# -----------------------------------------------------------------------------
echo "[Step 3/3] Creating Security Group..."

SG_NAME="ecommerce-rag-sg"

# Check if security group exists
SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${SG_NAME}" "Name=vpc-id,Values=${VPC_ID}" \
    --query 'SecurityGroups[0].GroupId' \
    --output text \
    --region ${AWS_REGION} 2>/dev/null || echo "None")

if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
    # Create new security group
    SG_ID=$(aws ec2 create-security-group \
        --group-name ${SG_NAME} \
        --description "Security group for E-commerce RAG Chatbot" \
        --vpc-id ${VPC_ID} \
        --query 'GroupId' \
        --output text \
        --region ${AWS_REGION})

    echo "[OK] Created security group: ${SG_ID}"

    # Add inbound rule for Streamlit (port 8501)
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 8501 \
        --cidr 0.0.0.0/0 \
        --region ${AWS_REGION}

    echo "[OK] Added inbound rule for port 8501"

    # Add inbound rule for HTTP (port 80) - for ALB
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region ${AWS_REGION}

    echo "[OK] Added inbound rule for port 80"
else
    echo "[OK] Security group already exists: ${SG_ID}"
fi

echo ""
echo "=============================================="
echo "VPC SETUP COMPLETE"
echo "=============================================="
echo ""
echo "Configuration:"
echo "  VPC ID: ${VPC_ID}"
echo "  Subnets: ${SUBNET_LIST}"
echo "  Security Group: ${SG_ID}"
echo ""
echo "Use these values to create your ECS service:"
echo ""
echo "aws ecs create-service \\"
echo "    --cluster ecommerce-rag-cluster \\"
echo "    --service-name ecommerce-rag-service \\"
echo "    --task-definition ecommerce-rag-task \\"
echo "    --desired-count 1 \\"
echo "    --launch-type FARGATE \\"
echo "    --network-configuration 'awsvpcConfiguration={subnets=[${SUBNET_LIST}],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}' \\"
echo "    --region ${AWS_REGION}"
echo ""

# Export for use in other scripts
echo "# Add these to your environment or use in deploy.sh"
echo "export VPC_ID=${VPC_ID}"
echo "export SUBNET_IDS=${SUBNET_LIST}"
echo "export SECURITY_GROUP_ID=${SG_ID}"
echo ""
