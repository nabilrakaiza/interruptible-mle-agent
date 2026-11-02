# Trajectory: A4-off_spooky-author-identification_seed2

- **Task** spooky-author-identification, **condition** A4-off, **seed** 2
- **Nodes** 43 (95% working), **budget used** 240.0 min, **LLM** 45 calls, 743,171 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Bag-of-words with linear classifiers, DictVectorizer with handcrafted token features, Feature hashing with streaming linear models, Tf-idf feature extraction with hyperparameter tuning, Out-of-core naive Bayes text classification, One-vs-rest probability calibration, Temperature scaling for multiclass softmax probabilities
- **Search** 2 improve chains exhausted; longest stretch without a new best 12 nodes; selection regret 0.0 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF word and bigram features with sublinear term frequencies to represent the sentences as sparse ve... (val 0.5774) |
| n0 | new best | val 0.5774, probe 0.5736: Use TF-IDF word and bigram features with sublinear term frequencies to represent the se... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Bag-of-words with linear classifiers" |
| n0 | card used | first script with TfidfVectorizer from the card "Tf-idf feature extraction with hyperparameter tuning" |
| n1 | draft | Use character n-gram TF-IDF features instead of word bigrams to capture stylistic punctuation, affixes, and... (val 0.5917) |
| n2 | draft | Use a feature-hashing pipeline on character n-grams instead of a vocabulary-based TF-IDF vectorizer. This c... (val 0.6210) |
| n2 | card used | first script with TfidfTransformer from the card "DictVectorizer with handcrafted token features" |
| n2 | card used | first script with HashingVectorizer, SGDClassifier, TfidfTransformer from the card "Feature hashing with streaming linear models" |
| n3 | draft | Use a sparse word-unigram TF-IDF representation with sublinear term frequencies, lowercasing, stop-word rem... (val 0.5240) |
| n3 | new best | val 0.5240, probe 0.5324, 9.24% better than n0: Use a sparse word-unigram TF-IDF representation with sublinear term frequencies, lowerc... |
| n4 | draft | Use TF-IDF word unigrams and bigrams with sublinear term frequency scaling to represent sentences. Train a ... (val 0.4943) |
| n4 | new best | val 0.4943, probe 0.4955, 5.67% better than n3: Use TF-IDF word unigrams and bigrams with sublinear term frequency scaling to represent... |
| n4 | card used | first script with MultinomialNB from the card "Out-of-core naive Bayes text classification" |
| n5 | new best | val 0.4827, probe 0.4871, 2.36% better than n4: Replace the MultinomialNB base estimator with ComplementNB, which estimates parameters ... |
| n6 | new best | val 0.4708, probe 0.4683, 2.46% better than n5: Add character n-gram TF-IDF features as a second feature block alongside the existing w... |
| n8 | new best | val 0.4602, probe 0.4614, 2.26% better than n6: Keep the same word+character TF-IDF FeatureUnion, ComplementNB base estimator, sigmoid ... |
| n9 | new best | val 0.4357, probe 0.4413, 5.31% better than n8: Replace the ComplementNB base estimator with a multiclass logistic regression (L2, lbfg... |
| n10 | crash | timeout: killed after 1200s |
| n12 | fixed | debug fixed the crash in n10 after 1 attempt(s) |
| n13 | new best | val 0.4249, probe 0.4302, 2.48% better than n9: Replace English stop-word removal in the word TF-IDF vectorizer with no stop-word filte... |
| n14 | no-op | same predictions as n13: Expand the C search grid for logistic regression to include larger regularization stren... |
| n15 | new best | val 0.4237, probe 0.4287, 0.29% better than n13: Increase the `max_df` cutoff from 0.8 to 1.0 in both the word and character TF-IDF vect... |
| n16 | new best | val 0.4135, probe 0.4214, 2.41% better than n15: Keep the existing word+character TF-IDF feature union and logistic regression pipeline,... |
| n17 | new best | val 0.4116, probe 0.4207, 0.46% better than n16: Change the word TF-IDF n-gram range from (1,2) to (1,3) so the model can capture common... |
| n18 | new best | val 0.3987, probe 0.4119, 3.14% better than n17: Add a post-hoc temperature scaling step to the existing calibrated logistic-regression ... |
| n21 | chain exhausted | the chain from n18 had 3 attempts without a real gain; the search moves elsewhere |
| n26 | no-op | same predictions as n22: Replace the single-best-C selection with a weighted ensemble of the five calibrated log... |
| n27 | no-op | same predictions as n23: Increase only the character TF-IDF vectorizer's vocabulary capacity from 100,000 to 200... |
| n31 | new best | val 0.3933, probe 0.3958, 1.34% better than n18: Add a calibrated ComplementNB model trained on the same word+character TF-IDF features ... |
| n32 | new best | val 0.3702, probe 0.3731, 5.87% better than n31: Tune the smoothing alpha of the ComplementNB model instead of fixing it at 1.0. The alp... |
| n33 | no-op | same predictions as n32: Refine the ensemble blend weight search from a coarse 0.1 step to a finer 0.02 step. Th... |
| n34 | new best | val 0.3690, probe 0.3704, 0.34% better than n32: Add a small block of handcrafted stylometric features to the existing FeatureUnion: sen... |
| n35 | new best | val 0.3683, probe 0.3700, 0.17% better than n34: Extend the handcrafted stylometric features in the existing stats block by adding type-... |
| n37 | new best | val 0.3683, probe 0.3700, 0.00% better than n35: Add a third model to the ensemble: a calibrated BernoulliNB that binarizes the TF-IDF f... |
| n38 | new best | val 0.3494, probe 0.3453, 5.14% better than n37: Replace the SLSQP convex weight search with a logistic-regression stacker. For each can... |
| n39 | new best | val 0.3491, probe 0.3457, 0.08% better than n38: Tune the regularization strength C of the logistic-regression stacker instead of using ... |
| n40 | new best | val 0.3429, probe 0.3392, 1.78% better than n39: Add a fourth base model to the stacking ensemble: a calibrated logistic regression trai... |
| n41 | new best | val 0.3428, probe 0.3390, 0.04% better than n40: Add a fifth base model to the stacking ensemble: a calibrated logistic regression train... |
| n42 | crash | timeout: killed after 405s |
|  | stop | budget, final selection best_val |
| n41 | final pick | val 0.3428 (rank 1 of 41), test 0.3472 (rank 2 of 41) |
| n40 | best on test | test 0.3471, but val rank 2 of 41: Add a fourth base model to the stacking ensemble: a calibrated logistic regression trai... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
