# Trajectory: C6_aerial-cactus-identification_seed102

- **Task** aerial-cactus-identification, **condition** C6, **seed** 102
- **Nodes** 28 (36% working), **budget used** 240.7 min, **LLM** 32 calls, 610,614 tokens
- **Interventions** 9 applied, 1 dropped
- **Model cards** PyTorch CNN for small fixed-size images, Scikit-learn MLP classifier on flattened pixels, Soft-voting ensemble of classifiers, AdaBoost with weak learners on image features, Pillow preprocessing and resizing pipeline, Hyperparameter tuning for neural network training
- **Search** 4 improve chains exhausted; longest stretch without a new best 10 nodes; selection regret 0.0 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Train a small convolutional neural network from scratch in PyTorch on the 32x32 RGB cactus images. Load all... (val 0.9988) |
| n1 | draft | I will use a non-CNN pipeline: load all RGB thumbnails, flatten them, reduce dimensionality with randomized... (val 0.9571) |
| n1 | card used | first script with MLPClassifier from the card "Scikit-learn MLP classifier on flattened pixels" |
| n2 | draft | I will extract compact color and texture features from each 32x32 image using per-channel statistics, color... (val 0.9938) |
| n3 | draft | Instead of a CNN, PCA+MLP, or boosted trees, I will use a simple linear classifier on raw pixels. Each 32x3... (val 0.9462) |
| n3 | intervention | human: prune n1, applied - [Claude] not a CNN model (PCA + sklearn MLP), val 0.957, weakest |
| n3 | intervention | human: prune n2, applied - [Claude] not a CNN model (handcrafted colour/texture + HistGradientBoosting), val 0.9938 |
| n4 | draft | I will use an Extra-Trees classifier on flattened 32x32 RGB pixel values, avoiding deep learning and pretra... (val 0.9791) |
| n9 | intervention | human: prune n3, applied - [Claude] not a CNN model (logistic regression on raw pixels), val 0.946 |
| n9 | intervention | human: prune n4, applied - [Claude] not a CNN model (Extra-Trees on raw pixels), val 0.979 |
| n9 | intervention | human: prune n6, dropped (already pruned) - [Claude] not a CNN model (sklearn MLP on raw pixels, branch of n3), val 0.965 |
| n10 | draft | I will train a compact strided convolutional network in PyTorch directly on normalized 32x32 RGB images, us... (val 1.0000) |
| n10 | new best | val 1.0000, probe 0.9996: I will train a compact strided convolutional network in PyTorch directly on normalized ... |
| n13 | chain exhausted | the chain from n10 had 3 attempts without a real gain; the search moves elsewhere |
| n14 | draft | I will use a soft-voting ensemble of three scikit-learn classifiers on PCA-reduced standardized raw pixels:... (val 0.9642) |
| n14 | intervention | human: prune n11, applied - [Claude] regression/broken: EMA drops val to 0.7528 from parent n10 0.99995; fix attempt n12 identical 0.7528 |
| n14 | intervention | human: prune n8, applied - [Claude] regression: TTA 0.99878 below parent n7 0.99905; dominated by n10 line |
| n17 | intervention | human: prune n14, applied - [Claude] not a CNN model (sklearn soft-voting ensemble on PCA pixels), val 0.964-0.968 incl. children n15/n16 |
| n18 | draft | I will train a small residual CNN from scratch in PyTorch on the normalized 32x32 RGB thumbnails. I will us... (val 1.0000) |
| n18 | new best | val 1.0000, probe 1.0000, 0.00% better than n10: I will train a small residual CNN from scratch in PyTorch on the normalized 32x32 RGB t... |
| n19 | new best | val 1.0000, probe 1.0000, 0.00% better than n18: I will add squeeze-and-excitation (SE) blocks to the residual CNN. Each residual block ... |
| n19 | intervention | human: prune n0, applied - [Claude] weak branch: n0 line best 0.99934 (n9) vs n18 0.99997 / n10 0.99995; focus search on the best branches |
| n20 | no-op | same predictions as n18: I will replace the final single-checkpoint selection with a snapshot ensemble: after tr... |
| n20 | intervention | human: prune n13, applied - [Claude] regression: translation aug 0.99972 below parent n10 0.99995 |
| n21 | chain exhausted | the chain from n18 had 3 attempts without a real gain; the search moves elsewhere |
| n22 | draft | I will train a compact depthwise-separable convolutional network from scratch on the 32x32 RGB thumbnails, ... (val 1.0000) |
| n22 | new best | val 1.0000, probe 1.0000, 0.00% better than n19: I will train a compact depthwise-separable convolutional network from scratch on the 32... |
| n25 | chain exhausted | the chain from n22 had 3 attempts without a real gain; the search moves elsewhere |
| n26 | draft | I will train a compact VGG-style convolutional network from scratch on the 32x32 RGB cactus thumbnails, usi... (val 0.9999) |
| n27 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n22 | final pick | val 1.0000 (rank 1 of 10), test 1.0000 (rank 6 of 10) |
| n18 | best on test | test 1.0000, but val rank 3 of 10: I will train a small residual CNN from scratch in PyTorch on the normalized 32x32 RGB t... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
