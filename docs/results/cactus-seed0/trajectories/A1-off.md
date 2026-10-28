# Trajectory: A1-off_aerial-cactus-identification_seed0

- **Task** aerial-cactus-identification, **condition** A1-off, **seed** 0
- **Nodes** 22 (91% working), **budget used** 120.0 min, **LLM** 25 calls, 418,400 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** PyTorch Convolutional Neural Network, Scikit-learn Multi-layer Perceptron, Soft Voting Ensemble of Classifiers, AdaBoost with Shallow Decision Trees, PIL Image Resizing Preprocessing, Hyperparameter Tuning for Neural Training
- **Search** 3 improve chains exhausted; longest stretch without a new best 6 nodes; selection regret 0.0 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will use a simple linear baseline that is fast and reliable on CPU: load the 32x32 RGB images, flatten th... (val 0.9368) |
| n0 | new best | val 0.9368, probe 0.9451: I will use a simple linear baseline that is fast and reliable on CPU: load the 32x32 RG... |
| n1 | draft | I will train a compact convolutional neural network from scratch in PyTorch on the 32x32 RGB images, using ... (val 0.9996) |
| n1 | new best | val 0.9996, probe 0.9994, 6.71% better than n0: I will train a compact convolutional neural network from scratch in PyTorch on the 32x3... |
| n2 | draft | I will use a nonlinear scikit-learn baseline based on principal components of downsampled images: resize ea... (val 0.9610) |
| n2 | card used | first script with MLPClassifier from the card "Scikit-learn Multi-layer Perceptron" |
| n3 | draft | Use a Random Forest classifier on downsampled color thumbnails. Load all images, resize each 32x32 JPEG to ... (val 0.9704) |
| n4 | draft | I will use a gradient-boosted tree model (HistGradientBoostingClassifier) on downsampled 16x16 RGB thumbnai... (val 0.9794) |
| n5 | new best | val 0.9996, probe 0.9994, 0.00% better than n1: I will keep the compact CNN and the original training procedure unchanged, but add test... |
| n6 | new best | val 0.9997, probe 0.9993, 0.00% better than n5: I will keep the compact CNN architecture and training procedure unchanged, but replace ... |
| n7 | new best | val 0.9997, probe 0.9996, 0.00% better than n6: I will add random D4 data augmentation (a random 90-degree rotation and a random horizo... |
| n7 | chain exhausted | the chain from n1 had 3 attempts without a real gain; the search moves elsewhere |
| n12 | crash | runtime_error: exit code 137 (killed, most likely out of memory: the limit is 4 GB) |
| n13 | fixed | debug fixed the crash in n12 after 1 attempt(s) |
| n13 | new best | val 0.9998, probe 0.9998, 0.01% better than n7: Replace the memory-heavy HistGradientBoosting pipeline with a compact CNN trained from ... |
| n15 | new best | val 0.9999, probe 0.9999, 0.01% better than n13: Replace the single best-epoch checkpoint with a snapshot ensemble of the top-3 training... |
| n16 | chain exhausted | the chain from n13 had 3 attempts without a real gain; the search moves elsewhere |
| n21 | crash | timeout: killed after 910s |
|  | stop | budget, final selection best_val |
| n15 | final pick | val 0.9999 (rank 1 of 20), test 0.9997 (rank 2 of 20) |
| n16 | best on test | test 0.9997, but val rank 2 of 20: Replace the D4 test-time augmentation probability averaging with logit averaging. Inste... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
