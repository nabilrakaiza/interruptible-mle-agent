# Trajectory: C5_random-acts-of-pizza_seed3

- **Task** random-acts-of-pizza, **condition** C5, **seed** 3
- **Nodes** 109 (97% working), **budget used** 240.2 min, **LLM** 124 calls, 2,979,584 tokens
- **Interventions** 2 applied, 0 dropped
- **Model cards** TF-IDF with linear text classifier, N-gram bag of words with linear model, Random forest with sigmoid calibration, Gradient boosted trees, AdaBoost with shallow decision trees, Sigmoid-calibrated probability pipeline, Calibrated classifier ensemble, Metadata-stripped text classification
- **Search** 19 improve chains exhausted; longest stretch without a new best 34 nodes; selection regret 0.0028 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft |  (val -) |
| n0 | crash | generation_error: empty reply |
| n1 | draft | I will build a simple pipeline that combines TF-IDF features from the request title and edit-aware request ... (val 0.6055) |
| n1 | new best | val 0.6055, probe 0.6345: I will build a simple pipeline that combines TF-IDF features from the request title and... |
| n1 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF with linear text classifier" |
| n1 | card used | first script with LogisticRegression, TfidfVectorizer from the card "N-gram bag of words with linear model" |
| n1 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Metadata-stripped text classification" |
| n2 | draft | Instead of the earlier linear TF-IDF approach, I will use a gradient-boosted tree classifier on a compact d... (val 0.6380) |
| n2 | new best | val 0.6380, probe 0.6816, 5.36% better than n1: Instead of the earlier linear TF-IDF approach, I will use a gradient-boosted tree class... |
| n2 | card used | first script with GradientBoostingClassifier, HistGradientBoostingClassifier from the card "Gradient boosted trees" |
| n3 | draft | I will use a random forest classifier, which is a different model family from the earlier linear and gradie... (val 0.6502) |
| n3 | new best | val 0.6502, probe 0.6816, 1.91% better than n2: I will use a random forest classifier, which is a different model family from the earli... |
| n3 | card used | first script with RandomForestClassifier from the card "Random forest with sigmoid calibration" |
| n4 | draft | I will build a soft-voting ensemble of two complementary models. The first is a logistic regression on TF-I... (val 0.6253) |
| n5 | new best | val 0.6618, probe 0.6860, 1.79% better than n3: Add one-hot indicator features for the 50 most common subreddits in the requester's pos... |
| n7 | new best | val 0.6644, probe 0.7041, 0.40% better than n5: Add SVD-based subreddit embedding features computed from the full subreddit membership ... |
| n7 | overfitting | beat n5 on validation (0.6618 -> 0.6644) but got worse on test (0.6876 -> 0.6694) |
| n10 | new best | val 0.6754, probe 0.6937, 1.65% better than n7: Add normalized ratio and interaction features derived from the existing request-time me... |
| n10 | overfitting | beat n5 on validation (0.6618 -> 0.6754) but got worse on test (0.6876 -> 0.6780) |
| n13 | new best | val 0.6802, probe 0.7170, 0.71% better than n10: Add a block of activity-rate and log-transformed engagement features derived from the e... |
| n15 | new best | val 0.6812, probe 0.7012, 0.14% better than n13: Add non-negative matrix factorization (NMF) topic features computed from the same TF-ID... |
| n18 | new best | val 0.6832, probe 0.6970, 0.30% better than n15: Retune the random forest by changing max_features from "sqrt" to 0.3 and increasing n_e... |
| n21 | new best | val 0.6852, probe 0.6816, 0.29% better than n18: Replace the RandomForestClassifier with an ExtraTreesClassifier, keeping the exact same... |
| n22 | new best | val 0.6894, probe 0.6818, 0.62% better than n21: Replace the fixed ExtraTrees hyperparameters with a small validation-driven search. I w... |
| n23 | new best | val 0.6916, probe 0.6744, 0.32% better than n22: Enable bootstrap sampling in the ExtraTrees classifier to decorrelate individual trees ... |
| n25 | new best | val 0.6968, probe 0.6757, 0.76% better than n23: Add max_samples=0.8 to the ExtraTreesClassifier base parameters. This makes each tree t... |
| n27 | no-op | same predictions as n26: I will keep the feature pipeline and base ExtraTrees parameters unchanged, and only bro... |
| n28 | chain exhausted | the chain from n25 had 3 attempts without a real gain; the search moves elsewhere |
| n30 | new best | val 0.6971, probe 0.6833, 0.04% better than n25: Add low-dimensional TruncatedSVD embeddings of the full subreddit membership matrix as ... |
| n32 | chain exhausted | the chain from n29 had 3 attempts without a real gain; the search moves elsewhere |
| n44 | new best | val 0.6981, probe 0.6794, 0.14% better than n30: Expand the ExtraTrees hyperparameter search with a finer grid around the current best c... |
| n44 | intervention | finding_correction: correct f-c7551bcba7, applied - C5: 1 of 2 cited nodes failed to replicate: n20 val -0.03175, probe +0.001286 vs n18 |
| n45 | no-op | same predictions as n44: I will expand the ExtraTrees hyperparameter search to include the entropy split criteri... |
| n47 | chain exhausted | the chain from n44 had 3 attempts without a real gain; the search moves elsewhere |
| n48 | no-op | same predictions as n43: Replace the ExtraTrees hyperparameter search grid with a finer grid centered on the cur... |
| n51 | no-op | same predictions as n23: I will add a `min_samples_split` hyperparameter search centered on the current best Ext... |
| n56 | no-op | same predictions as n52: Replace the single 80/20 train/validation split used for ExtraTrees hyperparameter sele... |
| n62 | no-op | same predictions as n23: Add a logistic regression model trained on the raw TF-IDF text features plus standardiz... |
| n65 | new best | val 0.6991, probe 0.6872, 0.15% better than n44: Add a set of binary keyword indicators derived from the combined request title and body... |
| n67 | new best | val 0.7041, probe 0.6899, 0.72% better than n65: Add a binary feature `username_contains_throwaway` that flags requester usernames conta... |
| n70 | chain exhausted | the chain from n67 had 3 attempts without a real gain; the search moves elsewhere |
| n71 | new best | val 0.7050, probe 0.6804, 0.12% better than n67: Add a small block of structural request-formatting features derived from the request te... |
| n72 | no-op | same predictions as n71: Add a HistGradientBoostingClassifier as a second candidate model trained on the same fe... |
| n74 | new best | val 0.7181, probe 0.6824, 1.87% better than n71: Add calendar features derived from the request timestamp: year, month, day-of-month, an... |
| n77 | chain exhausted | the chain from n74 had 3 attempts without a real gain; the search moves elsewhere |
| n90 | overfitting | beat n5 on validation (0.6618 -> 0.6730) but got worse on test (0.6876 -> 0.6593) |
| n96 | overfitting | beat n81 on validation (0.6503 -> 0.6606) but got worse on test (0.6553 -> 0.6303) |
| n100 | crash | runtime_error: ValueError: Found input variables with inconsistent numbers of samples: [403, 5] |
| n101 | fixed | debug fixed the crash in n100 after 1 attempt(s) |
| n104 | intervention | finding_correction: correct f-3937a6b539, applied - C5: 1 of 1 cited nodes failed to replicate: n100 buggy |
| n108 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n74 | final pick | val 0.7181 (rank 1 of 106), test 0.6907 (rank 4 of 106) |
| n77 | best on test | test 0.6935, but val rank 20 of 106: Enable bootstrap sampling with max_samples=0.8 in the ExtraTreesClassifier. The current... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
