# Trajectory: A4-off_random-acts-of-pizza_seed0

- **Task** random-acts-of-pizza, **condition** A4-off, **seed** 0
- **Nodes** 64 (94% working), **budget used** 242.3 min, **LLM** 67 calls, 1,284,095 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TF-IDF with linear classifier, Random forest with sigmoid probability calibration, Gradient boosted decision trees, AdaBoost with shallow trees, Calibrated classifier ensemble, N-gram text vectorization
- **Search** 13 improve chains exhausted; longest stretch without a new best 42 nodes; selection regret 0.0142 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft |  (val -) |
| n0 | crash | generation_error: empty reply |
| n1 | draft | Use TF-IDF on the request title and edit-aware request text to capture wording, combined with standardized ... (val 0.6353) |
| n1 | new best | val 0.6353, probe 0.6433: Use TF-IDF on the request title and edit-aware request text to capture wording, combine... |
| n2 | draft | I will build a hybrid feature set: TF-IDF on the combined request title and edit-aware body, reduced with T... (val 0.6477) |
| n2 | new best | val 0.6477, probe 0.6773, 1.96% better than n1: I will build a hybrid feature set: TF-IDF on the combined request title and edit-aware ... |
| n3 | draft | I will build a hybrid feature set: TF-IDF on the combined request title and edit-aware body, reduced with T... (val 0.6710) |
| n3 | new best | val 0.6710, probe 0.6833, 3.59% better than n2: I will build a hybrid feature set: TF-IDF on the combined request title and edit-aware ... |
| n4 | draft | I will build a hybrid feature set from the request title, edit-aware body, and subreddit list using TF-IDF ... (val -) |
| n4 | crash | runtime_error: TypeError: MLPClassifier.__init__() got an unexpected keyword argument 'class_weight' |
| n6 | fixed | debug fixed the crash in n4 after 1 attempt(s) |
| n7 | crash | runtime_error: AttributeError: 'HistGradientBoostingClassifier' object has no attribute 'best_iteration_' |
| n8 | fixed | debug fixed the crash in n7 after 1 attempt(s) |
| n9 | chain exhausted | the chain from n3 had 3 attempts without a real gain; the search moves elsewhere |
| n12 | overfitting | beat n11 on validation (0.6701 -> 0.6704) but got worse on test (0.6651 -> 0.6520) |
| n13 | new best | val 0.6720, probe 0.6962, 0.15% better than n3: I will add a set of engagement and reputation features derived from the existing reques... |
| n14 | new best | val 0.6845, probe 0.6898, 1.86% better than n13: I will add a character n-gram TF-IDF view of the request text. A second TfidfVectorizer... |
| n17 | chain exhausted | the chain from n14 had 3 attempts without a real gain; the search moves elsewhere |
| n21 | new best | val 0.6888, probe 0.6983, 0.62% better than n14: Use the unlabeled test requests when building the unsupervised text representations ins... |
| n22 | no-op | same predictions as n21: Add sign-aware logarithmic transformations of the skewed requester activity and account... |
| n24 | no-op | same predictions as n21: The current script ignores `unix_timestamp_of_request`, even though it is known at requ... |
| n24 | chain exhausted | the chain from n21 had 3 attempts without a real gain; the search moves elsewhere |
| n48 | no-op | same predictions as n45: I will add missing-value indicators to the numeric preprocessing. Several engineered ra... |
| n63 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n21 | final pick | val 0.6888 (rank 1 of 60), test 0.6553 (rank 29 of 60) |
| n29 | best on test | test 0.6695, but val rank 34 of 60: Add a TF-IDF plus TruncatedSVD representation of the requester's subreddit history. Eac... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
