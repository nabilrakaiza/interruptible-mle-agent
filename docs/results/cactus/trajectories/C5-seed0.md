# Trajectory: C5_aerial-cactus-identification_seed0

- **Task** aerial-cactus-identification, **condition** C5, **seed** 0
- **Nodes** 27 (89% working), **budget used** 120.0 min, **LLM** 31 calls, 510,090 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** scikit-learn MLPClassifier on pixel features, Soft-voting ensemble of classifiers, AdaBoost with weak learners, Pillow image preprocessing and resizing, Training loop with epoch, batch, and learning-rate tuning
- **Search** 5 improve chains exhausted; longest stretch without a new best 17 nodes; selection regret 0.0 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will flatten the 32x32 RGB images into 3072-dimensional pixel vectors and scale them to [0,1]. A logistic... (val 0.9454) |
| n0 | new best | val 0.9454, probe 0.9513: I will flatten the 32x32 RGB images into 3072-dimensional pixel vectors and scale them ... |
| n1 | draft | Build a small convolutional neural network in PyTorch, trained from scratch on the 32x32 RGB images. Load l... (val 0.9998) |
| n1 | new best | val 0.9998, probe 0.9999, 5.75% better than n0: Build a small convolutional neural network in PyTorch, trained from scratch on the 32x3... |
| n2 | draft | Use a scikit-learn MLPClassifier on downsampled RGB pixels instead of logistic regression or a custom PyTor... (val 0.9493) |
| n2 | card used | first script with MLPClassifier from the card "scikit-learn MLPClassifier on pixel features" |
| n2 | card used | first script with MLPClassifier from the card "Soft-voting ensemble of classifiers" |
| n3 | draft | Use PCA plus a Random Forest classifier on the full 32x32 RGB pixel values, which is a different approach f... (val 0.9642) |
| n4 | draft | This solution uses a gradient-boosted tree model on handcrafted color and texture features rather than raw ... (val -) |
| n4 | crash | runtime_error: AttributeError: 'HistGradientBoostingClassifier' object has no attribute 'best_iteration_' |
| n5 | new best | val 0.9999, probe 0.9999, 0.01% better than n1: Add random 90-degree rotations as an additional augmentation during training and extend... |
| n6 | fixed | debug fixed the crash in n4 after 1 attempt(s) |
| n8 | chain exhausted | the chain from n1 had 3 attempts without a real gain; the search moves elsewhere |
| n15 | crash | runtime_error: ValueError: object too deep for desired array |
| n17 | fixed | debug fixed the crash in n15 after 1 attempt(s) |
| n23 | new best | val 1.0000, probe 1.0000, 0.01% better than n5: Start from the best previous CNN recipe (stratified 90/10 validation, random 90-degree ... |
| n24 | new best | val 1.0000, probe 1.0000, 0.00% better than n23: Retain the exact residual CNN, training loop, and rotation-only test-time augmentation ... |
| n26 | crash | timeout: killed after 52s |
| n26 | chain exhausted | the chain from n23 had 3 attempts without a real gain; the search moves elsewhere |
|  | stop | budget, final selection best_val |
| n24 | final pick | val 1.0000 (rank 1 of 24), test 1.0000 (rank 3 of 24) |
| n25 | best on test | test 1.0000, but val rank 3 of 24: Add a lightweight squeeze-and-excitation (SE) channel-attention layer after each residu... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
