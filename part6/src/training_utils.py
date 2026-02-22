"""Training utilities for QLoRA fine-tuning."""

import json
import torch
from pathlib import Path
from transformers import BitsAndBytesConfig
from peft import LoraConfig, TaskType
from trl import SFTConfig


def get_quantization_config():
    """Get the standard 4-bit NF4 quantization config for QLoRA.

    Returns:
        BitsAndBytesConfig for 4-bit quantization
    """
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type='nf4',
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )


def get_lora_config(rank=16, alpha=32, target_modules=None, dropout=0.05):
    """Get a LoRA configuration.

    Args:
        rank: LoRA rank (default 16)
        alpha: LoRA alpha scaling (default 32, typically 2x rank)
        target_modules: List of module names to apply LoRA to
        dropout: LoRA dropout rate (default 0.05)

    Returns:
        LoraConfig instance
    """
    if target_modules is None:
        target_modules = ['q_proj', 'k_proj', 'v_proj', 'o_proj']

    return LoraConfig(
        r=rank,
        lora_alpha=alpha,
        target_modules=target_modules,
        lora_dropout=dropout,
        bias='none',
        task_type=TaskType.CAUSAL_LM
    )


def get_training_args(output_dir, **overrides):
    """Get standard SFT training arguments with optional overrides.

    Args:
        output_dir: Directory to save checkpoints
        **overrides: Any SFTConfig parameters to override

    Returns:
        SFTConfig instance
    """
    defaults = {
        'output_dir': str(output_dir),
        'num_train_epochs': 3,
        'per_device_train_batch_size': 2,
        'gradient_accumulation_steps': 4,
        'learning_rate': 2e-4,
        'warmup_steps': 10,
        'logging_steps': 10,
        'save_steps': 50,
        'fp16': True,
        'max_seq_length': 512,
        'optim': 'paged_adamw_32bit',
        'dataset_text_field': 'text',
        'report_to': 'none',
    }
    defaults.update(overrides)
    return SFTConfig(**defaults)


def print_trainable_parameters(model):
    """Print a formatted summary of trainable vs total parameters.

    Args:
        model: The PEFT model
    """
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    pct = trainable / total * 100

    print(f'Trainable parameters: {trainable:,} / {total:,} ({pct:.2f}%)')
    print(f'  Trainable: {trainable / 1e6:.1f}M')
    print(f'  Total: {total / 1e6:.1f}M')


def load_configs(configs_dir):
    """Load LoRA and training configs from JSON files.

    Args:
        configs_dir: Path to configs/ directory

    Returns:
        Tuple of (lora_params dict, training_params dict)
    """
    configs_dir = Path(configs_dir)

    with open(configs_dir / 'lora_config.json') as f:
        lora_params = json.load(f)

    with open(configs_dir / 'training_config.json') as f:
        training_params = json.load(f)

    return lora_params, training_params
