# Trajectory: A4-off_random-acts-of-pizza_seed2

- **Task** random-acts-of-pizza, **condition** A4-off, **seed** 2
- **Nodes** 67 (92% working), **budget used** 241.0 min, **LLM** 68 calls, 1,500,635 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TF-IDF text vectorization with linear classifier, Metadata-stripping text preprocessing, Random forest probability calibration, Bagging meta-estimator for high-variance models, Gradient boosted regression trees, AdaBoost with reweighted weak learners, Sigmoid calibration for ranking metrics, Calibrated classifier ensemble per class
- **Search** 11 improve chains exhausted; longest stretch without a new best 27 nodes; selection regret 0.0071 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will combine the request title, edit-aware request body, and requester subreddit history into a single te... (val 0.6305) |
| n0 | new best | val 0.6305, probe 0.6400: I will combine the request title, edit-aware request body, and requester subreddit hist... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF text vectorization with linear classifier" |
| n1 | draft | I will use two separate TF-IDF vectorizers for the request title and the edit-aware request body so each fi... (val 0.6431) |
| n1 | new best | val 0.6431, probe 0.6501, 2.00% better than n0: I will use two separate TF-IDF vectorizers for the request title and the edit-aware req... |
| n2 | draft | I will build a different model from the earlier TF-IDF-plus-logistic drafts by projecting TF-IDF text featu... (val 0.6272) |
| n2 | card used | first script with GradientBoostingClassifier from the card "Gradient boosted regression trees" |
| n3 | draft | I will represent each request as TF-IDF n-grams from the title, the edit-aware body, and the requester's hi... (val 0.6985) |
| n3 | new best | val 0.6985, probe 0.6666, 8.62% better than n1: I will represent each request as TF-IDF n-grams from the title, the edit-aware body, an... |
| n3 | card used | first script with RandomForestClassifier from the card "Random forest probability calibration" |
| n4 | draft | I will combine the request title, edit-aware request body, and requester subreddit history into one text fi... (val -) |
| n4 | crash | runtime_error: ValueError: assignment destination is read-only |
| n5 | crash | runtime_error: TypeError: StringMethods.count() got an unexpected keyword argument 'regex' |
| n6 | fixed | debug fixed the crash in n4 after 1 attempt(s) |
| n7 | fixed | debug fixed the crash in n5 after 1 attempt(s) |
| n9 | chain exhausted | the chain from n3 had 3 attempts without a real gain; the search moves elsewhere |
| n10 | crash | leakage: R3_val_in_training (line 274): holdout_model is evaluated on validation rows it was fitted on (fit at line 267) |
| n13 | fixed | debug fixed the crash in n10 after 1 attempt(s) |
| n17 | crash | runtime_error: TypeError: KNeighborsClassifier.fit() got an unexpected keyword argument 'sample_weight' |
| n20 | fixed | debug fixed the crash in n17 after 1 attempt(s) |
| n24 | overfitting | beat n16 on validation (0.6883 -> 0.6897) but got worse on test (0.6814 -> 0.6719) |
| n26 | overfitting | beat n24 on validation (0.6897 -> 0.6949) but got worse on test (0.6719 -> 0.6633) |
| n31 | new best | val 0.6988, probe 0.6737, 0.04% better than n3: I will add one new out-of-fold stacking feature to the final model: a nonlinear RBF-ker... |
| n32 | new best | val 0.7012, probe 0.6777, 0.34% better than n31: I will add two out-of-fold smoothed target-encoding features derived from `requester_su... |
| n34 | new best | val 0.7023, probe 0.6691, 0.16% better than n32: I will expand the subreddit target-encoding features from two summary statistics to a r... |
| n35 | new best | val 0.7050, probe 0.6673, 0.39% better than n34: I will keep the entire feature-engineering and training pipeline unchanged, and only en... |
| n36 | new best | val 0.7058, probe 0.6735, 0.12% better than n35: Add a new out-of-fold stacking feature from a small neural network (MLP) to the final m... |
| n39 | chain exhausted | the chain from n36 had 3 attempts without a real gain; the search moves elsewhere |
| n60 | new best | val 0.7090, probe 0.6777, 0.45% better than n36: Replace the final single random forest with a two-model ensemble: keep the existing ran... |
| n63 | new best | val 0.7109, probe 0.6833, 0.27% better than n60: Add an ExtraTreesClassifier as a third member of the final ensemble and average its pre... |
| n66 | crash | timeout: killed after 1s |
| n66 | chain exhausted | the chain from n63 had 3 attempts without a real gain; the search moves elsewhere |
|  | stop | budget, final selection best_val |
| n63 | final pick | val 0.7109 (rank 1 of 62), test 0.6822 (rank 7 of 62) |
| n65 | best on test | test 0.6893, but val rank 7 of 62: Add a new out-of-fold stacking feature from a logistic regression trained on character ... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
