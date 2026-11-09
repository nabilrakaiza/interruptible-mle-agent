# Trajectory: C5_aerial-cactus-identification_seed1

- **Task** aerial-cactus-identification, **condition** C5, **seed** 1
- **Nodes** 44 (91% working), **budget used** 120.2 min, **LLM** 50 calls, 729,445 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Scikit-learn multilayer perceptron, Soft voting ensemble of classifiers, AdaBoost with weak learners, Image preprocessing with thumbnails, Hyperparameter-tuned iterative training
- **Search** 8 improve chains exhausted; longest stretch without a new best 21 nodes; selection regret 0.0 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Load all 32x32 RGB images into normalized float tensors. Train a small convolutional neural network in PyTo... (val 0.9915) |
| n0 | new best | val 0.9915, probe 0.9877: Load all 32x32 RGB images into normalized float tensors. Train a small convolutional ne... |
| n1 | draft | Use a simple logistic regression on flattened 32x32 RGB pixels. Load the images into a NumPy array, scale p... (val 0.9464) |
| n2 | draft | Use a scikit-learn MLPClassifier on flattened 32x32 RGB pixels instead of a CNN or logistic regression. Loa... (val -) |
| n2 | crash | runtime_error: AttributeError: 'MLPClassifier' object has no attribute 'best_iter_' |
| n2 | card used | first script with MLPClassifier from the card "Scikit-learn multilayer perceptron" |
| n3 | draft | Use PCA to reduce flattened 32x32 RGB pixel vectors to a compact 100-dimensional representation. Train thre... (val 0.9256) |
| n4 | draft | Use compact handcrafted features instead of raw pixels or a CNN: per-channel color histograms, intensity hi... (val 0.9939) |
| n4 | new best | val 0.9939, probe 0.9950, 0.25% better than n0: Use compact handcrafted features instead of raw pixels or a CNN: per-channel color hist... |
| n5 | fixed | debug fixed the crash in n2 after 1 attempt(s) |
| n6 | new best | val 0.9954, probe 0.9968, 0.14% better than n4: Replace the simple soft-voting average with stacked generalization. Use 5-fold stratifi... |
| n7 | new best | val 0.9954, probe 0.9967, 0.01% better than n6: Add an ExtraTreesClassifier as a fourth diverse base model in the stacked ensemble. Ext... |
| n8 | new best | val 0.9988, probe 0.9987, 0.34% better than n7: Add a uniform Local Binary Pattern (LBP) histogram as an additional texture feature in ... |
| n9 | new best | val 0.9990, probe 0.9986, 0.02% better than n8: Add HSV color histograms and moments to the handcrafted feature extractor. Converting e... |
| n10 | new best | val 0.9990, probe 0.9987, 0.00% better than n9: Add downsampled RGB block means to the handcrafted feature extractor. Specifically, aft... |
| n11 | new best | val 0.9992, probe 0.9991, 0.03% better than n10: Add a multilayer perceptron classifier on the standardized handcrafted features as a fi... |
| n11 | chain exhausted | the chain from n8 had 3 attempts without a real gain; the search moves elsewhere |
| n30 | crash | runtime_error: ValueError: could not broadcast input array from shape (10,) into shape (9,) |
| n31 | fixed | debug fixed the crash in n30 after 1 attempt(s) |
| n33 | new best | val 0.9993, probe 0.9989, 0.00% better than n11: Add HSV color-space statistics and histograms to the handcrafted feature extractor. Con... |
| n34 | new best | val 0.9993, probe 0.9990, 0.00% better than n33: Add gray-level run-length matrix (GLRLM) texture features to the handcrafted feature ex... |
| n34 | chain exhausted | the chain from n31 had 3 attempts without a real gain; the search moves elsewhere |
| n42 | crash | runtime_error: ValueError: zero-dimensional arrays cannot be concatenated |
| n43 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n34 | final pick | val 0.9993 (rank 1 of 40), test 0.9993 (rank 1 of 40) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
