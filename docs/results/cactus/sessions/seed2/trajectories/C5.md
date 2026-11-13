# Trajectory: C5_aerial-cactus-identification_seed2

- **Task** aerial-cactus-identification, **condition** C5, **seed** 2
- **Nodes** 45 (91% working), **budget used** 120.9 min, **LLM** 52 calls, 892,647 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** PyTorch CNN image classifier, scikit-learn MLP classifier, Soft voting ensemble for image classification, AdaBoost weak learner ensemble, PIL thumbnail preprocessing pipeline, Neural network hyperparameter tuning
- **Search** 7 improve chains exhausted; longest stretch without a new best 18 nodes; selection regret 0.0 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use a small custom PyTorch CNN on the 32x32 RGB images. Load all images into memory, normalize using traini... (val -) |
| n0 | crash | runtime_error: RuntimeError: Input type (double) and bias type (float) should be the same |
| n1 | draft | Use PIL to load and downsample each 32x32 image to 24x24 RGB, flatten to 1728 features, and standardize usi... (val 0.9663) |
| n1 | new best | val 0.9663, probe 0.9680: Use PIL to load and downsample each 32x32 image to 24x24 RGB, flatten to 1728 features,... |
| n1 | card used | first script with MLPClassifier from the card "scikit-learn MLP classifier" |
| n2 | draft | should not redefine. But then code block lacking first line. We can write: (val -) |
| n2 | crash | invalid_submission: predictions.csv not found |
| n3 | draft | Use a randomized PCA + logistic regression pipeline instead of the earlier CNN/MLP approaches. Load the 32x... (val 0.9396) |
| n4 | draft | Load all 32x32 RGB JPEGs, downsample them to 16x16, and flatten each into 768 normalized pixel features. Tr... (val 0.9562) |
| n6 | fixed | debug fixed the crash in n0 after 1 attempt(s) |
| n6 | new best | val 0.9993, probe 0.9993, 3.42% better than n1: The failure was caused by computing the normalization mean and standard deviation as fl... |
| n7 | fixed | debug fixed the crash in n2 after 1 attempt(s) |
| n8 | new best | val 0.9995, probe 0.9996, 0.01% better than n6: Add data augmentation to the CNN training loop by using a custom PyTorch Dataset that a... |
| n9 | new best | val 0.9995, probe 0.9995, 0.01% better than n8: Add test-time augmentation to the prediction function by averaging the model's logits o... |
| n10 | new best | val 0.9996, probe 0.9996, 0.00% better than n9: Extend test-time augmentation from the current four flips to all eight D4 symmetries (f... |
| n10 | chain exhausted | the chain from n6 had 3 attempts without a real gain; the search moves elsewhere |
| n25 | new best | val 0.9997, probe 0.9996, 0.02% better than n10: Add a DCT-based frequency feature block computed on the full-resolution 32x32 grayscale... |
| n26 | new best | val 0.9999, probe 0.9984, 0.02% better than n25: Extend the existing DCT-based frequency block to be color-aware by computing the same 8... |
| n27 | chain exhausted | the chain from n24 had 3 attempts without a real gain; the search moves elsewhere |
| n28 | crash | timeout: killed after 1200s |
| n29 | fixed | debug fixed the crash in n28 after 1 attempt(s) |
| n44 | crash | timeout: killed after 15s |
|  | stop | budget, final selection best_val |
| n26 | final pick | val 0.9999 (rank 1 of 41), test 0.9998 (rank 2 of 41) |
| n27 | best on test | test 0.9999, but val rank 2 of 41: Add per-channel color local binary pattern histograms computed on the full-resolution r... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
