# Part 6: Fine-Tuning LLMs

Fine-tune an open-source LLM for e-commerce customer service, building on the RAG (Part 4) and Agentic RAG (Part 5) foundations.

## What's Different from Parts 4-5?

| Aspect | Parts 4-5 (API-based LLM) | Part 6 (Fine-Tuned LLM) |
|--------|--------------------------|------------------------|
| Model | Cloud API (gpt-4o) | Local open-source model |
| Customization | Prompt engineering | Trained on domain data |
| Cost | Per-token pricing | One-time GPU compute |
| Privacy | Data sent externally | Data stays local |
| Brand Voice | Relies on system prompt | Learned from examples |

## Prerequisites

- Completed Parts 4-5 (Python, RAG, Agentic RAG)
- NVIDIA GPU with 16-24 GB VRAM (RTX 3090, 4080, 4090, etc.)
- CUDA toolkit installed
- Hugging Face account with access to Llama 3.2 (or alternative model)
- ~10 GB disk space for model weights and outputs

## Notebooks

### Core Session (1.5 hours)

1. **01_foundations_and_setup.ipynb** - GPU setup, model loading, baseline testing
2. **02_data_prep_and_fine_tuning.ipynb** - Data preparation + QLoRA fine-tuning
3. **03_evaluation_and_comparison.ipynb** - Metrics, LLM-as-judge, gap analysis

### Bonus (if time permits)

4. **04_advanced_techniques.ipynb** - Hyperparameter tuning, DPO, larger models
5. **05_production_pipeline.ipynb** - Merge, export, integrate with agentic RAG

## Setup

### Option A: Conda (Recommended for Windows)

Conda handles CUDA/cuDNN automatically -- no need to install CUDA toolkit separately.

```bash
# Create environment
conda create -n finetune python=3.11 -y
conda activate finetune

# Install PyTorch with CUDA (handles CUDA automatically)
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia

# Install fine-tuning and ML libraries
pip install transformers peft trl bitsandbytes accelerate datasets
pip install sentence-transformers rouge-score scikit-learn matplotlib
pip install openai python-dotenv jupyter

# Verify GPU
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

### Troubleshooting: SSL Errors on Windows

If you get `disabling truststore since ssl support is missing` or `no matching distribution found` errors during pip install:

```bash
# Fix 1: Install OpenSSL in conda first
conda install openssl certifi ca-certificates -y
# Then retry the pip installs above

# Fix 2: If still failing, use trusted host flag
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org transformers peft trl bitsandbytes accelerate datasets
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org sentence-transformers rouge-score scikit-learn matplotlib
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org openai python-dotenv jupyter

# Fix 3: Install what you can via conda-forge, rest via pip
conda install -c conda-forge openai python-dotenv jupyter scikit-learn matplotlib -y
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org transformers peft trl bitsandbytes accelerate datasets sentence-transformers rouge-score
```

### Option B: venv (Linux/Mac/Colab)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Google Colab

All notebooks work on Colab (free tier T4 GPU is sufficient). No local setup needed -- just upload the notebooks and run the `!pip install` cells.

### Configure Environment

```bash
cp .env.example .env
# Edit .env with your HF token and LLM API credentials

# Login to Hugging Face (for gated models)
huggingface-cli login
```

## Models Used

| Model | Parameters | VRAM (4-bit) | Use Case |
|-------|-----------|-------------|----------|
| Llama 3.2 1B Instruct | 1.24B | ~2 GB | Primary (fast iteration) |
| Llama 3.2 3B Instruct | 3.21B | ~4 GB | Quality comparison |
| Mistral 7B Instruct v0.3 | 7.24B | ~6 GB | Optional (advanced) |

## Architecture

```
Fine-Tuned LLM (Part 6)
     |
     v
Agent Loop (Part 5)
     |
     v
Tools + RAG KB (Parts 4-5)
```

## Key Concepts

- **QLoRA**: 4-bit quantized LoRA -- fine-tune large models on consumer GPUs
- **SFT**: Supervised Fine-Tuning on instruction/conversation data
- **DPO**: Direct Preference Optimization for response quality
- **Adapter Merging**: Combine LoRA weights into base model for deployment
