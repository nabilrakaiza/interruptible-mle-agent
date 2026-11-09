# Trajectory: C1_random-acts-of-pizza_seed4

- **Task** random-acts-of-pizza, **condition** C1, **seed** 4
- **Nodes** 80 (92% working), **budget used** 241.4 min, **LLM** 95 calls, 2,460,778 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Tf-idf plus linear text classifier, Random forest with calibrated probabilities, Bag-of-words linear text pipeline, Metadata-stripping text preprocessing, Word and phrase n-gram features, Gradient boosted decision trees, Sigmoid calibration for ranking metrics, AdaBoost with small decision trees
- **Search** 13 improve chains exhausted; longest stretch without a new best 50 nodes; selection regret 0.0021 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft |  (val -) |
| n0 | crash | generation_error: empty reply |
| n1 | draft | I will build a simple text-plus-metadata pipeline. Request titles and bodies are combined and vectorized wi... (val 0.6442) |
| n1 | new best | val 0.6442, probe 0.6413: I will build a simple text-plus-metadata pipeline. Request titles and bodies are combin... |
| n1 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Tf-idf plus linear text classifier" |
| n1 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Bag-of-words linear text pipeline" |
| n1 | card used | first script with TfidfVectorizer from the card "Word and phrase n-gram features" |
| n2 | draft | Instead of relying on a single logistic regression on raw text, I will build a TF-IDF representation of the... (val 0.6823) |
| n2 | new best | val 0.6823, probe 0.6611, 5.91% better than n1: Instead of relying on a single logistic regression on raw text, I will build a TF-IDF r... |
| n2 | card used | first script with RandomForestClassifier from the card "Random forest with calibrated probabilities" |
| n3 | draft |  (val -) |
| n3 | crash | generation_error: empty reply |
| n4 | draft | I will use a histogram gradient boosted tree model on a compact feature set rather than a linear model or r... (val 0.6294) |
| n4 | card used | first script with GradientBoostingClassifier, HistGradientBoostingClassifier from the card "Gradient boosted decision trees" |
| n5 | new best | val 0.6825, probe 0.6732, 0.03% better than n2: Augment the text representation with character n-gram TF-IDF features in addition to th... |
| n7 | new best | val 0.6906, probe 0.6817, 1.18% better than n5: Replace the fixed 50/50 blend of logistic regression and random forest with a data-driv... |
| n10 | new best | val 0.6951, probe 0.6974, 0.65% better than n7: Replace the single concatenated TF-IDF text representation with separate TF-IDF vectori... |
| n13 | new best | val 0.7011, probe 0.7116, 0.87% better than n10: Add a set of normalized activity/engagement features to the numeric feature matrix. The... |
| n14 | new best | val 0.7020, probe 0.7081, 0.12% better than n13: Add an ExtraTrees classifier as a third ensemble member, trained on the same SVD-reduce... |
| n15 | new best | val 0.7040, probe 0.7035, 0.29% better than n14: Add an L1-regularized logistic regression as a fourth ensemble member, trained on the s... |
| n16 | new best | val 0.7053, probe 0.6990, 0.19% better than n15: Replace the grid-search convex blend with a logistic-regression meta-learner trained on... |
| n18 | new best | val 0.7055, probe 0.6992, 0.02% better than n16: Add a fifth base model: a logistic regression trained only on the standardized numeric/... |
| n21 | chain exhausted | the chain from n16 had 3 attempts without a real gain; the search moves elsewhere |
| n23 | new best | val 0.7080, probe 0.6946, 0.36% better than n18: Replace the coarse grid-search blend weights with a logistic-regression stacking meta-l... |
| n25 | new best | val 0.7132, probe 0.6898, 0.74% better than n23: Add a multilayer perceptron classifier as a fifth base model in the stacking ensemble. ... |
| n26 | new best | val 0.7134, probe 0.6897, 0.03% better than n25: Add a Gaussian Naive Bayes classifier as a sixth base model in the stacking ensemble. I... |
| n27 | new best | val 0.7147, probe 0.6898, 0.18% better than n26: Add a K-nearest neighbors classifier as a seventh base model in the stacking ensemble. ... |
| n29 | new best | val 0.7151, probe 0.6838, 0.07% better than n27: Add a Linear Discriminant Analysis classifier as an eighth base model in the stacking e... |
| n31 | chain exhausted | the chain from n27 had 3 attempts without a real gain; the search moves elsewhere |
| n33 | overfitting | beat n4 on validation (0.6294 -> 0.6533) but got worse on test (0.6841 -> 0.6511) |
| n43 | card used | first script with AdaBoostClassifier from the card "AdaBoost with small decision trees" |
| n64 | crash | runtime_error: TypeError: AdaBoostClassifier.__init__() got an unexpected keyword argument 'algorithm' |
| n65 | crash | runtime_error: TypeError: LinearDiscriminantAnalysis.fit() got an unexpected keyword argument 'sample_weight' |
| n66 | fixed | debug fixed the crash in n64 after 1 attempt(s) |
| n67 | crash | generation_error: empty reply |
| n79 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n29 | final pick | val 0.7151 (rank 1 of 74), test 0.7007 (rank 9 of 74) |
| n69 | best on test | test 0.7027, but val rank 47 of 74: Augment the stacking meta-learner's feature matrix with a small set of informative nume... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
