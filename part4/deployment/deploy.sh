#!/bin/bash

# =============================================================================
# E-commerce RAG Chatbot - AWS Deployment Script
# Deploys Streamlit app to ECR + Fargate
# =============================================================================

set -e  # Exit on error

# Configuration - MODIFY THESE
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
ECR_REPO_NAME="ecommerce-rag-chatbot"
ECS_CLUSTER_NAME="ecommerce-rag-cluster"
ECS_SERVICE_NAME="ecommerce-rag-service"
ECS_TASK_FAMILY="ecommerce-rag-task"
CONTAINER_NAME="ecommerce-rag-app"
CONTAINER_PORT=8501

# Derived values
ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
IMAGE_TAG="latest"

echo "=============================================="
echo "E-commerce RAG Chatbot - AWS Deployment"
echo "=============================================="
echo ""
echo "Configuration:"
echo "  AWS Region: ${AWS_REGION}"
echo "  Account ID: ${AWS_ACCOUNT_ID}"
echo "  ECR Repo: ${ECR_REPO_NAME}"
echo "  ECS Cluster: ${ECS_CLUSTER_NAME}"
echo ""

# -----------------------------------------------------------------------------
# Step 1: Create ECR Repository (if not exists)
# -----------------------------------------------------------------------------
echo "[Step 1/6] Creating ECR Repository..."

aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${AWS_REGION} 2>/dev/null || \
    aws ecr create-repository \
        --repository-name ${ECR_REPO_NAME} \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true

echo "[OK] ECR Repository ready: ${ECR_REPO_URI}"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Build Docker Image
# -----------------------------------------------------------------------------
echo "[Step 2/6] Building Docker Image..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Build the image
docker build -t ${ECR_REPO_NAME}:${IMAGE_TAG} .

echo "[OK] Docker image built: ${ECR_REPO_NAME}:${IMAGE_TAG}"
echo ""

# -----------------------------------------------------------------------------
# Step 3: Push to ECR
# -----------------------------------------------------------------------------
echo "[Step 3/6] Pushing to ECR..."

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Tag and push
docker tag ${ECR_REPO_NAME}:${IMAGE_TAG} ${ECR_REPO_URI}:${IMAGE_TAG}
docker push ${ECR_REPO_URI}:${IMAGE_TAG}

echo "[OK] Image pushed to ECR: ${ECR_REPO_URI}:${IMAGE_TAG}"
echo ""

# -----------------------------------------------------------------------------
# Step 4: Create ECS Cluster (if not exists)
# -----------------------------------------------------------------------------
echo "[Step 4/6] Creating ECS Cluster..."

aws ecs describe-clusters --clusters ${ECS_CLUSTER_NAME} --region ${AWS_REGION} --query 'clusters[0].status' --output text 2>/dev/null | grep -q "ACTIVE" || \
    aws ecs create-cluster \
        --cluster-name ${ECS_CLUSTER_NAME} \
        --capacity-providers FARGATE FARGATE_SPOT \
        --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
        --region ${AWS_REGION}

echo "[OK] ECS Cluster ready: ${ECS_CLUSTER_NAME}"
echo ""

# -----------------------------------------------------------------------------
# Step 5: Register Task Definition
# -----------------------------------------------------------------------------
echo "[Step 5/6] Registering Task Definition..."

# Create task definition JSON
cat > /tmp/task-definition.json << EOF
{
    "family": "${ECS_TASK_FAMILY}",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024",
    "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskExecutionRole",
    "taskRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/ecsTaskRole",
    "containerDefinitions": [
        {
            "name": "${CONTAINER_NAME}",
            "image": "${ECR_REPO_URI}:${IMAGE_TAG}",
            "essential": true,
            "portMappings": [
                {
                    "containerPort": ${CONTAINER_PORT},
                    "hostPort": ${CONTAINER_PORT},
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {"name": "AWS_DEFAULT_REGION", "value": "${AWS_REGION}"}
            ],
            "secrets": [
                {"name": "KNOWLEDGE_BASE_ID", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/ecommerce-rag/KNOWLEDGE_BASE_ID"},
                {"name": "LLM_BASE_URL", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/ecommerce-rag/LLM_BASE_URL"},
                {"name": "LLM_API_KEY", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/ecommerce-rag/LLM_API_KEY"},
                {"name": "LLM_MODEL", "valueFrom": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/ecommerce-rag/LLM_MODEL"}
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/${ECS_TASK_FAMILY}",
                    "awslogs-region": "${AWS_REGION}",
                    "awslogs-stream-prefix": "ecs",
                    "awslogs-create-group": "true"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:${CONTAINER_PORT}/_stcore/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ]
}
EOF

aws ecs register-task-definition \
    --cli-input-json file:///tmp/task-definition.json \
    --region ${AWS_REGION}

echo "[OK] Task definition registered: ${ECS_TASK_FAMILY}"
echo ""

# -----------------------------------------------------------------------------
# Step 6: Create/Update Service
# -----------------------------------------------------------------------------
echo "[Step 6/6] Creating/Updating ECS Service..."

# Check if service exists
SERVICE_EXISTS=$(aws ecs describe-services \
    --cluster ${ECS_CLUSTER_NAME} \
    --services ${ECS_SERVICE_NAME} \
    --region ${AWS_REGION} \
    --query 'services[0].status' \
    --output text 2>/dev/null || echo "NONE")

if [ "$SERVICE_EXISTS" == "ACTIVE" ]; then
    echo "Service exists, updating..."
    aws ecs update-service \
        --cluster ${ECS_CLUSTER_NAME} \
        --service ${ECS_SERVICE_NAME} \
        --task-definition ${ECS_TASK_FAMILY} \
        --force-new-deployment \
        --region ${AWS_REGION}
else
    echo "Creating new service..."
    echo ""
    echo "[WARNING] You need to provide subnet and security group IDs"
    echo "Run the following command with your VPC details:"
    echo ""
    echo "aws ecs create-service \\"
    echo "    --cluster ${ECS_CLUSTER_NAME} \\"
    echo "    --service-name ${ECS_SERVICE_NAME} \\"
    echo "    --task-definition ${ECS_TASK_FAMILY} \\"
    echo "    --desired-count 1 \\"
    echo "    --launch-type FARGATE \\"
    echo "    --network-configuration 'awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}' \\"
    echo "    --region ${AWS_REGION}"
    echo ""
fi

echo ""
echo "=============================================="
echo "DEPLOYMENT COMPLETE"
echo "=============================================="
echo ""
echo "ECR Image: ${ECR_REPO_URI}:${IMAGE_TAG}"
echo "ECS Cluster: ${ECS_CLUSTER_NAME}"
echo "Task Definition: ${ECS_TASK_FAMILY}"
echo ""
echo "Next Steps:"
echo "1. Ensure IAM roles exist (run setup-iam.sh)"
echo "2. Store secrets in SSM Parameter Store (run setup-ssm-params.sh)"
echo "3. Create/update the ECS service with correct VPC settings"
echo "4. Access the app via the task's public IP or ALB"
echo ""
