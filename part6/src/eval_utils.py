"""Evaluation utilities for comparing base vs fine-tuned models."""

import json
import numpy as np
import pandas as pd
from rouge_score import rouge_scorer


def compute_rouge(predictions, references):
    """Compute ROUGE-L scores between predictions and references.

    Args:
        predictions: List of generated responses
        references: List of expected responses

    Returns:
        List of ROUGE-L F1 scores
    """
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = []
    for pred, ref in zip(predictions, references):
        score = scorer.score(ref, pred)
        scores.append(score['rougeL'].fmeasure)
    return scores


def compute_semantic_similarity(predictions, references, model_name='all-MiniLM-L6-v2'):
    """Compute cosine similarity between prediction and reference embeddings.

    Args:
        predictions: List of generated responses
        references: List of expected responses
        model_name: Sentence transformer model name

    Returns:
        List of cosine similarity scores
    """
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    embed_model = SentenceTransformer(model_name)
    pred_embeds = embed_model.encode(predictions)
    ref_embeds = embed_model.encode(references)

    similarities = []
    for p, r in zip(pred_embeds, ref_embeds):
        sim = cosine_similarity([p], [r])[0][0]
        similarities.append(float(sim))

    return similarities


def llm_judge(query, reference, response, llm_client, model_name):
    """Use an LLM to judge response quality on a 1-5 scale.

    Args:
        query: Customer query
        reference: Expected/reference response
        response: Model-generated response
        llm_client: OpenAI client instance
        model_name: Model name for judging

    Returns:
        Dict with 'helpfulness', 'accuracy', 'tone' scores (1-5)
    """
    judge_prompt = f"""You are evaluating an e-commerce customer service response.

CUSTOMER QUERY: {query}

REFERENCE ANSWER: {reference}

MODEL RESPONSE: {response}

Rate the MODEL RESPONSE on these criteria (1-5 scale):
1. **Helpfulness** (1=useless, 5=very helpful): Does it address the customer's need?
2. **Accuracy** (1=wrong, 5=perfectly accurate): Is the information correct?
3. **Tone** (1=rude/robotic, 5=friendly/professional): Appropriate customer service tone?

Return ONLY a JSON object:
{{"helpfulness": X, "accuracy": X, "tone": X}}"""

    result = llm_client.chat.completions.create(
        model=model_name,
        messages=[{'role': 'user', 'content': judge_prompt}],
        temperature=0.1,
        max_tokens=100
    )

    content = result.choices[0].message.content.strip()
    if '```' in content:
        content = content.split('```')[1].replace('json', '').strip()

    return json.loads(content)


def compare_models(queries, base_responses, ft_responses, references):
    """Build a comparison DataFrame with all metrics.

    Args:
        queries: List of customer queries
        base_responses: List of base model responses
        ft_responses: List of fine-tuned model responses
        references: List of expected responses

    Returns:
        DataFrame with queries, responses, and metrics
    """
    # Compute ROUGE
    base_rouge = compute_rouge(base_responses, references)
    ft_rouge = compute_rouge(ft_responses, references)

    # Compute similarity
    base_sim = compute_semantic_similarity(base_responses, references)
    ft_sim = compute_semantic_similarity(ft_responses, references)

    df = pd.DataFrame({
        'query': queries,
        'expected': references,
        'base_response': base_responses,
        'ft_response': ft_responses,
        'base_rouge': base_rouge,
        'ft_rouge': ft_rouge,
        'base_similarity': base_sim,
        'ft_similarity': ft_sim,
        'base_len': [len(r) for r in base_responses],
        'ft_len': [len(r) for r in ft_responses],
    })

    return df
