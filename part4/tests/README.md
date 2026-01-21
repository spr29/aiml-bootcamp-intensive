# Test Scripts

Test scripts for validating various components of the RAG system.

## Available Tests

### `test_bedrock.py`
Tests AWS Bedrock Claude model access and inference.

**Usage:**
```bash
python tests/test_bedrock.py
```

**Tests:**
- AWS credentials validity
- Bedrock service access
- Claude model inference
- Response generation

---

### `test_embeddings.py`
Tests embedding models on AWS Bedrock.

**Usage:**
```bash
python tests/test_embeddings.py
```

**Tests:**
- Titan embedding model access
- Embedding generation
- Vector dimensions validation

---

### `test_paypal_llm.py`
Tests LLM endpoint connectivity and inference.

**Usage:**
```bash
python tests/test_paypal_llm.py
```

**Tests:**
- LLM API endpoint connectivity
- Authentication with API key
- Model availability
- Chat completion generation

---

### `test_hybrid_setup.py`
Tests the complete hybrid setup (LLM + Embeddings).

**Usage:**
```bash
python tests/test_hybrid_setup.py
```

**Tests:**
- LLM endpoint (OpenAI-compatible)
- Bedrock embeddings (Titan v2)
- Combined functionality
- End-to-end validation

---

### `test_bedrock_kb.py`
Tests Bedrock Knowledge Base retrieval.

**Usage:**
```bash
python tests/test_bedrock_kb.py
```

**Tests:**
- Knowledge Base connectivity
- Document retrieval
- Relevance scoring
- Multiple query types

---

## Running All Tests

```bash
# Run all tests sequentially
for test in tests/test_*.py; do
    echo "Running $test..."
    python "$test"
    echo "---"
done
```

## Prerequisites

All tests require:
- Valid `.env` file with credentials
- Virtual environment activated
- Dependencies installed: `pip install -r requirements.txt`

## Expected Results

**Successful Test Output:**
```
[OK] Test passed
[OK] All components working
```

**Failed Test Output:**
```
[FAILED] Error message
[WARNING] Potential issue
```

## Troubleshooting

### AWS Credentials Error
- Check `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`
- Verify IAM permissions for Bedrock

### LLM Connection Error
- Verify `LLM_BASE_URL` and `LLM_API_KEY` in `.env`
- Check network connectivity to LLM endpoint

### Knowledge Base Error
- Ensure `KNOWLEDGE_BASE_ID` is correct
- Verify ingestion job completed successfully
- Check data source is synced
