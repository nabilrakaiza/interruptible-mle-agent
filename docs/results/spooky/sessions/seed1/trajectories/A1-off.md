# Trajectory: A1-off_spooky-author-identification_seed1

- **Task** spooky-author-identification, **condition** A1-off, **seed** 1
- **Nodes** 56 (98% working), **budget used** 120.0 min, **LLM** 63 calls, 1,077,925 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Tfidf sparse features with linear classifiers, Multinomial naive Bayes on bag-of-words, Temperature scaling for multiclass probability calibration, Feature hashing with linear text classifiers, Out-of-core text classification with partial_fit
- **Search** 1 improve chains exhausted; longest stretch without a new best 5 nodes; selection regret 0.0234 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use a TF-IDF vectorizer with sublinear term frequencies, English stop words, and unigram+bigram features to... (val 0.6052) |
| n0 | new best | val 0.6052, probe 0.6080: Use a TF-IDF vectorizer with sublinear term frequencies, English stop words, and unigra... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Tfidf sparse features with linear classifiers" |
| n0 | card used | first script with TfidfVectorizer from the card "Multinomial naive Bayes on bag-of-words" |
| n0 | card used | first script with LogisticRegression from the card "Feature hashing with linear text classifiers" |
| n1 | draft | Use feature hashing with unigram+bigram sparse text features, followed by TF-IDF-style scaling with subline... (val 0.8268) |
| n1 | card used | first script with HashingVectorizer, SGDClassifier from the card "Out-of-core text classification with partial_fit" |
| n2 | draft | Use a simple bag-of-words Naive Bayes pipeline instead of linear TF-IDF/hashing models. CountVectorizer pro... (val 0.5056) |
| n2 | new best | val 0.5056, probe 0.4937, 16.47% better than n0: Use a simple bag-of-words Naive Bayes pipeline instead of linear TF-IDF/hashing models.... |
| n3 | draft | I’ll use character n-gram TF-IDF features (char_wb, 2-grams through 5-grams) rather than the earlier word-l... (val 0.5167) |
| n4 | draft | I’ll build a simple ensemble of two TF-IDF logistic-regression pipelines: one using word unigrams+bigrams a... (val 0.5179) |
| n5 | new best | val 0.4211, probe 0.4151, 16.70% better than n2: I will replace the single character TF-IDF logistic regression with a small ensemble th... |
| n6 | new best | val 0.4204, probe 0.4146, 0.18% better than n5: I keep the same two base models and the same 80/20 stratified holdout, but replace the ... |
| n7 | new best | val 0.4112, probe 0.4039, 2.19% better than n6: I will add a third base model, a character n-gram bag-of-words Multinomial Naive Bayes ... |
| n8 | new best | val 0.4059, probe 0.3971, 1.27% better than n7: I will keep the existing three-model pipeline and the class-specific blend. After compu... |
| n9 | no-op | same predictions as n8: I will tune the smoothing alpha of both MultinomialNB models on the validation split in... |
| n11 | new best | val 0.4034, probe 0.3921, 0.62% better than n8: Replace the scalar temperature scaling with per-class vector scaling: each class gets i... |
| n12 | new best | val 0.3739, probe 0.3704, 7.31% better than n11: Add a fourth base model to the ensemble: a word-count Multinomial Naive Bayes model tha... |
| n14 | new best | val 0.3598, probe 0.3582, 3.78% better than n12: Add two Naive Bayes variants to the word-count feature space: ComplementNB on the no-st... |
| n15 | new best | val 0.3562, probe 0.3550, 1.00% better than n14: Add two diverse Naive Bayes base models that reuse the existing character n-gram count ... |
| n16 | new best | val 0.3562, probe 0.3550, 0.00% better than n15: Add a ninth base model that uses a dense semantic representation: word-level TF-IDF fea... |
| n18 | chain exhausted | the chain from n15 had 3 attempts without a real gain; the search moves elsewhere |
| n22 | new best | val 0.3232, probe 0.3339, 9.25% better than n16: Replace the hand-tuned per-class convex blend plus vector scaling with a regularized mu... |
| n24 | new best | val 0.3168, probe 0.3216, 1.99% better than n22: Add one diverse base model to the current stacking ensemble: ComplementNB trained on th... |
| n25 | new best | val 0.3143, probe 0.3208, 0.80% better than n24: Add a tenth base model to the ensemble: MultinomialNB trained on the existing character... |
| n26 | new best | val 0.3128, probe 0.3203, 0.49% better than n25: Add an eleventh base model to the ensemble: ComplementNB trained on the existing stop-w... |
| n27 | new best | val 0.3078, probe 0.3149, 1.58% better than n26: Add a twelfth base model to the ensemble: a case-preserving character n-gram TF-IDF log... |
| n28 | new best | val 0.3071, probe 0.3144, 0.24% better than n27: Add a thirteenth base model to the ensemble: a case-preserving character n-gram Multino... |
| n29 | new best | val 0.3040, probe 0.3118, 1.00% better than n28: Add a fourteenth base model to the stacking ensemble: a Bernoulli Naive Bayes model on ... |
| n30 | new best | val 0.2924, probe 0.3016, 3.83% better than n29: Add a fifteenth base model to the stacking ensemble: BernoulliNB on case-preserving wor... |
| n31 | new best | val 0.2908, probe 0.3028, 0.53% better than n30: Add a sixteenth base model to the stacking ensemble: MultinomialNB on the case-preservi... |
| n32 | new best | val 0.2882, probe 0.3016, 0.92% better than n31: Add a seventeenth base model to the stacking ensemble: a case-preserving word-level TF-... |
| n33 | new best | val 0.2846, probe 0.3024, 1.22% better than n32: The current ensemble already contains several char_wb n-gram models, but char_wb pads w... |
| n34 | new best | val 0.2828, probe 0.3025, 0.65% better than n33: Add one diverse base model to the stack: a lowercased word n-gram CountVectorizer with ... |
| n35 | new best | val 0.2816, probe 0.3019, 0.41% better than n34: Add one diverse base model to the stack: ComplementNB on the existing case-preserving c... |
| n36 | new best | val 0.2808, probe 0.3027, 0.29% better than n35: Add one more base model to the stacking ensemble: BernoulliNB on the existing case-pres... |
| n37 | new best | val 0.2802, probe 0.3027, 0.22% better than n36: Add one more diverse base model to the stacking ensemble: ComplementNB on the existing ... |
| n38 | new best | val 0.2787, probe 0.3031, 0.55% better than n37: Add one more diverse base model to the existing stacking ensemble: a ComplementNB train... |
| n41 | new best | val 0.2767, probe 0.3034, 0.69% better than n38: Add one diverse base model to the stacking ensemble: a ComplementNB trained on a case-p... |
| n42 | new best | val 0.2731, probe 0.3012, 1.30% better than n41: Add a hashed word/punctuation logistic regression as a new diverse base model. A Hashin... |
| n43 | new best | val 0.2721, probe 0.3003, 0.39% better than n42: Add a character-level hashing logistic regression as a new diverse base model. A Hashin... |
| n44 | new best | val 0.2542, probe 0.3085, 6.59% better than n43: The current stacker feeds only log probabilities to the logistic meta-model. I will cha... |
| n44 | overfitting | beat n43 on validation (0.2721 -> 0.2542) but got worse on test (0.3144 -> 0.3257) |
| n45 | new best | val 0.2513, probe 0.3110, 1.11% better than n44: Add one new base model to the stacking ensemble: a MultinomialNB trained on the existin... |
| n46 | new best | val 0.2502, probe 0.3107, 0.47% better than n45: Add one new base model to the stacking ensemble: a ComplementNB trained on a case-prese... |
| n47 | new best | val 0.2482, probe 0.3107, 0.78% better than n46: Add two new base models to the stacking ensemble that reuse the already-computed raw ch... |
| n48 | new best | val 0.2462, probe 0.3107, 0.79% better than n47: Add a new base model to the stacking ensemble: a hashed, case-preserving raw character ... |
| n49 | new best | val 0.2369, probe 0.2963, 3.79% better than n48: Add a new base model to the stacking ensemble: a case-preserving hashed word/punctuatio... |
| n50 | new best | val 0.2319, probe 0.2946, 2.13% better than n49: Add a new base model to the stacking ensemble: case-preserving raw character n-gram cou... |
| n51 | new best | val 0.2310, probe 0.2934, 0.38% better than n50: Add a new base model to the stacking ensemble: ComplementNB trained on the already-comp... |
| n52 | new best | val 0.2291, probe 0.2941, 0.82% better than n51: Add a BernoulliNB base model on the already-computed lowercased word 2-4 n-gram count m... |
| n53 | new best | val 0.2271, probe 0.2940, 0.86% better than n52: Add an L1-regularized SGD logistic regression base model that reuses the already-comput... |
| n54 | new best | val 0.2051, probe 0.3089, 9.69% better than n53: Add complementary uncertainty features to the stacking meta-learner. Currently each bas... |
| n54 | overfitting | beat n53 on validation (0.2271 -> 0.2051) but got worse on test (0.3201 -> 0.3374) |
| n55 | crash | timeout: killed after 14s |
|  | stop | budget, final selection best_val |
| n54 | final pick | val 0.2051 (rank 1 of 55), test 0.3374 (rank 27 of 55) |
| n42 | best on test | test 0.3140, but val rank 13 of 55: Add a hashed word/punctuation logistic regression as a new diverse base model. A Hashin... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
