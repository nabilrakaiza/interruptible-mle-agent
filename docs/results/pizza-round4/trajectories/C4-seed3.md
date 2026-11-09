# Trajectory: C4_random-acts-of-pizza_seed3

- **Task** random-acts-of-pizza, **condition** C4, **seed** 3
- **Nodes** 83 (93% working), **budget used** 240.0 min, **LLM** 97 calls, 2,170,999 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** L2-normalized TF-IDF features, Bag-of-words with linear classifiers, Word n-grams for local ordering, Calibrated random forest probabilities, Gradient boosted trees, AdaBoost with weak decision trees, CalibratedClassifierCV ensemble, Sigmoid calibration for ranking metrics
- **Search** 14 improve chains exhausted; longest stretch without a new best 14 nodes; selection regret 0.0102 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will build a simple pipeline that combines TF-IDF features from request text, title, and subreddit histor... (val 0.6476) |
| n0 | new best | val 0.6476, probe 0.6458: I will build a simple pipeline that combines TF-IDF features from request text, title, ... |
| n0 | card used | first script with TfidfVectorizer from the card "L2-normalized TF-IDF features" |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Bag-of-words with linear classifiers" |
| n0 | card used | first script with TfidfVectorizer from the card "Word n-grams for local ordering" |
| n1 | draft | Build a two-model ensemble rather than a single TF-IDF logistic regression. A HashingVectorizer converts th... (val 0.6472) |
| n1 | card used | first script with GradientBoostingClassifier, HistGradientBoostingClassifier from the card "Gradient boosted trees" |
| n2 | draft | Instead of feeding raw sparse TF-IDF directly to a classifier, I build a compact dense text representation:... (val 0.6650) |
| n2 | new best | val 0.6650, probe 0.6474, 2.69% better than n0: Instead of feeding raw sparse TF-IDF directly to a classifier, I build a compact dense ... |
| n3 | draft | Build a two-model ensemble: a logistic regression on TF-IDF word 1- and 2-grams from the request title, tex... (val -) |
| n3 | crash | runtime_error: exit code 1 |
| n4 | draft | I will build a text-and-metadata model that differs from word-level TF-IDF baselines by using character n-g... (val 0.5710) |
| n5 | fixed | debug fixed the crash in n3 after 1 attempt(s) |
| n6 | new best | val 0.6667, probe 0.6489, 0.25% better than n2: Keep the existing TF-IDF + TruncatedSVD dense text representation and numeric metadata ... |
| n8 | new best | val 0.6918, probe 0.6784, 3.77% better than n6: Keep the existing TF-IDF + TruncatedSVD text representation and logistic regression pip... |
| n12 | chain exhausted | the chain from n8 had 3 attempts without a real gain; the search moves elsewhere |
| n18 | new best | val 0.6967, probe 0.6939, 0.70% better than n8: Replace the single HistGradientBoosting model with a small cross-validated ensemble: ke... |
| n19 | new best | val 0.6974, probe 0.6962, 0.10% better than n18: Fix the log1p transform so it is applied only to genuinely count-like non-negative meta... |
| n22 | chain exhausted | the chain from n19 had 3 attempts without a real gain; the search moves elsewhere |
| n26 | new best | val 0.7017, probe 0.6967, 0.61% better than n19: Add a RandomForestClassifier as a third, diverse ensemble member alongside the existing... |
| n26 | card used | first script with RandomForestClassifier from the card "Calibrated random forest probabilities" |
| n27 | new best | val 0.7027, probe 0.6948, 0.15% better than n26: Add an ExtraTreesClassifier as a fourth ensemble member alongside the existing HistGrad... |
| n30 | new best | val 0.7037, probe 0.6983, 0.13% better than n27: Add a classic GradientBoostingClassifier as a fifth ensemble member alongside HistGB, l... |
| n32 | crash | runtime_error: exit code 1 |
| n33 | crash | runtime_error: TypeError: StringMethods.count() got an unexpected keyword argument 'regex' |
| n35 | crash | generation_error: empty reply |
| n36 | new best | val 0.7043, probe 0.6998, 0.09% better than n30: Add character n-gram TF-IDF features reduced with TruncatedSVD as an additional dense t... |
| n36 | chain exhausted | the chain from n30 had 3 attempts without a real gain; the search moves elsewhere |
| n43 | crash | runtime_error: TypeError: AdaBoostClassifier.__init__() got an unexpected keyword argument 'algorithm' |
| n43 | card used | first script with AdaBoostClassifier from the card "AdaBoost with weak decision trees" |
| n45 | fixed | debug fixed the crash in n43 after 1 attempt(s) |
| n51 | new best | val 0.7044, probe 0.6960, 0.01% better than n36: Add a second dense text representation based on character n-gram TF-IDF features, reduc... |
| n54 | chain exhausted | the chain from n51 had 3 attempts without a real gain; the search moves elsewhere |
| n59 | no-op | same predictions as n56: Increase the TF-IDF vectorizer’s `max_features` from 60,000 to 100,000 while keeping `m... |
| n64 | new best | val 0.7045, probe 0.7001, 0.03% better than n51: Add local-time features derived from the requester's own timestamp (`unix_timestamp_of_... |
| n65 | chain exhausted | the chain from n60 had 3 attempts without a real gain; the search moves elsewhere |
| n69 | no-op | same predictions as n66: Switch the out-of-fold ensemble from 5-fold to 10-fold cross-validation. With 10 folds,... |
| n70 | new best | val 0.7053, probe 0.6813, 0.11% better than n64: Add three hand-crafted text features derived from the combined request text: counts of ... |
| n71 | new best | val 0.7086, probe 0.6804, 0.47% better than n70: Add a character n-gram TF-IDF representation of the combined request text, using `char_... |
| n73 | no-op | same predictions as n71: Replace the single 5-fold StratifiedKFold out-of-fold generation with a 2-repeat, 5-fol... |
| n74 | chain exhausted | the chain from n71 had 3 attempts without a real gain; the search moves elsewhere |
| n80 | new best | val 0.7135, probe 0.6775, 0.69% better than n71: Add a character n-gram TF-IDF representation of the combined request text, reduced with... |
| n82 | crash | timeout: killed after 51s |
|  | stop | budget, final selection best_val |
| n80 | final pick | val 0.7135 (rank 1 of 77), test 0.7060 (rank 26 of 77) |
| n55 | best on test | test 0.7162, but val rank 27 of 77: Add a character-level TF-IDF text representation to the existing dense feature matrix. ... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
