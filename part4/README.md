# E-commerce RAG Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot for e-commerce customer support, built with AWS Bedrock Knowledge Base and OpenAI-compatible LLMs.

## Overview

This project demonstrates a complete RAG pipeline for e-commerce customer service, including:

- Vector-based semantic search using Amazon Bedrock
- Hybrid retrieval combining vector search and BM25
- Conversational AI with context memory
- Source attribution and citations
- Streamlit web interface
- Docker deployment to AWS ECS Fargate

## Features

- Multiple retrieval strategies (Vector, BM25, Hybrid)
- Conversational memory for multi-turn dialogues
- Real-time answers from policy documents and FAQ
- Source citations for transparency
- Scalable cloud deployment on AWS

## Project Structure

```
ecommerce-chatbot/
├── notebooks/
│   ├── 00_setup_and_connections.ipynb
│   ├── 01_data_exploration_chunking.ipynb
│   ├── 02_bedrock_knowledge_base.ipynb
│   ├── 03_baseline_rag.ipynb
│   └── 04_deployment_to_aws.ipynb
├── src/
│   └── rag_engine.py
├── data/
│   ├── ecommerce_faq.csv
│   ├── knowledge_base/
│   └── knowledge_base_chunks.json
├── app.py
├── Dockerfile
├── requirements-app.txt
└── .env
```

## Prerequisites

- Python 3.9 or higher
- AWS Account with:
  - Access to Amazon Bedrock (Titan Embeddings V2)
  - S3 bucket for knowledge base storage
  - IAM permissions for Bedrock and S3
- OpenAI-compatible LLM endpoint (or OpenAI API key)
- Docker (for deployment)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ecommerce-chatbot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements-app.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# AWS Bedrock Knowledge Base
KNOWLEDGE_BASE_ID=your_kb_id

# LLM Configuration
LLM_BASE_URL=https://your-llm-endpoint
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o
```

## Getting Started

### Step 1: Setup and Validation

Run the setup notebook to validate all connections:

```bash
jupyter notebook notebooks/00_setup_and_connections.ipynb
```

This notebook will:
- Install required Python packages
- Download the e-commerce FAQ dataset from HuggingFace
- Test AWS credentials and connectivity
- Verify Bedrock model access (Titan Embeddings V2)
- Test LLM API endpoint
- Validate all integrations

### Step 2: Data Exploration and Chunking

Explore different chunking strategies:

```bash
jupyter notebook notebooks/01_data_exploration_chunking.ipynb
```

This notebook covers:
- Loading and exploring the FAQ dataset (79 Q&A pairs)
- Creating sample policy documents (return, shipping, warranty)
- Implementing 4 chunking strategies:
  - Fixed-size chunking (naive)
  - Sentence-based chunking
  - Recursive character splitting (production-ready)
  - Semantic chunking (topic-based)
- Comparing chunking approaches
- Preparing knowledge base chunks

Key findings:
- Recursive character splitting with 50-character overlap works best
- Chunk size: 400-600 characters recommended
- Total: 93 chunks (14 policy chunks + 79 FAQ chunks)

### Step 3: Bedrock Knowledge Base Management

Set up and manage the vector database:

```bash
jupyter notebook notebooks/02_bedrock_knowledge_base.ipynb
```

This notebook demonstrates:
- Connecting to AWS Bedrock Knowledge Base
- Triggering and monitoring ingestion jobs
- Exploring indexed data structure
- Testing vector retrieval
- Visualizing retrieval scores
- Understanding semantic similarity

### Step 4: Build RAG Pipeline

Implement complete retrieval and generation:

```bash
jupyter notebook notebooks/03_baseline_rag.ipynb
```

This notebook builds:
- Vector search (semantic similarity)
- BM25 search (keyword-based)
- Hybrid search (combination of both)
- LLM-based answer generation
- Conversational memory
- Source attribution and citations
- Performance evaluation

Retrieval comparison:
- Vector: Best for natural language queries
- BM25: Best for exact keyword matches
- Hybrid (alpha=0.5): Balanced, recommended for production

### Step 5: Deploy to AWS

Deploy the application to AWS ECS Fargate:

```bash
jupyter notebook notebooks/04_deployment_to_aws.ipynb
```

Deployment steps:
- Create Amazon ECR repository
- Build and push Docker image
- Create ECS Fargate cluster
- Configure task definition (1 vCPU, 2GB recommended)
- Deploy service with public access
- Configure security groups (port 8501)

## Running Locally

### Option 1: Streamlit App

```bash
streamlit run app.py
```

Access the chatbot at: http://localhost:8501

### Option 2: Python API

```python
from src.rag_engine import ConversationalRAG

# Initialize chatbot
chatbot = ConversationalRAG(
    retrieval_method='hybrid',
    num_results=3,
    alpha=0.5
)

# Ask questions
response = chatbot.chat("What is your return policy?")
print(response['answer'])

# Follow-up questions
response = chatbot.chat("How long does it take?")
print(response['answer'])
```

## Docker Deployment

### Build Image

```bash
docker build -t ecommerce-rag-chatbot .
```

### Run Container

```bash
docker run -p 8501:8501 ecommerce-rag-chatbot
```

Access at: http://localhost:8501

## AWS Deployment

### Prerequisites

- AWS CLI configured
- IAM permissions for ECR, ECS, Fargate

### Quick Deployment

```bash
# 1. Create ECR repository
aws ecr create-repository --repository-name ecommerce-rag-chatbot --region us-east-1

# 2. Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# 3. Build and push
docker build -t ecommerce-rag-chatbot .
docker tag ecommerce-rag-chatbot:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ecommerce-rag-chatbot:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ecommerce-rag-chatbot:latest

# 4. Create ECS cluster (via AWS Console)
# 5. Create task definition (via AWS Console)
# 6. Deploy service (via AWS Console)
```

See Notebook 04 for detailed deployment instructions.

## Configuration

### Retrieval Methods

Choose your retrieval strategy in the app:

- **Vector Search**: Semantic similarity using embeddings (best for natural language)
- **BM25 Search**: Keyword-based ranking (best for exact terms)
- **Hybrid Search**: Weighted combination (alpha=0.5 recommended)

### Chunking Strategy

The system uses Recursive Character Text Splitting:
- Chunk size: 500 characters
- Overlap: 50 characters
- Separators: paragraphs, sentences, words

### LLM Parameters

Default configuration:
- Temperature: 0.1 (low for factual responses)
- Max tokens: 500
- Model: gpt-4o (configurable)

## Architecture

```
User Query
    ↓
Streamlit UI
    ↓
RAG Engine
    ├── Retrieval (Vector/BM25/Hybrid)
    │   └── AWS Bedrock Knowledge Base
    │       └── OpenSearch Serverless (Vector DB)
    └── Generation
        └── OpenAI-compatible LLM
            └── Answer + Citations
```

## Knowledge Base

### Data Sources

1. E-commerce FAQ Dataset
   - 79 Q&A pairs from HuggingFace
   - Topics: orders, shipping, returns, payments

2. Policy Documents
   - Return Policy (eligibility, process, timeline, restrictions)
   - Shipping Policy (timeframes, costs, tracking, regions)
   - Warranty Policy (coverage, exclusions, claims)

### Ingestion Process

1. Documents uploaded to S3
2. Bedrock parses and chunks documents
3. Titan Embeddings V2 generates vectors (1024 dimensions)
4. Vectors stored in OpenSearch Serverless
5. Available for semantic search

## Evaluation

### Retrieval Performance

Average relevance scores:
- Vector Search: 0.50
- BM25 Search: 0.48
- Hybrid Search: 0.55 (best)

### Answer Quality

- Factual accuracy: High (answers grounded in retrieved context)
- Source attribution: All answers include document citations
- Conversation coherence: Maintains context across turns

## Cost Estimation

### AWS Services (Monthly)

- ECS Fargate (1 vCPU, 2GB): ~$58/month (24/7 operation)
- Bedrock Knowledge Base: ~$5-10/month (storage + queries)
- OpenSearch Serverless: Included in Knowledge Base
- ECR storage: ~$0.05/month
- CloudWatch Logs: ~$0.50-1/month

Total: ~$65-70/month for continuous operation

Cost savings:
- Stop tasks when not in use (reduce to ~$10/month for storage)
- Use Fargate Spot (save ~70% on compute)

## Troubleshooting

### Common Issues

**Connection Timeout (Deployment)**
- Check security group allows port 8501
- Ensure public IP is enabled
- Verify subnets are public

**Task Keeps Stopping**
- Check CloudWatch logs for errors
- Verify .env file is included in Docker image
- Increase task memory to 2GB

**No Results from Knowledge Base**
- Verify KNOWLEDGE_BASE_ID is correct
- Check ingestion job completed successfully
- Ensure documents were uploaded to S3

**LLM Not Responding**
- Verify LLM_BASE_URL and LLM_API_KEY are correct
- Test endpoint independently
- Check CloudWatch logs for API errors

## Limitations

- No access to real-time data (orders, inventory)
- Cannot perform actions (process returns, cancel orders)
- Limited to pre-indexed knowledge
- Single-step retrieval (no iterative reasoning)

## Future Enhancements

- Add authentication (AWS Cognito, Streamlit auth)
- Implement custom domain with Application Load Balancer
- Add database integration for order lookups
- Build agentic RAG with LangGraph for multi-step reasoning
- Add feedback collection and evaluation metrics
- Implement A/B testing for retrieval strategies

## License

This project is for demonstration purposes.

## Acknowledgments

- Dataset: HuggingFace Ecommerce_FAQ by Andyrasika
- Embeddings: Amazon Titan Embeddings V2
- Vector Store: AWS Bedrock Knowledge Base with OpenSearch Serverless
- UI Framework: Streamlit
