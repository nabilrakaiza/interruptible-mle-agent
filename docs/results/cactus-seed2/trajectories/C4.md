# Trajectory: C4_aerial-cactus-identification_seed2

- **Task** aerial-cactus-identification, **condition** C4, **seed** 2
- **Nodes** 50 (94% working), **budget used** 122.3 min, **LLM** 60 calls, 1,068,345 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** PyTorch CNN image classifier, scikit-learn MLP classifier on pixel features, Soft voting ensemble of classifiers, AdaBoost with shallow trees on image features, Pillow preprocessing pipeline for image inputs
- **Search** 10 improve chains exhausted; longest stretch without a new best 21 nodes; selection regret 0.0 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use a small PyTorch CNN on the 32x32 RGB images, since the task is image classification and the images are ... (val 0.9978) |
| n0 | new best | val 0.9978, probe 0.9959: Use a small PyTorch CNN on the 32x32 RGB images, since the task is image classification... |
| n1 | draft | I will train a logistic regression classifier on flattened 32x32 RGB pixel values, which is a simple CPU-fr... (val 0.9477) |
| n2 | draft | Use a scikit-learn MLP classifier on flattened RGB pixel values, which is a simple CPU-only alternative to ... (val 0.9494) |
| n2 | card used | first script with MLPClassifier from the card "scikit-learn MLP classifier on pixel features" |
| n3 | draft | Use a scikit-learn HistGradientBoostingClassifier on PCA-reduced flattened RGB pixels, which is a tree-base... (val 0.9724) |
| n4 | draft | I will build a soft-voting ensemble of a logistic regression classifier on standardized raw RGB pixels and ... (val 0.9651) |
| n5 | new best | val 0.9979, probe 0.9958, 0.01% better than n0: Keep the same CNN architecture and training setup, but add test-time augmentation (TTA)... |
| n6 | new best | val 0.9987, probe 0.9979, 0.09% better than n5: Expand the test-time augmentation from the original plus horizontal flip to all four fl... |
| n7 | chain exhausted | the chain from n0 had 3 attempts without a real gain; the search moves elsewhere |
| n12 | new best | val 0.9989, probe 0.9991, 0.01% better than n6: Add a color histogram feature block computed from the normalized RGB images. For each i... |
| n13 | new best | val 0.9991, probe 0.9995, 0.02% better than n12: Add an HSV color histogram feature block to the existing HistGradientBoosting pipeline.... |
| n15 | new best | val 0.9991, probe 0.9995, 0.00% better than n13: Replace the single HistGradientBoosting fit with a 5-fold stratified cross-validated en... |
| n15 | chain exhausted | the chain from n11 had 3 attempts without a real gain; the search moves elsewhere |
| n17 | new best | val 0.9992, probe 0.9991, 0.01% better than n15: Add a frequency-domain feature block to the existing HistGradientBoosting pipeline. For... |
| n18 | new best | val 0.9992, probe 0.9992, 0.00% better than n17: Add a Haar wavelet feature block to the existing HistGradientBoosting pipeline. For eac... |
| n18 | chain exhausted | the chain from n14 had 3 attempts without a real gain; the search moves elsewhere |
| n26 | new best | val 0.9994, probe 0.9992, 0.02% better than n18: Add a Local Phase Quantization (LPQ) texture descriptor block to the existing HistGradi... |
| n27 | new best | val 0.9995, probe 0.9993, 0.01% better than n26: Add a color autocorrelogram feature block to the existing HistGradientBoosting pipeline... |
| n28 | new best | val 0.9996, probe 0.9993, 0.00% better than n27: Add a Color Coherence Vector (CCV) feature block to the existing HistGradientBoosting p... |
| n28 | chain exhausted | the chain from n25 had 3 attempts without a real gain; the search moves elsewhere |
| n39 | crash | runtime_error: ValueError: cannot reshape array of size 575 into shape (16,32) |
| n40 | fixed | debug fixed the crash in n39 after 1 attempt(s) |
| n47 | crash | runtime_error: SyntaxError: invalid decimal literal |
| n48 | fixed | debug fixed the crash in n47 after 1 attempt(s) |
| n49 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n28 | final pick | val 0.9996 (rank 1 of 47), test 0.9998 (rank 1 of 47) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
