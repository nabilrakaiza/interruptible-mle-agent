# Trajectory: C5_detecting-insults-in-social-commentary_seed4

- **Task** detecting-insults-in-social-commentary, **condition** C5, **seed** 4
- **Nodes** 112 (98% working), **budget used** 240.0 min, **LLM** 128 calls, 2,234,255 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Stochastic gradient descent linear classifiers on sparse text, TF-IDF text feature extraction pipeline, Calibrated random forest classifier, Sigmoid and isotonic probability calibration, Out-of-core naive Bayes for large text corpora, Stop word handling for style-sensitive text
- **Search** 19 improve chains exhausted; longest stretch without a new best 32 nodes; selection regret 0.0021 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use a TF-IDF vectorizer with word and character n-grams combined with a fast linear model (logistic regress... (val 0.8883) |
| n0 | new best | val 0.8883, probe 0.9171: Use a TF-IDF vectorizer with word and character n-grams combined with a fast linear mod... |
| n0 | card used | first script with TfidfVectorizer from the card "Stochastic gradient descent linear classifiers on sparse text" |
| n0 | card used | first script with TfidfVectorizer from the card "TF-IDF text feature extraction pipeline" |
| n0 | card used | first script with TfidfVectorizer from the card "Stop word handling for style-sensitive text" |
| n1 | draft | I will use a TF-IDF vectorizer with word and character n-grams combined with logistic regression, which is ... (val 0.8602) |
| n2 | draft | I will use a fast, robust text classifier built from character n-grams and a linear SGD logistic regression... (val 0.8732) |
| n3 | draft | I will use character n-gram features with a Complement Naive Bayes classifier, which is a different model f... (val 0.8511) |
| n4 | draft | I will use a HashingVectorizer to create word and word-pair features, followed by a TF-IDF transformer and ... (val 0.7262) |
| n8 | chain exhausted | the chain from n0 had 3 attempts without a real gain; the search moves elsewhere |
| n12 | new best | val 0.8933, probe 0.9191, 0.56% better than n0: Keep the existing hashed character+word SGD pipeline unchanged, but add a second comple... |
| n15 | chain exhausted | the chain from n12 had 3 attempts without a real gain; the search moves elsewhere |
| n36 | no-op | same predictions as n34: Add tunable FeatureUnion transformer weights to the existing grid search. The current m... |
| n42 | no-op | same predictions as n34: Keep the exact TF-IDF word+character logistic regression pipeline and its hyperparamete... |
| n44 | overfitting | beat n43 on validation (0.8899 -> 0.8904) but got worse on test (0.9065 -> 0.9038) |
| n45 | new best | val 0.8959, probe 0.9151, 0.29% better than n12: Keep the transductive TF-IDF word+character pipeline and the full-feature logistic regr... |
| n47 | card used | first script with RandomForestClassifier from the card "Calibrated random forest classifier" |
| n48 | new best | val 0.8970, probe 0.9167, 0.12% better than n45: Add lightweight temporal features from the Date column to the scaled SVD branch before ... |
| n50 | new best | val 0.8972, probe 0.9180, 0.02% better than n48: Expand the word TF-IDF n-gram range from (1,2) to (1,3) in the existing FeatureUnion. T... |
| n52 | new best | val 0.8994, probe 0.9124, 0.25% better than n50: Replace the single SVD semantic branch, which currently reduces the concatenated word+c... |
| n56 | new best | val 0.9003, probe 0.9146, 0.10% better than n52: Expand the character n-gram range from (2,5) to (2,7) in the character TF-IDF vectorize... |
| n59 | chain exhausted | the chain from n56 had 3 attempts without a real gain; the search moves elsewhere |
| n71 | overfitting | beat n43 on validation (0.8899 -> 0.8930) but got worse on test (0.9065 -> 0.9024) |
| n77 | card used | first script with GaussianNB from the card "Out-of-core naive Bayes for large text corpora" |
| n84 | new best | val 0.9036, probe 0.9198, 0.36% better than n56: Replace the fixed weighted rank-average fusion with a 5-fold stratified out-of-fold log... |
| n87 | new best | val 0.9054, probe 0.9158, 0.20% better than n84: Increase the dimensionality of the transductive SVD semantic features from 150 to 200 c... |
| n87 | overfitting | beat n84 on validation (0.9036 -> 0.9054) but got worse on test (0.9051 -> 0.9029) |
| n91 | new best | val 0.9060, probe 0.9161, 0.06% better than n87: Add pairwise interaction features of the rank-normalized out-of-fold predictions to the... |
| n91 | chain exhausted | the chain from n87 had 3 attempts without a real gain; the search moves elsewhere |
| n104 | new best | val 0.9108, probe 0.9231, 0.53% better than n91: Enrich the Date-derived features used by both the sparse logistic-regression branch and... |
| n105 | new best | val 0.9112, probe 0.9218, 0.05% better than n104: Extend the Date-derived temporal feature block from 8 to 10 columns by adding cyclic da... |
| n106 | new best | val 0.9127, probe 0.9224, 0.16% better than n105: Add a fifth base model to the out-of-fold stacking ensemble: an ExtraTreesClassifier tr... |
| n108 | crash | runtime_error: NameError: name 'temporal_features' is not defined |
| n109 | fixed | debug fixed the crash in n108 after 1 attempt(s) |
| n111 | crash | timeout: killed after 239s |
| n111 | chain exhausted | the chain from n106 had 3 attempts without a real gain; the search moves elsewhere |
|  | stop | budget, final selection best_val |
| n106 | final pick | val 0.9127 (rank 1 of 110), test 0.9074 (rank 13 of 110) |
| n37 | best on test | test 0.9095, but val rank 61 of 110: Add a complementary k-nearest-neighbors classifier on the same exact TF-IDF word/charac... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
