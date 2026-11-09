# Trajectory: C6_detecting-insults-in-social-commentary_seed100

- **Task** detecting-insults-in-social-commentary, **condition** C6, **seed** 100
- **Nodes** 60 (87% working), **budget used** 120.0 min, **LLM** 67 calls, 1,301,659 tokens
- **Interventions** 8 applied, 0 dropped
- **Model cards** Random forest with probability calibration, HashingVectorizer with a linear classifier, N-gram features with careful stop-word handling, Bag-of-words with fast linear models, SGD linear models for large-scale text, CalibratedClassifierCV for probability estimates, Naive Bayes with out-of-core partial fit, Benchmarking text classification pipelines
- **Search** 11 improve chains exhausted; longest stretch without a new best 10 nodes; selection regret 0.0035 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Clean comment fields by stripping the CSV-level double-quote wrapper and normalizing common escape sequence... (val 0.8664) |
| n0 | card used | first script with TfidfVectorizer from the card "Random forest with probability calibration" |
| n0 | card used | first script with LogisticRegression from the card "HashingVectorizer with a linear classifier" |
| n0 | card used | first script with TfidfVectorizer from the card "N-gram features with careful stop-word handling" |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Bag-of-words with fast linear models" |
| n1 | draft | Instead of a TF-IDF vocabulary model, use a fixed HashingVectorizer with word and punctuation tokens and 1-... (val 0.8596) |
| n1 | card used | first script with SGDClassifier from the card "SGD linear models for large-scale text" |
| n2 | draft | Use character n-grams instead of word-level features so the model captures subword patterns, spelling varia... (val 0.8878) |
| n3 | draft | This solution uses a count-based bag-of-ngrams representation rather than TF-IDF or hashing. It cleans the ... (val 0.8071) |
| n4 | draft | Clean the CSV-quoted comment fields with `ast.literal_eval` plus a safe fallback for escaped text and unico... (val 0.7696) |
| n4 | new best | val 0.7696, probe 0.8072: Clean the CSV-quoted comment fields with `ast.literal_eval` plus a safe fallback for es... |
| n4 | card used | first script with MultinomialNB from the card "Naive Bayes with out-of-core partial fit" |
| n5 | new best | val 0.8898, probe 0.9168, 15.62% better than n4: Keep the robust comment-decoding logic but replace the MultinomialNB word-only model wi... |
| n7 | new best | val 0.8900, probe 0.9243, 0.03% better than n5: Add an internal cross-validation step to select the L2 regularization strength C for th... |
| n8 | new best | val 0.8912, probe 0.9269, 0.13% better than n7: Add a log-transformed comment length feature to the logistic regression, since insults ... |
| n9 | new best | val 0.8929, probe 0.9278, 0.19% better than n8: Change only the word-level TF-IDF n-gram range from unigrams+bigrams to unigrams+bigram... |
| n14 | new best | val 0.8932, probe 0.9280, 0.03% better than n9: Use balanced class weights in the logistic regression. The training labels are imbalanc... |
| n14 | chain exhausted | the chain from n9 had 3 attempts without a real gain; the search moves elsewhere |
| n18 | new best | val 0.8959, probe 0.9320, 0.30% better than n14: Add a date/time feature block to the logistic regression input: for each row, a missing... |
| n20 | intervention | human: prune n3, applied - Far behind with no path up: raw word+char counts with ComplementNB, val 0.807 vs best 0.893 (n14); TF-IDF + logistic regression drafts are clearly better. No children, never improved. Prune so exploration doesn’t spend a node on it. |
| n22 | new best | val 0.8976, probe 0.9278, 0.19% better than n18: Add TruncatedSVD semantic features to the current logistic-regression pipeline. After f... |
| n25 | chain exhausted | the chain from n22 had 3 attempts without a real gain; the search moves elsewhere |
| n25 | intervention | human: redirect n2 {"operator": "improve"}, applied - Exploration check, one step: n2 (char-only TF-IDF + LR, val 0.888) is the best draft and has never been improved. The leading line plateaued n9–n17 before n18/n22; try n2 once to see whether that branch can catch up. Deliberate exception to oversight-only. |
| n28 | overfitting | beat n8 on validation (0.8912 -> 0.8949) but got worse on test (0.9096 -> 0.9042) |
| n30 | new best | val 0.9000, probe 0.9343, 0.28% better than n22: Add a local co-occurrence surface feature that counts second-person pronouns appearing ... |
| n32 | no-op | same predictions as n30: The existing L2 regularization grid stops at C=10.0, and the cross-validation picks tha... |
| n33 | chain exhausted | the chain from n30 had 3 attempts without a real gain; the search moves elsewhere |
| n34 | new best | val 0.9006, probe 0.9368, 0.06% better than n30: Add a local co-occurrence feature block to the existing surface features: for every sec... |
| n37 | new best | val 0.9079, probe 0.9402, 0.82% better than n34: Add a temporal feature block to the current best pipeline, which currently ignores the ... |
| n38 | new best | val 0.9080, probe 0.9400, 0.00% better than n37: Add a direct bigram surface feature that detects a second-person pronoun immediately fo... |
| n39 | intervention | human: inject {"card": "One-off experiment, try once only: keep n37\u2019s feature pipeline exactly (word 1\u20133 + char_wb 2\u20135 TF-IDF, log length, surface features, and the date features) and replace the logistic regression with a gradient-boosting or random-forest model, within the 20-minute limit. If it doesn\u2019t beat n37 on validation, keep using logistic regression."}, applied |
| n39 | intervention | human: redirect n37 {"operator": "improve"}, applied - Apply the injected one-off experiment to the current best node (n37): same features, more complex model (boosting or random forest), to see whether a non-linear model adds anything over logistic regression. |
| n40 | new best | val 0.9080, probe 0.9397, 0.00% better than n38: Add a negation-aware surface feature block to the current pipeline. Many comments conta... |
| n40 | chain exhausted | the chain from n37 had 3 attempts without a real gain; the search moves elsewhere |
| n45 | new best | val 0.9091, probe 0.9373, 0.12% better than n40: Add a second unsupervised semantic feature block to the current best pipeline. In addit... |
| n47 | new best | val 0.9093, probe 0.9378, 0.02% better than n45: Add an obfuscation-aware insult lexicon feature block. For every lexicon word, compile ... |
| n47 | intervention | human: prune n0, applied - Separate draft branch, 0.02–0.04 behind the best (n45, 0.909) with ~35 min left; stop exploration from spending nodes on it. |
| n47 | intervention | human: prune n1, applied - Separate draft branch, 0.02–0.04 behind the best (n45, 0.909) with ~35 min left; stop exploration from spending nodes on it. |
| n47 | intervention | human: prune n2, applied - Separate draft branch, 0.02–0.04 behind the best (n45, 0.909) with ~35 min left; stop exploration from spending nodes on it. |
| n49 | new best | val 0.9101, probe 0.9356, 0.09% better than n47: Add a third-person pronoun disambiguation block to the existing surface features. The c... |
| n49 | chain exhausted | the chain from n45 had 3 attempts without a real gain; the search moves elsewhere |
| n55 | no-op | same predictions as n34: Change only the comment-cleaning step to repair UTF-8 byte sequences that were decoded ... |
| n58 | intervention | human: override n37, applied - Final pick by probe instead of validation: since n37, validation crept up (n45–n49, +0.002) while the probe fell (−0.005). n37 has the run’s highest probe (0.9402) at val 0.9079; trust the held-out probe over small validation gains on the SVD branch. |
| n59 | crash | timeout: killed after 158s |
|  | stop | budget, final selection override |
| n37 | final pick | val 0.9079 (rank 9 of 52), test 0.9087 (rank 14 of 52) |
| n17 | best on test | test 0.9122, but val rank 35 of 52: Keep the existing cleaning, TF-IDF features, log-length feature, and L2-regularized log... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
