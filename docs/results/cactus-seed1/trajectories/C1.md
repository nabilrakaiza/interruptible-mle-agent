# Trajectory: C1_aerial-cactus-identification_seed1

- **Task** aerial-cactus-identification, **condition** C1, **seed** 1
- **Nodes** 18 (94% working), **budget used** 120.1 min, **LLM** 21 calls, 279,207 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Scikit-learn Multi-layer Perceptron classifier on pixel features, Pillow thumbnail preprocessing pipeline for uniform image inputs, Soft voting ensemble of diverse classifiers, AdaBoost ensemble of shallow decision trees, Manual hyperparameter-controlled neural network training loop
- **Search** 2 improve chains exhausted; longest stretch without a new best 3 nodes; selection regret 0.0 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will load every 32x32 RGB image, flatten it into pixel features, and standardize the features. A L2-regul... (val 0.9432) |
| n0 | new best | val 0.9432, probe 0.9484: I will load every 32x32 RGB image, flatten it into pixel features, and standardize the ... |
| n1 | draft | I will train a scikit-learn MLP classifier on flattened, standardized RGB pixel features, which is a non-li... (val 0.9607) |
| n1 | new best | val 0.9607, probe 0.9599, 1.85% better than n0: I will train a scikit-learn MLP classifier on flattened, standardized RGB pixel feature... |
| n1 | card used | first script with MLPClassifier from the card "Scikit-learn Multi-layer Perceptron classifier on pixel features" |
| n2 | draft | I'll train a small convolutional neural network from scratch on the 32x32 RGB images using PyTorch, a diffe... (val 0.9920) |
| n2 | new best | val 0.9920, probe 0.9884, 3.26% better than n1: I'll train a small convolutional neural network from scratch on the 32x32 RGB images us... |
| n3 | draft | I will avoid training deep networks and instead represent each 32x32 JPEG as a compact 16x16 RGB thumbnail.... (val 0.9519) |
| n4 | draft | I will use a different approach from the earlier baselines by reducing each image to a 16x16 RGB thumbnail,... (val 0.9553) |
| n6 | new best | val 0.9929, probe 0.9891, 0.09% better than n2: I will add random horizontal and vertical flips as data augmentation during CNN trainin... |
| n8 | new best | val 0.9991, probe 0.9989, 0.62% better than n6: I will improve the CNN architecture by replacing the plain two-convolution network with... |
| n11 | chain exhausted | the chain from n8 had 3 attempts without a real gain; the search moves elsewhere |
| n12 | new best | val 0.9999, probe 0.9999, 0.08% better than n8: I will replace the small convolutional network with a deeper residual CNN that uses wid... |
| n14 | new best | val 0.9999, probe 0.9999, 0.00% better than n12: Replace the fixed Adam learning rate with a cosine annealing schedule. The learning rat... |
| n15 | chain exhausted | the chain from n12 had 3 attempts without a real gain; the search moves elsewhere |
| n17 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n14 | final pick | val 0.9999 (rank 1 of 17), test 0.9999 (rank 1 of 17) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
