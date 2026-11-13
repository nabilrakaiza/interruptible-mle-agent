# Trajectory: A4-off_random-acts-of-pizza_seed1

- **Task** random-acts-of-pizza, **condition** A4-off, **seed** 1
- **Nodes** 109 (94% working), **budget used** 241.0 min, **LLM** 117 calls, 2,676,580 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TF-IDF with logistic regression, Random forest with calibrated probabilities, Bagged tree ensemble, AdaBoost with weak learners, Gradient-boosted regression trees, N-gram text features for local word order
- **Search** 17 improve chains exhausted; longest stretch without a new best 30 nodes; selection regret 0.0 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will build a simple, robust classifier using TF-IDF features from the request title and body plus a handf... (val 0.6386) |
| n0 | new best | val 0.6386, probe 0.6453: I will build a simple, robust classifier using TF-IDF features from the request title a... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF with logistic regression" |
| n0 | card used | first script with TfidfVectorizer from the card "N-gram text features for local word order" |
| n1 | draft | I will build a text-plus-metadata model that is different from a plain TF-IDF logistic regression. I will v... (val 0.6303) |
| n1 | card used | first script with GradientBoostingClassifier, HistGradientBoostingClassifier from the card "Gradient-boosted regression trees" |
| n2 | draft | I will build a Random Forest classifier with sigmoid-calibrated probabilities. Text from the request title ... (val 0.7011) |
| n2 | new best | val 0.7011, probe 0.6582, 9.78% better than n0: I will build a Random Forest classifier with sigmoid-calibrated probabilities. Text fro... |
| n2 | card used | first script with RandomForestClassifier from the card "Random forest with calibrated probabilities" |
| n3 | draft | I will build a gradient-boosted classifier on a compact dense feature matrix. Text from the request title a... (val 0.6498) |
| n4 | draft |  (val -) |
| n4 | crash | generation_error: empty reply |
| n8 | chain exhausted | the chain from n2 had 3 attempts without a real gain; the search moves elsewhere |
| n10 | overfitting | beat n3 on validation (0.6498 -> 0.6509) but got worse on test (0.6869 -> 0.6707) |
| n11 | overfitting | beat n3 on validation (0.6498 -> 0.6506) but got worse on test (0.6869 -> 0.6551) |
| n17 | crash | generation_error: empty reply |
| n22 | overfitting | beat n21 on validation (0.6852 -> 0.6865) but got worse on test (0.6938 -> 0.6890) |
| n28 | new best | val 0.7017, probe 0.6783, 0.09% better than n2: Replace the fixed weighted average of HistGBM, RandomForest, and ExtraTrees with a 5-fo... |
| n31 | chain exhausted | the chain from n28 had 3 attempts without a real gain; the search moves elsewhere |
| n50 | card used | first script with AdaBoostClassifier from the card "AdaBoost with weak learners" |
| n52 | crash | runtime_error: IndexError: boolean index did not match indexed array along axis 0; size of axis is 1 but size of corresponding boolean axis is 403 |
| n55 | card used | first script with BaggingClassifier from the card "Bagged tree ensemble" |
| n59 | new best | val 0.7054, probe 0.6786, 0.53% better than n28: Add cyclical time features (sin and cos transforms of hour, day of week, and month) to ... |
| n60 | crash | runtime_error: IndexError: boolean index did not match indexed array along axis 0; size of axis is 1 but size of corresponding boolean axis is 403 |
| n61 | crash | runtime_error: AttributeError: 'coo_matrix' object has no attribute 'A1' |
| n64 | fixed | debug fixed the crash in n52 after 3 attempt(s) |
| n65 | chain exhausted | the chain from n59 had 3 attempts without a real gain; the search moves elsewhere |
| n79 | new best | val 0.7070, probe 0.6825, 0.23% better than n59: Enrich the subreddit-history target encoding block. Instead of a single smoothing stren... |
| n83 | chain exhausted | the chain from n79 had 3 attempts without a real gain; the search moves elsewhere |
| n86 | overfitting | beat n54 on validation (0.7007 -> 0.7016) but got worse on test (0.7062 -> 0.6990) |
| n108 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n79 | final pick | val 0.7070 (rank 1 of 103), test 0.7078 (rank 1 of 103) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
