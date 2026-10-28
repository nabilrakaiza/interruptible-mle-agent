# Trajectory: C1_aerial-cactus-identification_seed2

- **Task** aerial-cactus-identification, **condition** C1, **seed** 2
- **Nodes** 26 (81% working), **budget used** 120.0 min, **LLM** 32 calls, 556,852 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** PyTorch CNN image classifier trained from scratch, Scikit-learn multi-layer perceptron baseline, Soft voting ensemble of diverse classifiers, AdaBoost ensemble of weak image-feature learners, Image resizing and thumbnail preprocessing pipeline, Neural network hyperparameter tuning loop, MLP classifier with probability outputs
- **Search** 4 improve chains exhausted; longest stretch without a new best 17 nodes; selection regret 0.0002 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Load the labeled training images and unlabeled prediction images into memory as normalized float arrays. Tr... (val 0.9991) |
| n0 | new best | val 0.9991, probe 0.9993: Load the labeled training images and unlabeled prediction images into memory as normali... |
| n1 | draft | I will use a scikit-learn MLP classifier instead of a CNN. Each image is resized to a 16x16 RGB thumbnail, ... (val 0.9692) |
| n1 | card used | first script with MLPClassifier from the card "Scikit-learn multi-layer perceptron baseline" |
| n1 | card used | first script with MLPClassifier from the card "MLP classifier with probability outputs" |
| n2 | draft | I will use a soft-voting ensemble of a logistic regression and a random forest trained on raw pixel feature... (val 0.9687) |
| n3 | draft | I will use a gradient-boosted tree ensemble (HistGradientBoostingClassifier) on compact hand-crafted image ... (val -) |
| n3 | crash | runtime_error: TypeError: HistGradientBoostingClassifier.__init__() got an unexpected keyword argument 'n_jobs' |
| n4 | draft | I will use a principal component analysis (PCA) plus logistic regression pipeline on raw pixel features. Al... (val 0.9388) |
| n5 | new best | val 0.9991, probe 0.9992, 0.00% better than n0: I will keep the CNN training pipeline exactly as is, but improve inference by adding te... |
| n6 | fixed | debug fixed the crash in n3 after 1 attempt(s) |
| n8 | new best | val 0.9991, probe 0.9989, 0.00% better than n5: I will replace the current two-view test-time augmentation (original + horizontal flip)... |
| n8 | chain exhausted | the chain from n0 had 3 attempts without a real gain; the search moves elsewhere |
| n20 | crash | runtime_error: RuntimeError: weights.ndim (2) must match len(axes) (3) |
| n21 | crash | generation_error: empty reply |
| n24 | crash | timeout: killed after 1200s |
| n25 | crash | timeout: killed after 968s |
|  | stop | budget, final selection best_val |
| n8 | final pick | val 0.9991 (rank 1 of 21), test 0.9992 (rank 5 of 21) |
| n23 | best on test | test 0.9994, but val rank 5 of 21: Replace the plain convolutional network with a residual CNN with batch normalization an... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
