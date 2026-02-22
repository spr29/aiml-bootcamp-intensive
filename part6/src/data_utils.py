"""Data utilities for fine-tuning data preparation."""

import json
import random
import pandas as pd
from pathlib import Path


def load_faq_data(csv_path):
    """Load the e-commerce FAQ data from Part 4.

    Args:
        csv_path: Path to ecommerce_faq.csv

    Returns:
        DataFrame with 'question' and 'answer' columns
    """
    return pd.read_csv(csv_path)


def format_as_instruction(question, answer, system_prompt):
    """Convert a single Q&A pair into chat message format.

    Args:
        question: Customer question
        answer: Expected assistant answer
        system_prompt: System prompt for the agent

    Returns:
        Dict with 'messages' key containing the chat messages
    """
    return {
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': question},
            {'role': 'assistant', 'content': answer}
        ]
    }


def generate_conversations(llm_client, model_name, faq_df, system_prompt, scenario, faq_context=None):
    """Generate synthetic multi-turn conversations using an LLM.

    Args:
        llm_client: OpenAI client instance
        model_name: Model name for generation
        faq_df: DataFrame with FAQ data
        system_prompt: System prompt for the agent
        scenario: Dict with 'topic', 'description', 'num_conversations'
        faq_context: Pre-built FAQ context string (optional)

    Returns:
        List of conversation dicts with 'messages' key
    """
    if faq_context is None:
        faq_context = '\n'.join(
            f'Q: {row["question"]}\nA: {row["answer"]}\n'
            for _, row in faq_df.iterrows()
        )

    conversations = []

    for _ in range(scenario['num_conversations']):
        generation_prompt = f"""Generate a realistic multi-turn customer service conversation for an e-commerce store called ShopEasy.

SCENARIO: {scenario['description']}

REFERENCE FAQ DATA (use this to ensure accuracy):
{faq_context[:3000]}

RULES:
- Generate 3-6 turns (alternating user/assistant messages)
- The assistant should be concise, friendly, and professional
- Use realistic customer language (casual, sometimes frustrated)
- Include specific details (order numbers like ORD-XXXXX, product names, dates)
- The assistant's answers should be consistent with the FAQ data above
- Do NOT include any system message -- just the user/assistant turns

Return ONLY a valid JSON array of message objects:
[
  {{"role": "user", "content": "..."}},
  {{"role": "assistant", "content": "..."}},
  ...
]"""

        try:
            response = llm_client.chat.completions.create(
                model=model_name,
                messages=[{'role': 'user', 'content': generation_prompt}],
                temperature=0.9,
                max_tokens=1000
            )

            content = response.choices[0].message.content.strip()
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            turns = json.loads(content)
            messages = [{'role': 'system', 'content': system_prompt}] + turns
            conversations.append({'messages': messages})
        except Exception:
            continue

    return conversations


def create_train_eval_split(data, eval_ratio=0.1, seed=42):
    """Split data into train and eval sets.

    Args:
        data: List of training samples
        eval_ratio: Fraction for evaluation (default 0.1)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (train_data, eval_data)
    """
    shuffled = data.copy()
    random.seed(seed)
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * (1 - eval_ratio))
    return shuffled[:split_idx], shuffled[split_idx:]


def validate_dataset(data):
    """Validate dataset format and quality.

    Args:
        data: List of training samples

    Returns:
        Dict with 'issues' (list of strings) and 'stats' (dict)
    """
    issues = []
    turn_counts = []

    for i, sample in enumerate(data):
        messages = sample.get('messages', [])

        if not messages:
            issues.append(f'Sample {i}: Empty messages')
            continue

        if messages[0]['role'] != 'system':
            issues.append(f'Sample {i}: First message is not system')

        for j, msg in enumerate(messages):
            if not msg.get('content', '').strip():
                issues.append(f'Sample {i}, message {j}: Empty content')

        if messages[-1]['role'] != 'assistant':
            issues.append(f'Sample {i}: Last message is not assistant')

        turns = len([m for m in messages if m['role'] != 'system'])
        turn_counts.append(turns)

    stats = {
        'total_samples': len(data),
        'min_turns': min(turn_counts) if turn_counts else 0,
        'max_turns': max(turn_counts) if turn_counts else 0,
        'avg_turns': sum(turn_counts) / len(turn_counts) if turn_counts else 0,
        'single_turn': sum(1 for t in turn_counts if t == 2),
        'multi_turn': sum(1 for t in turn_counts if t > 2),
    }

    return {'issues': issues, 'stats': stats}
