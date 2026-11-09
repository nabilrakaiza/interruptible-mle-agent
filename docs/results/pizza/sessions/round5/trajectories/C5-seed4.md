# Trajectory: C5_random-acts-of-pizza_seed4

- **Task** random-acts-of-pizza, **condition** C5, **seed** 4
- **Nodes** 95 (96% working), **budget used** 243.2 min, **LLM** 112 calls, 2,181,119 tokens
- **Interventions** 3 applied, 0 dropped
- **Model cards** Tf-idf text vectorization with linear classifier, Random forest with calibrated probabilities, Bag-of-words with encoding detection and linear models, Metadata-stripped text classification, Word n-gram text representation, Gradient boosted trees for tabular features, AdaBoost with weak decision trees, Calibrated classifier ensemble
- **Search** 17 improve chains exhausted; longest stretch without a new best 70 nodes; selection regret 0.0121 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use tf-idf features from the request title and cleaned request text, combined with a small set of request-t... (val 0.6029) |
| n0 | new best | val 0.6029, probe 0.6412: Use tf-idf features from the request title and cleaned request text, combined with a sm... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Tf-idf text vectorization with linear classifier" |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Bag-of-words with encoding detection and linear models" |
| n0 | card used | first script with TfidfVectorizer from the card "Metadata-stripped text classification" |
| n0 | card used | first script with TfidfVectorizer from the card "Word n-gram text representation" |
| n1 | draft | I will build a gradient-boosted tree model on request-time metadata plus hand-crafted text features. This a... (val 0.6501) |
| n1 | new best | val 0.6501, probe 0.6779, 7.83% better than n0: I will build a gradient-boosted tree model on request-time metadata plus hand-crafted t... |
| n1 | card used | first script with GradientBoostingClassifier, HistGradientBoostingClassifier from the card "Gradient boosted trees for tabular features" |
| n2 | draft | I will build a simple ensemble of two complementary models: a logistic regression on tf-idf word and word-p... (val 0.6482) |
| n2 | card used | first script with RandomForestClassifier from the card "Random forest with calibrated probabilities" |
| n3 | draft | I will build a random forest on a low-dimensional text representation created by tf-idf plus truncated SVD,... (val 0.6539) |
| n3 | new best | val 0.6539, probe 0.6619, 0.58% better than n1: I will build a random forest on a low-dimensional text representation created by tf-idf... |
| n4 | draft | I will use a text-only approach based on tf-idf features and a Complement Naive Bayes classifier. The title... (val 0.5168) |
| n5 | new best | val 0.6776, probe 0.6714, 3.63% better than n3: I will add the requester's subreddit history at request time as an extra text signal. T... |
| n10 | chain exhausted | the chain from n5 had 3 attempts without a real gain; the search moves elsewhere |
| n13 | crash | runtime_error: SyntaxError: invalid syntax |
| n14 | intervention | finding_correction: correct f-c1dedbc9c5, applied - C5: 1 of 1 cited nodes failed to replicate: n6 val +0.04254, probe -0.009324 vs n0 |
| n15 | fixed | debug fixed the crash in n13 after 1 attempt(s) |
| n18 | new best | val 0.6793, probe 0.6671, 0.26% better than n5: Replace the linear classifier with a random forest trained on SVD-reduced tf-idf text t... |
| n21 | new best | val 0.7055, probe 0.6597, 3.86% better than n18: The current best script uses a random forest on SVD-reduced word 1-2 gram tf-idf featur... |
| n24 | new best | val 0.7066, probe 0.6694, 0.15% better than n21: Extend the word n-gram range from (1,3) to (1,4) and raise max_features to 200000 so th... |
| n24 | overfitting | beat n21 on validation (0.7055 -> 0.7066) but got worse on test (0.6861 -> 0.6740) |
| n24 | intervention | finding_correction: correct f-e4d3e94b20, applied - C5: 1 of 2 cited nodes failed to replicate: n22 val -0.02704, probe +0.003922 vs n21 |
| n28 | chain exhausted | the chain from n24 had 3 attempts without a real gain; the search moves elsewhere |
| n29 | overfitting | beat n21 on validation (0.7055 -> 0.7066) but got worse on test (0.6861 -> 0.6740) |
| n64 | crash | generation_error: empty reply |
| n74 | intervention | finding_correction: correct f-ec28c5ab15, applied - C5: 1 of 2 cited nodes failed to replicate: n34 val -0.05657, probe +0.0144 vs n29 |
| n80 | crash | generation_error: empty reply |
| n94 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n24 | final pick | val 0.7066 (rank 1 of 91), test 0.6740 (rank 8 of 91) |
| n21 | best on test | test 0.6861, but val rank 3 of 91: The current best script uses a random forest on SVD-reduced word 1-2 gram tf-idf featur... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
