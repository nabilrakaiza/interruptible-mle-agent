# Trajectory: A4-off_aerial-cactus-identification_seed1

- **Task** aerial-cactus-identification, **condition** A4-off, **seed** 1
- **Nodes** 36 (92% working), **budget used** 120.0 min, **LLM** 37 calls, 583,598 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** scikit-learn multi-layer perceptron classifier, Voting classifier with soft probability averaging, AdaBoost ensemble of shallow decision trees, PIL thumbnail preprocessing pipeline
- **Search** 5 improve chains exhausted; longest stretch without a new best 19 nodes; selection regret 0.0 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use a simple logistic-regression baseline on raw pixels. Load all 32x32 RGB images from the IDs in train.cs... (val 0.9458) |
| n0 | new best | val 0.9458, probe 0.9491: Use a simple logistic-regression baseline on raw pixels. Load all 32x32 RGB images from... |
| n1 | draft | Use a CPU-friendly PCA + MLP pipeline instead of a raw logistic-regression baseline. Load every image as a ... (val 0.9633) |
| n1 | new best | val 0.9633, probe 0.9537, 1.86% better than n0: Use a CPU-friendly PCA + MLP pipeline instead of a raw logistic-regression baseline. Lo... |
| n1 | card used | first script with MLPClassifier from the card "scikit-learn multi-layer perceptron classifier" |
| n2 | draft | Instead of linear or PCA-based baselines, I will use a bounded-depth random forest on normalized raw 32x32 ... (val 0.9747) |
| n2 | new best | val 0.9747, probe 0.9754, 1.18% better than n1: Instead of linear or PCA-based baselines, I will use a bounded-depth random forest on n... |
| n3 | draft | I will use a soft-voting ensemble of two CPU-friendly classifiers on a compact image representation: a regu... (val 0.9627) |
| n3 | card used | first script with VotingClassifier from the card "Voting classifier with soft probability averaging" |
| n4 | draft | Instead of the earlier sklearn baselines, I will train a small convolutional neural network from scratch in... (val 0.9927) |
| n4 | new best | val 0.9927, probe 0.9892, 1.85% better than n2: Instead of the earlier sklearn baselines, I will train a small convolutional neural net... |
| n7 | new best | val 0.9988, probe 0.9986, 0.62% better than n4: Change only the CNN feature extractor by adding a batch normalization layer after each ... |
| n8 | new best | val 0.9988, probe 0.9984, 0.00% better than n7: I will increase the number of training epochs from 6 to 12. The validation AUC was stil... |
| n9 | new best | val 0.9990, probe 0.9986, 0.01% better than n8: I will add four-way test-time augmentation to the validation and final prediction phase... |
| n10 | chain exhausted | the chain from n7 had 3 attempts without a real gain; the search moves elsewhere |
| n13 | new best | val 0.9995, probe 0.9990, 0.06% better than n9: Replace the raw-pixel random forest with a compact convolutional neural network trained... |
| n16 | new best | val 0.9998, probe 0.9996, 0.02% better than n13: Add weight-averaging via an exponential moving average (EMA) of the model parameters an... |
| n16 | chain exhausted | the chain from n13 had 3 attempts without a real gain; the search moves elsewhere |
| n17 | crash | runtime_error: ValueError: could not broadcast input array from shape (256,) into shape (59,) |
| n19 | fixed | debug fixed the crash in n17 after 1 attempt(s) |
| n27 | crash | runtime_error: TypeError: BCEWithLogitsLoss.__init__() got an unexpected keyword argument 'label_smoothing' |
| n29 | fixed | debug fixed the crash in n27 after 1 attempt(s) |
| n35 | crash | timeout: killed after 581s |
|  | stop | budget, final selection best_val |
| n16 | final pick | val 0.9998 (rank 1 of 33), test 0.9994 (rank 1 of 33) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
