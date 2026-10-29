# Trajectory: A1-off_spooky-author-identification_seed0

- **Task** spooky-author-identification, **condition** A1-off, **seed** 0
- **Nodes** 42 (98% working), **budget used** 120.0 min, **LLM** 47 calls, 857,361 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Sparse TF-IDF linear classifier, Out-of-core Naive Bayes on text, Probability-calibrated text classifier, Feature hashing for high-dimensional text, Structured feature vectorization with DictVectorizer, Tuned text feature extraction pipeline
- **Search** 0 improve chains exhausted; longest stretch without a new best 3 nodes; selection regret 0.0004 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will use a TF-IDF vectorizer followed by multinomial logistic regression, which is a fast and strong base... (val 0.6052) |
| n0 | new best | val 0.6052, probe 0.6080: I will use a TF-IDF vectorizer followed by multinomial logistic regression, which is a ... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Sparse TF-IDF linear classifier" |
| n0 | card used | first script with TfidfVectorizer from the card "Out-of-core Naive Bayes on text" |
| n0 | card used | first script with LogisticRegression from the card "Probability-calibrated text classifier" |
| n0 | card used | first script with TfidfVectorizer from the card "Tuned text feature extraction pipeline" |
| n1 | draft | Use a TF-IDF vectorizer with sublinear term frequency and 1-2 word n-grams, followed by a Complement Naive ... (val 0.6437) |
| n2 | draft | Use feature hashing instead of a vocabulary-based TF-IDF vectorizer to keep the pipeline memory-light: Hash... (val 0.7505) |
| n2 | card used | first script with HashingVectorizer, TfidfTransformer from the card "Feature hashing for high-dimensional text" |
| n2 | card used | first script with TfidfTransformer from the card "Structured feature vectorization with DictVectorizer" |
| n3 | draft | Use character-level TF-IDF features, which capture punctuation and stylistic sub-word patterns better than ... (val 0.5190) |
| n3 | new best | val 0.5190, probe 0.5204, 14.25% better than n0: Use character-level TF-IDF features, which capture punctuation and stylistic sub-word p... |
| n4 | draft | I will combine word-level TF-IDF (1-2 n-grams) with character-level TF-IDF (char_wb 2-5 n-grams) to capture... (val 0.4137) |
| n4 | new best | val 0.4137, probe 0.4116, 20.28% better than n3: I will combine word-level TF-IDF (1-2 n-grams) with character-level TF-IDF (char_wb 2-5... |
| n5 | new best | val 0.4092, probe 0.4025, 1.11% better than n4: I will keep the current combined word-level and char_wb TF-IDF features and the logisti... |
| n6 | no-op | same predictions as n5: I will broaden the logistic-regression regularization search from C = [0.3, 1.0, 3.0] t... |
| n7 | new best | val 0.3918, probe 0.3843, 4.24% better than n5: I will add a second character-level TF-IDF representation using the raw `char` analyzer... |
| n8 | new best | val 0.3906, probe 0.3835, 0.30% better than n7: I will include 1-character n-grams in both character TF-IDF vectorizers by changing the... |
| n10 | new best | val 0.3875, probe 0.3802, 0.79% better than n8: I will make the raw character TF-IDF vectorizer case-sensitive by setting `lowercase=Fa... |
| n12 | new best | val 0.3817, probe 0.3723, 1.51% better than n10: I will keep the existing feature set and logistic-regression C search unchanged, but ad... |
| n13 | new best | val 0.3807, probe 0.3703, 0.26% better than n12: Keep the existing features, logistic-regression C search, and temperature calibration f... |
| n14 | new best | val 0.3756, probe 0.3629, 1.32% better than n13: Add a case-sensitive word-level TF-IDF vectorizer alongside the existing lowercased wor... |
| n15 | new best | val 0.3737, probe 0.3607, 0.51% better than n14: Replace the final probability-space weighted ensemble with logit-space stacking. The th... |
| n16 | new best | val 0.3707, probe 0.3624, 0.81% better than n15: Replace the final scalar logit-space weight optimization with a per-class logistic-regr... |
| n17 | new best | val 0.3592, probe 0.3508, 3.09% better than n16: Add supervised Naive-Bayes log-count-ratio features to the engineered style block so ev... |
| n18 | new best | val 0.3579, probe 0.3510, 0.36% better than n17: Keep the entire feature extraction and base-model ensemble unchanged, and only improve ... |
| n19 | new best | val 0.3579, probe 0.3509, 0.00% better than n18: Replace the scalar temperature scaling used on the stacked model's logits with per-clas... |
| n20 | new best | val 0.3579, probe 0.3510, 0.00% better than n19: Replace the per-class temperature scaling applied to the final stacker's logits with a ... |
| n21 | new best | val 0.3522, probe 0.3489, 1.61% better than n20: Keep the entire existing feature, calibration, and stacking pipeline intact. The only c... |
| n22 | no-op | same predictions as n21: The best inverse-regularization strength from the existing grid was C=0.3, which sat ex... |
| n23 | new best | val 0.3470, probe 0.3433, 1.45% better than n21: I will add a new TF-IDF feature block that encodes "case shape": a custom preprocessor ... |
| n25 | new best | val 0.3327, probe 0.3206, 4.14% better than n23: I will add a new dense feature block of supervised Naive-Bayes log-count-ratio features... |
| n26 | new best | val 0.3322, probe 0.3203, 0.13% better than n25: I will add one new supervised dense feature block: Naive-Bayes log-count-ratio features... |
| n27 | new best | val 0.3294, probe 0.3205, 0.84% better than n26: I will augment the existing dense style-feature block with additional hand-crafted styl... |
| n28 | new best | val 0.3283, probe 0.3201, 0.33% better than n27: Add a case-sensitive word-boundary character TF-IDF block (`analyzer='char_wb'`, `lower... |
| n32 | new best | val 0.3273, probe 0.3192, 0.33% better than n28: Add a fourth base model to the logit-space ensemble: a logistic regression trained only... |
| n33 | new best | val 0.3271, probe 0.3194, 0.04% better than n32: Add a fifth base model to the logit-space ensemble: a logistic regression trained on a ... |
| n34 | new best | val 0.3271, probe 0.3198, 0.00% better than n33: Add a sixth base model to the logit-space ensemble: a logistic regression trained on a ... |
| n35 | new best | val 0.3219, probe 0.3202, 1.60% better than n34: Add a seventh base model to the logit-space ensemble: a Complement Naive Bayes classifi... |
| n36 | new best | val 0.3210, probe 0.3220, 0.27% better than n35: Add a second generative base model to the logit-space ensemble: a Complement Naive Baye... |
| n38 | new best | val 0.3158, probe 0.3143, 1.62% better than n36: Add a third generative base model to the logit-space ensemble: a Complement Naive Bayes... |
| n40 | new best | val 0.3149, probe 0.3140, 0.30% better than n38: Add an additional generative base model to the logit-space ensemble: a Complement Naive... |
| n41 | crash | timeout: killed after 150s |
|  | stop | budget, final selection best_val |
| n40 | final pick | val 0.3149 (rank 1 of 41), test 0.3377 (rank 2 of 41) |
| n38 | best on test | test 0.3372, but val rank 2 of 41: Add a third generative base model to the logit-space ensemble: a Complement Naive Bayes... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
