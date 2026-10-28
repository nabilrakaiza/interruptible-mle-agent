# Trajectory: C4_aerial-cactus-identification_seed0

- **Task** aerial-cactus-identification, **condition** C4, **seed** 0
- **Nodes** 39 (95% working), **budget used** 120.0 min, **LLM** 44 calls, 638,446 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Scikit-learn multi-layer perceptron classifier, Soft-voting ensemble of complementary classifiers, Pillow image resizing and attribute-check pipeline, AdaBoost ensemble of weak learners
- **Search** 7 improve chains exhausted; longest stretch without a new best 22 nodes; selection regret 0.0003 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Flatten and normalize every 32x32 RGB image into a 3072-element feature vector. Train a single logistic reg... (val 0.9454) |
| n0 | new best | val 0.9454, probe 0.9513: Flatten and normalize every 32x32 RGB image into a 3072-element feature vector. Train a... |
| n1 | draft | Use PyTorch to train a small convolutional neural network directly on 32x32 RGB cactus images. Load the lab... (val 0.9951) |
| n1 | new best | val 0.9951, probe 0.9960, 5.25% better than n0: Use PyTorch to train a small convolutional neural network directly on 32x32 RGB cactus ... |
| n2 | draft | Load all RGB thumbnails with Pillow, flatten them into 3072-dimensional feature vectors, and standardize ea... (val 0.9596) |
| n2 | card used | first script with MLPClassifier from the card "Scikit-learn multi-layer perceptron classifier" |
| n3 | draft | Instead of using raw flattened pixels, I extract compact features from each 32x32 RGB image: a 16x16 block-... (val 0.9951) |
| n3 | new best | val 0.9951, probe 0.9947, 0.00% better than n1: Instead of using raw flattened pixels, I extract compact features from each 32x32 RGB i... |
| n4 | draft | Use Pillow to resize each 32x32 RGB image down to a compact 16x16 RGB block and flatten those pixels into f... (val 0.9791) |
| n5 | new best | val 0.9976, probe 0.9976, 0.26% better than n3: I keep the current engineered-feature pipeline and soft-voting ensemble, but add a comp... |
| n6 | new best | val 0.9988, probe 0.9983, 0.12% better than n5: I add a compact HSV/greenness feature block to the existing engineered feature vector. ... |
| n7 | new best | val 0.9990, probe 0.9986, 0.01% better than n6: I add a multi-scale local binary pattern feature block to the existing engineered featu... |
| n8 | new best | val 0.9992, probe 0.9993, 0.02% better than n7: Add a Histogram of Oriented Gradients (HOG) feature block to the engineered feature ext... |
| n9 | chain exhausted | the chain from n6 had 3 attempts without a real gain; the search moves elsewhere |
| n16 | new best | val 0.9996, probe 0.9994, 0.04% better than n8: I will keep the existing compact CNN architecture, optimizer, and data-loading pipeline... |
| n19 | chain exhausted | the chain from n16 had 3 attempts without a real gain; the search moves elsewhere |
| n24 | crash | runtime_error: RuntimeError: result type Float can't be cast to the desired output type Long |
| n25 | fixed | debug fixed the crash in n24 after 1 attempt(s) |
| n38 | crash | timeout: killed after 633s |
|  | stop | budget, final selection best_val |
| n16 | final pick | val 0.9996 (rank 1 of 37), test 0.9994 (rank 4 of 37) |
| n23 | best on test | test 0.9997, but val rank 3 of 37: Keep the current compact residual CNN, training loop, optimizer, and horizontal-flip te... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
