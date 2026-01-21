# AWS Fargate Deployment Guide

Deploy the E-commerce RAG Chatbot to AWS using ECR and Fargate.

## Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed and running
- Your `.env` file with valid credentials (this gets baked into the image)

---

## Step 1: Push Docker Image to ECR

Run these commands from the project root:

```bash
# Set variables
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1

# Create ECR repository (first time only)
aws ecr create-repository --repository-name ecommerce-rag-chatbot --region $AWS_REGION

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push (includes .env file)
docker build -t ecommerce-rag-chatbot .
docker tag ecommerce-rag-chatbot:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ecommerce-rag-chatbot:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ecommerce-rag-chatbot:latest
```

---

## Step 2: Create ECS Cluster

1. Go to **ECS** > **Clusters** > **Create Cluster**
2. Enter cluster name: `ecommerce-rag-cluster`
3. Infrastructure: Select **AWS Fargate (serverless)**
4. Click **Create**

---

## Step 3: Create Task Definition

1. Go to **ECS** > **Task Definitions** > **Create new Task Definition**

2. **Task Definition Configuration:**
   - Family name: `ecommerce-rag-task`
   - Launch type: AWS Fargate
   - Operating system: Linux/X86_64
   - CPU: 0.5 vCPU
   - Memory: 1 GB
   - Task execution role: Create new or use `ecsTaskExecutionRole`

3. **Container Configuration:**
   - Name: `ecommerce-rag-app`
   - Image URI: `<account-id>.dkr.ecr.us-east-1.amazonaws.com/ecommerce-rag-chatbot:latest`
   - Container port: `8501`
   - Protocol: TCP

4. Click **Create**

> Note: No environment variables needed - they're included in the Docker image via `.env`

---

## Step 4: Create Service

1. Go to your cluster > **Services** tab > **Create**

2. **Environment:**
   - Compute options: Launch type
   - Launch type: FARGATE

3. **Deployment Configuration:**
   - Application type: Service
   - Task definition family: `ecommerce-rag-task`
   - Service name: `ecommerce-rag-service`
   - Desired tasks: 1

4. **Networking:**
   - VPC: Select your default VPC
   - Subnets: Select public subnets
   - Security group: Create new
     - Inbound rule: Custom TCP, Port 8501, Source 0.0.0.0/0
   - Public IP: Turned ON

5. Click **Create**

---

## Step 5: Access Your Application

1. Wait for service to reach "Running" state (check Tasks tab)
2. Click on the running task
3. Find the **Public IP** in the Configuration section
4. Open in browser: `http://<public-ip>:8501`

---

## Updating the Application

After making code changes:

```bash
# Rebuild and push
docker build -t ecommerce-rag-chatbot .
docker tag ecommerce-rag-chatbot:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ecommerce-rag-chatbot:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/ecommerce-rag-chatbot:latest

# Force new deployment
aws ecs update-service \
    --cluster ecommerce-rag-cluster \
    --service ecommerce-rag-service \
    --force-new-deployment \
    --region us-east-1
```

---

## Viewing Logs

```bash
aws logs tail /ecs/ecommerce-rag-task --follow --region us-east-1
```

Or view in AWS Console: **CloudWatch** > **Log groups** > `/ecs/ecommerce-rag-task`

---

## Cleanup

To delete all resources:

1. Delete the ECS Service (set desired count to 0 first)
2. Delete the ECS Cluster
3. Delete the ECR Repository
4. Delete CloudWatch Log Group

---

## Troubleshooting

**Task fails to start:**
- Check CloudWatch logs for error messages
- Verify `.env` file was included in the Docker build

**Cannot access application:**
- Verify security group allows inbound port 8501
- Check that Public IP is assigned
- Ensure task is in "Running" state

**Container health check fails:**
- Application may need more startup time
- Check if Streamlit is running correctly in logs
