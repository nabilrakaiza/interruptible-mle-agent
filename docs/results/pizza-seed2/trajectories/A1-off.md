# Trajectory: A1-off_random-acts-of-pizza_seed2

- **Task** random-acts-of-pizza, **condition** A1-off, **seed** 2
- **Nodes** 84 (95% working), **budget used** 240.0 min, **LLM** 93 calls, 2,234,847 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TF-IDF text vectorization with linear classifier, Sparse bag-of-words pipeline, Random forest with calibrated probabilities, Metadata-stripping text preprocessing, N-gram text features, Gradient boosted trees, AdaBoost ensemble, Sigmoid calibration that preserves ranking
- **Search** 14 improve chains exhausted; longest stretch without a new best 22 nodes; selection regret 0.0086 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF bigram features on the request title plus body text, combined with numeric metadata features (ac... (val 0.6654) |
| n0 | new best | val 0.6654, probe 0.6357: Use TF-IDF bigram features on the request title plus body text, combined with numeric m... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF text vectorization with linear classifier" |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Sparse bag-of-words pipeline" |
| n0 | card used | first script with TfidfVectorizer from the card "Metadata-stripping text preprocessing" |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "N-gram text features" |
| n1 | draft | Use a random forest instead of the earlier logistic-regression baseline. Combine request title, body, and s... (val 0.6675) |
| n1 | new best | val 0.6675, probe 0.6372, 0.32% better than n0: Use a random forest instead of the earlier logistic-regression baseline. Combine reques... |
| n1 | card used | first script with RandomForestClassifier from the card "Random forest with calibrated probabilities" |
| n2 | draft | Build a regularized logistic-regression model on sparse text features combining word unigrams/bigrams and c... (val 0.6880) |
| n2 | new best | val 0.6880, probe 0.6797, 3.07% better than n1: Build a regularized logistic-regression model on sparse text features combining word un... |
| n3 | draft | Use a hashing-based sparse text representation instead of TF-IDF to keep the pipeline simple and memory-saf... (val 0.5853) |
| n4 | draft | Use a sparse TF-IDF unigram+bigram representation of the request title, edit-aware body, and parsed subredd... (val 0.5852) |
| n5 | no-op | same predictions as n2: Keep the existing feature engineering and TF-IDF pipeline, but replace the fixed regula... |
| n6 | new best | val 0.6947, probe 0.6961, 0.98% better than n2: Add a random-forest model trained on the request-time numeric metadata and blend its pr... |
| n9 | card used | first script with GradientBoostingClassifier, HistGradientBoostingClassifier from the card "Gradient boosted trees" |
| n10 | chain exhausted | the chain from n6 had 3 attempts without a real gain; the search moves elsewhere |
| n11 | overfitting | beat n7 on validation (0.6883 -> 0.6899) but got worse on test (0.6920 -> 0.6787) |
| n13 | new best | val 0.6956, probe 0.6796, 0.13% better than n6: Replace the single logistic-regression classifier with a bootstrap-aggregated logistic ... |
| n15 | new best | val 0.6972, probe 0.6775, 0.24% better than n13: Keep the entire feature pipeline and validation protocol unchanged, and make only the b... |
| n16 | new best | val 0.7003, probe 0.6614, 0.44% better than n15: Add sine/cosine cyclical encodings of the timestamp components (hour, day-of-week, and ... |
| n17 | new best | val 0.7003, probe 0.6611, 0.01% better than n16: Add a continuous timestamp feature, "timestamp_days" (days since Unix epoch), to the nu... |
| n18 | new best | val 0.7080, probe 0.6962, 1.10% better than n17: Add a RandomForestClassifier trained on the numeric metadata block (including timestamp... |
| n20 | new best | val 0.7100, probe 0.6913, 0.29% better than n18: Add a compact dense text representation to the random forest by fitting a word TF-IDF v... |
| n21 | new best | val 0.7114, probe 0.6895, 0.19% better than n20: Add a second dense text representation to the random forest by projecting character n-g... |
| n22 | no-op | same predictions as n21: Add a HistGradientBoostingClassifier trained on the same dense feature matrix used by t... |
| n23 | no-op | same predictions as n21: Add a rank/quantile-normalized blending path in addition to the existing raw-probabilit... |
| n24 | new best | val 0.7168, probe 0.6825, 0.75% better than n21: Add a Non-negative Matrix Factorization topic model as an additional dense text represe... |
| n27 | chain exhausted | the chain from n24 had 3 attempts without a real gain; the search moves elsewhere |
| n31 | new best | val 0.7246, probe 0.6914, 1.09% better than n24: Add a block of requester-activity ratio and derived-karma features to the shared numeri... |
| n32 | new best | val 0.7253, probe 0.6894, 0.09% better than n31: Switch the random forest's class weighting from the global `balanced` setting to `balan... |
| n33 | no-op | same predictions as n32: Add a logit-scale blending path for combining the bagged logistic-regression and random... |
| n34 | no-op | same predictions as n32: Add an ExtraTreesClassifier trained on the same dense feature matrix (numeric metadata ... |
| n34 | chain exhausted | the chain from n31 had 3 attempts without a real gain; the search moves elsewhere |
| n39 | no-op | same predictions as n37: Add a compact neural-network branch to the existing ensemble. The MLP is trained on the... |
| n49 | new best | val 0.7257, probe 0.6972, 0.06% better than n32: Add derived account-creation date features to the numeric feature set: account_created_... |
| n52 | chain exhausted | the chain from n49 had 3 attempts without a real gain; the search moves elsewhere |
| n53 | new best | val 0.7290, probe 0.7002, 0.45% better than n49: Fit all unsupervised text feature extractors (TF-IDF, CountVectorizer, TruncatedSVD, an... |
| n56 | chain exhausted | the chain from n53 had 3 attempts without a real gain; the search moves elsewhere |
| n58 | new best | val 0.7309, probe 0.7032, 0.26% better than n53: Add a smoothed leave-one-out target encoding of the requester's prior subreddit history... |
| n60 | new best | val 0.7341, probe 0.6979, 0.44% better than n58: Add two smoothed leave-one-out target encodings of the request title and request body w... |
| n61 | new best | val 0.7345, probe 0.6937, 0.05% better than n60: Add smoothed leave-one-out target encodings of word bigrams from the request title and ... |
| n63 | chain exhausted | the chain from n60 had 3 attempts without a real gain; the search moves elsewhere |
| n65 | crash | runtime_error: ValueError: could not convert string to float: "[Request] Hungry University student Tucson, AZ I've been down on my luck lately. I have a... |
| n66 | crash | runtime_error: NameError: name 'val_auc_rf' is not defined. Did you mean: 'val_auc_lr'? |
| n69 | fixed | debug fixed the crash in n66 after 1 attempt(s) |
| n73 | fixed | debug fixed the crash in n65 after 1 attempt(s) |
| n79 | no-op | same predictions as n57: Add an ExtraTreesClassifier as a third model in the ensemble, trained on the same dense... |
| n82 | crash | runtime_error: TypeError: Cannot clone object '<__main__.FrozenVectorizer object at 0x7b27263ee660>' (type <class '__main__.FrozenVectorizer'>): it does... |
| n83 | crash | timeout: killed after 72s |
|  | stop | budget, final selection best_val |
| n61 | final pick | val 0.7345 (rank 1 of 80), test 0.6899 (rank 33 of 80) |
| n21 | best on test | test 0.6985, but val rank 53 of 80: Add a second dense text representation to the random forest by projecting character n-g... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
