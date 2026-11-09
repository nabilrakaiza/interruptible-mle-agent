# Trajectory: C5_spooky-author-identification_seed4

- **Task** spooky-author-identification, **condition** C5, **seed** 4
- **Nodes** 49 (98% working), **budget used** 240.0 min, **LLM** 55 calls, 987,622 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TF-IDF bag-of-words with linear classifier, Hashing vectorizer with linear model, Out-of-core naive Bayes for text, Temperature scaling for multiclass probability calibration, One-vs-rest probability calibration for multiclass text, Dictionary-style contextual feature pipeline, Multiclass logistic regression for categorical text
- **Search** 2 improve chains exhausted; longest stretch without a new best 4 nodes; selection regret 0.0 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF word and bigram features with sublinear term frequency and frequency-based cutoffs, then train a... (val 0.4725) |
| n0 | new best | val 0.4725, probe 0.4737: Use TF-IDF word and bigram features with sublinear term frequency and frequency-based c... |
| n0 | card used | first script with TfidfVectorizer from the card "TF-IDF bag-of-words with linear classifier" |
| n0 | card used | first script with TfidfVectorizer from the card "Out-of-core naive Bayes for text" |
| n0 | card used | first script with LogisticRegression from the card "Multiclass logistic regression for categorical text" |
| n1 | draft | Use a HashingVectorizer with word and bigram features, combined with a TfidfTransformer, and train a multin... (val 0.8605) |
| n1 | card used | first script with HashingVectorizer, TfidfTransformer from the card "Hashing vectorizer with linear model" |
| n1 | card used | first script with TfidfTransformer from the card "Dictionary-style contextual feature pipeline" |
| n2 | draft | This first solution uses a fixed-size HashingVectorizer with word and bigram features, avoiding an explicit... (val 0.4930) |
| n3 | draft | I’ll use character n-gram TF-IDF features instead of the earlier word/hashing baselines, because character ... (val 0.5267) |
| n4 | draft | I will use a TF-IDF vectorizer on word unigrams only, with sublinear term frequency, stop-word removal, and... (val 0.6016) |
| n5 | new best | val 0.3984, probe 0.4022, 15.70% better than n0: Add character n-gram TF-IDF features to the existing word and bigram features. Characte... |
| n7 | new best | val 0.3951, probe 0.4012, 0.81% better than n5: Expand the word TF-IDF vectorizer from unigrams plus bigrams to include trigrams as wel... |
| n8 | new best | val 0.3843, probe 0.3924, 2.75% better than n7: Add temperature scaling to the existing word+bigram and character n-gram TF-IDF logisti... |
| n10 | new best | val 0.3763, probe 0.3830, 2.08% better than n8: Add a raw character n-gram TF-IDF feature set using analyzer='char' in addition to the ... |
| n11 | no-op | same predictions as n10: Instead of fixing C=4.0, I will tune the logistic regression regularization strength on... |
| n12 | new best | val 0.3564, probe 0.3529, 5.27% better than n10: Add a Complement Naive Bayes model as a second classifier in addition to the logistic r... |
| n13 | new best | val 0.3537, probe 0.3494, 0.78% better than n12: I will jointly tune the two model hyperparameters on the existing validation split inst... |
| n14 | new best | val 0.3478, probe 0.3420, 1.67% better than n13: I will augment the existing ensemble with a third model, an explicit TF-IDF Multinomial... |
| n15 | new best | val 0.3451, probe 0.3400, 0.76% better than n14: Add a compact set of hand-crafted style features to the logistic regression branch of t... |
| n16 | new best | val 0.3323, probe 0.3270, 3.72% better than n15: Replace the arithmetic weighted average of the three temperature-scaled model probabili... |
| n18 | new best | val 0.3290, probe 0.3223, 0.97% better than n16: Add a fourth base model, Bernoulli Naive Bayes, trained on the exact same combined word... |
| n20 | no-op | same predictions as n18: Add a fifth base model to the ensemble: a logistic regression trained only on the chara... |
| n21 | no-op | same predictions as n18: Add a Gaussian Naive Bayes model trained on standardized TruncatedSVD components (100 d... |
| n22 | new best | val 0.3266, probe 0.3219, 0.74% better than n18: Expand the handcrafted style feature block with normalized punctuation rates (commas, s... |
| n23 | new best | val 0.3243, probe 0.3199, 0.70% better than n22: Change the word TF-IDF vectorizer's token pattern so that punctuation marks are kept as... |
| n26 | chain exhausted | the chain from n23 had 3 attempts without a real gain; the search moves elsewhere |
| n28 | new best | val 0.3203, probe 0.3203, 1.24% better than n23: Increase the character n-gram window from (2,5) to (2,6) for both the `char_wb` and `ch... |
| n29 | new best | val 0.3174, probe 0.3213, 0.91% better than n28: Increase the character n-gram window from (2,6) to (2,7) for both the `char_wb` and `ch... |
| n30 | new best | val 0.3171, probe 0.3203, 0.09% better than n29: Add a single hand-crafted style feature to the logistic regression input: the proportio... |
| n31 | new best | val 0.3165, probe 0.3185, 0.19% better than n30: Add two hand-crafted style features to the existing logistic-regression feature matrix:... |
| n33 | new best | val 0.3159, probe 0.3163, 0.21% better than n31: Replace the single global ensemble weights with per-class weights: instead of learning ... |
| n34 | new best | val 0.3141, probe 0.3144, 0.55% better than n33: Extend the word-level TF-IDF vectorizer from unigrams+bigrams to unigrams+bigrams+trigr... |
| n36 | new best | val 0.3140, probe 0.3163, 0.05% better than n34: Replace the optional BernoulliNB base model with a MultinomialNB trained only on the ch... |
| n38 | no-op | same predictions as n36: Add a ComplementNB base model trained only on the character n-gram TF-IDF features (cha... |
| n38 | chain exhausted | the chain from n34 had 3 attempts without a real gain; the search moves elsewhere |
| n40 | no-op | same predictions as n39: Add a logistic regression base model trained only on the character n-gram TF-IDF featur... |
| n41 | new best | val 0.3068, probe 0.3090, 2.29% better than n36: Add a case-sensitive word TF-IDF block (unigrams and bigrams, with `lowercase=False`) t... |
| n42 | new best | val 0.3060, probe 0.3079, 0.26% better than n41: The lowercased word TF-IDF vectorizer still uses the default scikit-learn token pattern... |
| n44 | new best | val 0.3055, probe 0.3086, 0.15% better than n42: The logistic regression regularization grid currently only spans C=0.5 to 8, so the val... |
| n46 | new best | val 0.3006, probe 0.3028, 1.62% better than n44: Add a punctuation-shape TF-IDF block that is missing from the current feature matrix. A... |
| n48 | crash | timeout: killed after 399s |
|  | stop | budget, final selection best_val |
| n46 | final pick | val 0.3006 (rank 1 of 48), test 0.3136 (rank 1 of 48) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
