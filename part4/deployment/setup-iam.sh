#!/bin/bash

# =============================================================================
# Setup IAM Roles for ECS Fargate Deployment
# =============================================================================

set -e

AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"

echo "=============================================="
echo "Setting up IAM Roles for ECS Fargate"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# Step 1: Create ECS Task Execution Role
# -----------------------------------------------------------------------------
echo "[Step 1/3] Creating ECS Task Execution Role..."

# Trust policy for ECS
cat > /tmp/ecs-trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Check if role exists
if aws iam get-role --role-name ecsTaskExecutionRole 2>/dev/null; then
    echo "[OK] ecsTaskExecutionRole already exists"
else
    aws iam create-role \
        --role-name ecsTaskExecutionRole \
        --assume-role-policy-document file:///tmp/ecs-trust-policy.json

    # Attach managed policy
    aws iam attach-role-policy \
        --role-name ecsTaskExecutionRole \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

    echo "[OK] Created ecsTaskExecutionRole"
fi

# Add SSM read permissions for secrets
cat > /tmp/ssm-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameters",
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/ecommerce-rag/*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-name SSMParameterAccess \
    --policy-document file:///tmp/ssm-policy.json

echo "[OK] Added SSM Parameter access to ecsTaskExecutionRole"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Create ECS Task Role (for application permissions)
# -----------------------------------------------------------------------------
echo "[Step 2/3] Creating ECS Task Role..."

if aws iam get-role --role-name ecsTaskRole 2>/dev/null; then
    echo "[OK] ecsTaskRole already exists"
else
    aws iam create-role \
        --role-name ecsTaskRole \
        --assume-role-policy-document file:///tmp/ecs-trust-policy.json

    echo "[OK] Created ecsTaskRole"
fi

# Add Bedrock and S3 permissions
cat > /tmp/task-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:Retrieve",
                "bedrock:RetrieveAndGenerate"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:Retrieve"
            ],
            "Resource": "arn:aws:bedrock:${AWS_REGION}:${AWS_ACCOUNT_ID}:knowledge-base/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::ecom-rag-bucket",
                "arn:aws:s3:::ecom-rag-bucket/*"
            ]
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name ecsTaskRole \
    --policy-name BedrockS3Access \
    --policy-document file:///tmp/task-policy.json

echo "[OK] Added Bedrock and S3 access to ecsTaskRole"
echo ""

# -----------------------------------------------------------------------------
# Step 3: Add CloudWatch Logs permissions
# -----------------------------------------------------------------------------
echo "[Step 3/3] Adding CloudWatch Logs permissions..."

cat > /tmp/logs-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:log-group:/ecs/*"
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-name CloudWatchLogsAccess \
    --policy-document file:///tmp/logs-policy.json

echo "[OK] Added CloudWatch Logs permissions"
echo ""

echo "=============================================="
echo "IAM SETUP COMPLETE"
echo "=============================================="
echo ""
echo "Created/Updated Roles:"
echo "  - ecsTaskExecutionRole (for ECS to pull images, get secrets)"
echo "  - ecsTaskRole (for app to access Bedrock, S3)"
echo ""
echo "Next: Run setup-ssm-params.sh to store secrets"
echo ""
