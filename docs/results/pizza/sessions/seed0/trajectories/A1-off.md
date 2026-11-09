# Trajectory: A1-off_random-acts-of-pizza_seed0

- **Task** random-acts-of-pizza, **condition** A1-off, **seed** 0
- **Nodes** 28 (93% working), **budget used** 240.0 min, **LLM** 34 calls, 914,545 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Text preprocessing to strip message metadata, Word n-grams for local ordering, Bag-of-words with linear classifier, AdaBoost with weak decision trees, Gradient-boosted trees, Random forest with calibrated probabilities, Ranking-preserving sigmoid calibration, Cross-validation calibrated classifier ensemble
- **Search** 4 improve chains exhausted; longest stretch without a new best 8 nodes; selection regret 0.0074 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will build a simple text + numeric model. Text is formed from the request title and the edit-aware reques... (val 0.6564) |
| n0 | new best | val 0.6564, probe 0.6313: I will build a simple text + numeric model. Text is formed from the request title and t... |
| n0 | card used | first script with TfidfVectorizer from the card "Text preprocessing to strip message metadata" |
| n0 | card used | first script with TfidfVectorizer from the card "Word n-grams for local ordering" |
| n0 | card used | first script with LogisticRegression from the card "Bag-of-words with linear classifier" |
| n0 | card used | first script with TfidfVectorizer from the card "Cross-validation calibrated classifier ensemble" |
| n1 | draft | I will build a fast logistic-regression baseline. Text from the title and edit-aware body is converted to T... (val 0.6439) |
| n2 | draft | I'll build a hybrid model that combines a TF-IDF logistic regression on the request title and edit-aware bo... (val 0.6957) |
| n2 | new best | val 0.6957, probe 0.6885, 5.98% better than n0: I'll build a hybrid model that combines a TF-IDF logistic regression on the request tit... |
| n2 | card used | first script with GradientBoostingClassifier, HistGradientBoostingClassifier from the card "Gradient-boosted trees" |
| n3 | draft | I will build a dense feature matrix by combining request-time numeric metadata, simple text-length features... (val 0.6869) |
| n4 | draft |  (val -) |
| n4 | crash | generation_error: empty reply |
| n5 | new best | val 0.6994, probe 0.6725, 0.54% better than n2: Add one-hot indicators for the 100 most frequent subreddits in the requester's posting ... |
| n6 | new best | val 0.7023, probe 0.6694, 0.40% better than n5: I will replace the fixed 50/50 ensemble weight with a weight tuned on the held-out vali... |
| n7 | new best | val 0.7067, probe 0.6809, 0.63% better than n6: Add a character n-gram TF-IDF logistic model trained on the same request text. Characte... |
| n8 | new best | val 0.7149, probe 0.6956, 1.16% better than n7: Add derived ratio features to the numeric metadata block: comments/posts per account da... |
| n9 | no-op | same predictions as n8: Add a Complement Naive Bayes text model on the same word TF-IDF features as an addition... |
| n11 | new best | val 0.7164, probe 0.6876, 0.21% better than n8: Add a block of hand-crafted lexical and content features to the numeric metadata block:... |
| n12 | new best | val 0.7199, probe 0.6974, 0.49% better than n11: Add a random forest classifier as a fourth ensemble member, trained on the same imputed... |
| n12 | card used | first script with RandomForestClassifier from the card "Random forest with calibrated probabilities" |
| n13 | new best | val 0.7207, probe 0.7020, 0.11% better than n12: Add a fifth ensemble member: a TF-IDF logistic regression trained on the request title ... |
| n16 | chain exhausted | the chain from n13 had 3 attempts without a real gain; the search moves elsewhere |
| n18 | new best | val 0.7217, probe 0.6999, 0.14% better than n13: Add requester-username-derived features to the numeric feature block consumed by the hi... |
| n19 | new best | val 0.7231, probe 0.6896, 0.18% better than n18: Add a sixth ensemble member: a TF-IDF logistic regression trained on the request body a... |
| n21 | no-op | same predictions as n19: Add a seventh ensemble member: a logistic regression on binary (presence/absence) TF-ID... |
| n22 | no-op | same predictions as n19: Add a seventh ensemble member: a logistic regression on word 1-3 gram TF-IDF features o... |
| n22 | chain exhausted | the chain from n19 had 3 attempts without a real gain; the search moves elsewhere |
| n27 | crash | timeout: killed after 213s |
|  | stop | budget, final selection best_val |
| n19 | final pick | val 0.7231 (rank 1 of 26), test 0.6700 (rank 19 of 26) |
| n1 | best on test | test 0.6774, but val rank 26 of 26: I will build a fast logistic-regression baseline. Text from the title and edit-aware bo... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
