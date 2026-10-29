# Trajectory: C6_leaf-classification_seed100

- **Task** leaf-classification, **condition** C6, **seed** 100
- **Nodes** 49 (90% working), **budget used** 120.9 min, **LLM** 55 calls, 1,169,791 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Temperature scaling calibrated classifier, SVM with precomputed kernel, Pipeline with nested parameter grid search, Gradient boosted trees with multiclass log-loss, AdaBoost ensemble of weak learners, Soft voting classifier, Calibrated classifier ensemble
- **Search** 6 improve chains exhausted; longest stretch without a new best 15 nodes; selection regret 0.0142 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Load the provided pre-extracted features from train.csv and predict.csv. Use a simple scikit-learn pipeline... (val 0.1746) |
| n0 | new best | val 0.1746, probe 0.2512: Load the provided pre-extracted features from train.csv and predict.csv. Use a simple s... |
| n1 | draft | I will build a soft-voting ensemble that combines a standardized multinomial logistic regression with a ran... (val 0.4804) |
| n2 | draft | Use the 192 precomputed features directly. Train a HistGradientBoostingClassifier with multiclass log loss,... (val 1.2072) |
| n3 | draft | Use the 192 precomputed leaf features directly. Train an ExtraTreesClassifier on a stratified training spli... (val 0.0685) |
| n3 | new best | val 0.0685, probe 0.4068, 60.77% better than n0: Use the 192 precomputed leaf features directly. Train an ExtraTreesClassifier on a stra... |
| n4 | draft | Build a stacking ensemble on the 192 precomputed leaf features. Base learners are a scaled logistic regress... (val 0.0438) |
| n4 | new best | val 0.0438, probe 0.1839, 36.05% better than n3: Build a stacking ensemble on the 192 precomputed leaf features. Base learners are a sca... |
| n7 | crash | runtime_error: ValueError: n_splits=10 cannot be greater than the number of members in each class. |
| n8 | fixed | debug fixed the crash in n7 after 1 attempt(s) |
| n8 | new best | val 0.0435, probe 0.1758, 0.65% better than n4: The previous script failed because the stacking ensemble used a 10-fold stratified CV, ... |
| n9 | new best | val 0.0430, probe 0.1862, 1.10% better than n8: Add a Linear Discriminant Analysis classifier with Ledoit-Wolf shrinkage as a fifth bas... |
| n10 | no-op | same predictions as n9: Increase the number of folds in the stacking cross-validation from 5 to 10 when class c... |
| n11 | new best | val 0.0276, probe 0.1734, 35.90% better than n9: Add a compact set of hand-crafted image features extracted from the binary leaf images ... |
| n12 | crash | runtime_error: KeyError: 'Acer_Capillipes' |
| n13 | fixed | debug fixed the crash in n12 after 1 attempt(s) |
| n14 | crash | runtime_error: TypeError: only 0-dimensional arrays can be converted to Python scalars |
| n15 | fixed | debug fixed the crash in n14 after 1 attempt(s) |
| n15 | new best | val 0.0081, probe 0.1704, 70.70% better than n11: The runtime error was caused by incorrectly unpacking the result of `ndimage.label`: th... |
| n18 | new best | val 0.0060, probe 0.1319, 26.02% better than n15: Add compact histogram summary features derived from the three precomputed 64-bin featur... |
| n19 | new best | val 0.0019, probe 0.1998, 68.95% better than n18: Change the stacking ensemble's final estimator to also receive the original feature mat... |
| n22 | chain exhausted | the chain from n19 had 3 attempts without a real gain; the search moves elsewhere |
| n31 | no-op | same predictions as n28: Switch the stacking ensemble's internal cross-validation from 5-fold to 10-fold stratif... |
| n32 | new best | val 0.0010, probe 0.2318, 45.85% better than n19: Add a compact radial-distance histogram feature family to the hand-crafted image featur... |
| n33 | new best | val 0.0009, probe 0.1787, 11.90% better than n32: Add compact convexity-defect features to the hand-crafted image feature extractor. For ... |
| n36 | chain exhausted | the chain from n33 had 3 attempts without a real gain; the search moves elsewhere |
| n39 | crash | runtime_error: ValueError: operands could not be broadcast together with shapes (4,0) (1,18) |
| n40 | fixed | debug fixed the crash in n39 after 1 attempt(s) |
| n48 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n33 | final pick | val 0.0009 (rank 1 of 44), test 0.0261 (rank 7 of 44) |
| n42 | best on test | test 0.0119, but val rank 13 of 44: Add a HistGradientBoostingClassifier as a sixth base learner in the stacking ensemble. ... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
