# LoRA: Low-Rank Adaptation (Phi-3-mini)


## Hidden Size: Where It All Starts

Every token in the model is represented as a vector of numbers. The **hidden size** is the length of that vector.

```
Token: "return"  →  [0.12, -0.45, 0.78, 0.03, ..., -0.91]
                     ←------------ 3072 numbers -----------→

Phi-3-mini hidden size = 3072
```

These 3072 numbers encode everything the model understands about that token — its meaning, context, grammar, relationships. As the token passes through each of Phi-3's 32 transformer layers, these numbers get updated.

```
Input: "return" → [3072 numbers]
     ↓ Layer 1:   [3072 numbers updated]
     ↓ Layer 2:   [3072 numbers updated]
     ↓ ...
     ↓ Layer 32:  [3072 numbers updated]
Output: prediction for next token
```

The weight matrices (W) in each layer are 3072 x 3072 because they transform one 3072-length vector into another 3072-length vector. This is where LoRA comes in.


## The Problem

A neural network layer is a matrix multiplication:

```
output = W x input

W = weight matrix = 3072 x 3072 = 9,437,184 numbers (~9.4M per layer)
```

Fine-tuning changes W by some amount delta-W (the difference between old and new weights):

```
Before fine-tuning:  W           (original weights)
After fine-tuning:   W + delta-W (original + changes)

output = (W + delta-W) x input
```

But delta-W is the same size as W — 9.4M parameters per layer. Across all layers and projections in Phi-3, that's ~2B total parameters. Too expensive to train on a 12 GB GPU.


## LoRA's Key Insight

The useful changes during fine-tuning are **low rank** — most of the 9.4M values in delta-W are redundant. We can approximate delta-W by multiplying two much smaller matrices:

```
delta-W  =  B  x  A

                         r=16
                    |<--------->|
                    |           |
          A =       |     A     |  ← shape: 16 x 3072
                    |           |
                    |-----------|

                    |-----------|
                    |           |
                    |           |
          B = 3072  |     B     |  ← shape: 3072 x 16
                    |           |
                    |           |
                    |-----------|
                        r=16

          B x A = 3072 x 3072     (same shape as delta-W!)
```


## Parameter Savings

```
Full fine-tuning (delta-W):

    3072
    +--------------------------+
    |                          |
    |       9,437,184          |
    |       parameters         |  3072
    |       (all trainable)    |
    |                          |
    +--------------------------+


LoRA with r=16 (B x A):

    16                              3072
    +----+                     +----+----+----+----+
    |    |                     |                    |
    |    |                     | A: 16 x 3072       | 16
    | B  | 3072                | = 49,152 params    |
    |    |                     +----+----+----+----+
    |    |
    |    |                     Total: 49,152 + 49,152
    +----+                          = 98,304 params
    B: 3072 x 16
    = 49,152 params            That's 96x fewer!
```


## How Rank (r) Affects Size

```
r=4:     (3072 x 4)  + (4 x 3072)  =   24,576 params  | very small
r=16:    (3072 x 16) + (16 x 3072) =   98,304 params  | good default (our choice)
r=64:    (3072 x 64) + (64 x 3072) =  393,216 params  | more expressive
                                                        |
Full:     3072 x 3072              = 9,437,184 params   | original size
```

Higher rank = more capacity to learn, but more VRAM and overfitting risk.
The rank does NOT depend on the hidden size — you choose it based on your dataset size and task complexity.


## The Forward Pass

```
                    input
                      |
          +-----------+-----------+
          |                       |
          v                       v
    +------------+          +----------+
    | W (frozen) |          |    A     |  trainable
    | 3072x3072  |          | 16x3072  |
    +------------+          +----------+
          |                       |
          |                       v
          |               +----------+
          |               |    B     |  trainable
          |               | 3072x16  |
          |               +----------+
          |                       |
          v                       v
    +------------+          +----------+
    | W x input  |          | BxAx inp |
    +------------+          +----------+
          |                       |
          |         scale by      |
          |        alpha / r      |
          |        = 32/16 = 2x   |
          |                       |
          +----------++-----------+
                     ||
                     vv
               +------------+
               |   output   |
               | W*inp +    |
               | 2 * BA*inp |
               +------------+
```

Formula:

```
output = W*input + (alpha / r) * B * A * input
         ^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         frozen         trainable (small)

For our config:
output = W*input + (32 / 16) * B * A * input
       = W*input + 2 * B * A * input
```


## Alpha Scaling

Alpha controls how strongly the adapter influences the output.

```
alpha = 32, r = 16  -->  scaling = 32/16 = 2x   (our config)
alpha = 16, r = 16  -->  scaling = 16/16 = 1x   (neutral)
alpha = 8,  r = 16  -->  scaling = 8/16  = 0.5x (subtle changes)
```

Think of it as a volume knob for the adapter's effect. We use 2x so the adapter's small corrections are amplified enough to meaningfully change the output.


## Initialization

```
At start of training:

A = small random values    (Gaussian)
B = all zeros

B x A = zero matrix  -->  adapter has NO effect
                          model behaves exactly like base Phi-3

During training:

A and B learn gradually  -->  adapter effect increases
                              model starts responding like ShopEasy agent
```

This ensures training starts from the base model's behavior and changes smoothly.


## Where LoRA Is Applied in Phi-3

LoRA adapters are added to specific layers inside each transformer block:

```
Phi-3 Transformer Layer (repeated 32 times)
+--------------------------------------------------+
|                                                  |
|   Attention Block                                |
|   +--------------------------------------------+|
|   |  q_proj  [W + BA]  <-- "what am I looking  ||
|   |                         for?"               ||
|   |  k_proj  [W + BA]  <-- "what info do I     ||
|   |                         have?"              ||
|   |  v_proj  [W + BA]  <-- "what content to    ||
|   |                         pass forward"       ||
|   |  o_proj  [W + BA]  <-- "combine attention  ||
|   |                         results"            ||
|   +--------------------------------------------+|
|                                                  |
|   MLP Block (not targeted in our config)         |
|   +--------------------------------------------+|
|   |  gate_proj  [W]  (frozen, no LoRA)          ||
|   |  up_proj    [W]  (frozen, no LoRA)          ||
|   |  down_proj  [W]  (frozen, no LoRA)          ||
|   +--------------------------------------------+|
|                                                  |
+--------------------------------------------------+

4 projections x 32 layers = 128 LoRA adapter pairs (A and B)
Each pair: 98,304 params
Total LoRA params: ~0.5% of Phi-3's 3.8B parameters
```


## Our Config (NB02)

```python
LoraConfig(
    r=16,                    # Rank: 16-dim adapter matrices
    lora_alpha=32,           # Scaling: 32/16 = 2x amplification
    target_modules=[         # Which layers get adapters:
        'q_proj',            #   Query projection
        'k_proj',            #   Key projection
        'v_proj',            #   Value projection
        'o_proj'             #   Output projection
    ],
    lora_dropout=0.05,       # 5% dropout to prevent overfitting
    bias='none',             # Don't train bias terms
    task_type='CAUSAL_LM'   # This is a text generation model
)
```

Result: ~9.5 MB adapter instead of modifying the ~4 GB base model.


## QLoRA: LoRA + Quantization

QLoRA combines 4-bit quantization with LoRA for maximum VRAM savings:

```
Full Fine-Tuning          LoRA                    QLoRA (what we use)
+------------------+    +------------------+    +------------------+
|                  |    |                  |    |                  |
| All params       |    | W frozen (16-bit)|    | W frozen (4-bit) |
| trainable        |    | + B,A (16-bit)   |    | + B,A (16-bit)   |
| (16-bit)         |    |                  |    |                  |
|                  |    |                  |    |                  |
| ~8 GB VRAM       |    | ~4 GB VRAM       |    | ~2.1 GB VRAM     |
| for Phi-3        |    | for Phi-3        |    | for Phi-3        |
+------------------+    +------------------+    +------------------+

Base model weights:       frozen               frozen
                         full precision        4-bit compressed (NF4)

Adapter weights:          N/A                  16-bit (full precision)
                                               (small, so no need to compress)
```

The base model is compressed to 4-bit to save VRAM. The adapter stays in 16-bit full precision because it's tiny (~9.5 MB) and needs to learn accurately. This is why we can fine-tune Phi-3 (3.8B parameters) on a single 12 GB GPU.
