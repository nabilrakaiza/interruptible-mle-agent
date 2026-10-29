# Trajectory: A4-off_spooky-author-identification_seed0

- **Task** spooky-author-identification, **condition** A4-off, **seed** 0
- **Nodes** 38 (92% working), **budget used** 121.0 min, **LLM** 39 calls, 566,857 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TF-IDF with logistic regression, Multiclass calibration with temperature scaling, CalibratedClassifierCV for multiclass text models, Naive Bayes for out-of-core text classification, Dictionary feature vectorization for text, Text feature extraction with hashing and clustering
- **Search** 1 improve chains exhausted; longest stretch without a new best 3 nodes; selection regret 0.0009 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use a TF-IDF vectorizer with sublinear term frequencies, English stop words, and 1-2 word n-grams to conver... (val 0.6116) |
| n0 | new best | val 0.6116, probe 0.6144: Use a TF-IDF vectorizer with sublinear term frequencies, English stop words, and 1-2 wo... |
| n0 | card used | first script with TfidfVectorizer from the card "TF-IDF with logistic regression" |
| n0 | card used | first script with TfidfVectorizer from the card "Text feature extraction with hashing and clustering" |
| n1 | draft | Use a TF-IDF vectorizer with sublinear term frequencies, English stop words, and 1-2 word n-grams to extrac... (val 0.6964) |
| n2 | draft | I will use TF-IDF word/word-pair features with sublinear term frequencies, English stop-word removal, and f... (val -) |
| n2 | crash | runtime_error: OSError: [Errno 30] Read-only file system: './predictions.csv' |
| n3 | draft | I will use a hashing-based text vectorizer instead of a vocabulary-building TfidfVectorizer, making this ru... (val 0.7548) |
| n3 | card used | first script with TfidfTransformer from the card "Dictionary feature vectorization for text" |
| n4 | draft | I will use word-boundary-aware character n-grams (2–5 characters) with TF-IDF weighting instead of word bag... (val 0.5146) |
| n4 | new best | val 0.5146, probe 0.5022, 15.85% better than n0: I will use word-boundary-aware character n-grams (2–5 characters) with TF-IDF weighting... |
| n4 | card used | first script with MultinomialNB from the card "Naive Bayes for out-of-core text classification" |
| n5 | new best | val 0.4896, probe 0.4882, 4.87% better than n4: I will replace the MultinomialNB base classifier with a multiclass logistic regression ... |
| n6 | crash | runtime_error: KeyError: 'OUTPUT_DIR' |
| n7 | new best | val 0.4778, probe 0.4786, 2.40% better than n5: The only change is to increase CalibratedClassifierCV's cross-validation folds from 3 t... |
| n8 | new best | val 0.4297, probe 0.4339, 10.07% better than n7: Replace the single char_wb TF-IDF vectorizer with a FeatureUnion that keeps the same ch... |
| n9 | new best | val 0.4294, probe 0.4337, 0.05% better than n8: Extend the word-level TF-IDF branch from unigrams and bigrams to also include trigrams,... |
| n10 | no-op | same predictions as n9: Increase the word-level TF-IDF feature budget from 50,000 to 100,000 while keeping the ... |
| n11 | fixed | debug fixed the crash in n2 after 2 attempt(s) |
| n12 | new best | val 0.4291, probe 0.4348, 0.09% better than n9: Remove the English stop-word filter from the word-level TF-IDF branch. Function words s... |
| n12 | chain exhausted | the chain from n8 had 3 attempts without a real gain; the search moves elsewhere |
| n15 | new best | val 0.4184, probe 0.4227, 2.48% better than n12: Add a third feature branch to the existing FeatureUnion: a character n-gram TF-IDF vect... |
| n17 | new best | val 0.4071, probe 0.4142, 2.70% better than n15: Add a fourth TF-IDF branch to the existing FeatureUnion that preserves original casing,... |
| n18 | new best | val 0.4039, probe 0.4113, 0.79% better than n17: Add a fifth TF-IDF branch that uses character n-grams within word boundaries while pres... |
| n19 | new best | val 0.3971, probe 0.4056, 1.69% better than n18: Raise the logistic regression regularization parameter C from 1.0 to 3.0, reducing L2 r... |
| n20 | new best | val 0.3958, probe 0.4046, 0.32% better than n19: The current model at C=3.0 already improves over stronger regularization (C=0.5), sugge... |
| n23 | new best | val 0.3729, probe 0.3808, 5.80% better than n20: Replace the per-class sigmoid calibration from CalibratedClassifierCV with a single mul... |
| n25 | new best | val 0.3702, probe 0.3799, 0.72% better than n23: Change the cross-validation scheme from 5 folds without shuffling to 10 folds with rand... |
| n26 | new best | val 0.3544, probe 0.3577, 4.27% better than n25: Keep the existing TF-IDF feature pipeline and 10-fold CV, but replace the final tempera... |
| n27 | new best | val 0.3524, probe 0.3570, 0.54% better than n26: Add four surface-level features (log word count, log character count, average word leng... |
| n29 | new best | val 0.3338, probe 0.3447, 5.30% better than n27: Add a third diverse base model to the stacking ensemble: a MultinomialNB trained on a w... |
| n30 | new best | val 0.3295, probe 0.3370, 1.28% better than n29: Add a fourth base model to the stacking ensemble: a logistic regression trained on the ... |
| n32 | new best | val 0.3263, probe 0.3351, 0.97% better than n30: Add a fifth base model to the stacking ensemble: a MultinomialNB trained on the existin... |
| n34 | new best | val 0.3234, probe 0.3347, 0.87% better than n32: Add a sixth base model to the stacking ensemble: a MultinomialNB trained on the charact... |
| n35 | new best | val 0.3231, probe 0.3354, 0.12% better than n34: Add a dedicated logistic regression base model on the existing character `char_wb` TF-I... |
| n36 | new best | val 0.3214, probe 0.3345, 0.51% better than n35: Add a MultinomialNB base model on the existing case-sensitive word TF-IDF matrix, using... |
| n37 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n36 | final pick | val 0.3214 (rank 1 of 35), test 0.3361 (rank 2 of 35) |
| n34 | best on test | test 0.3352, but val rank 3 of 35: Add a sixth base model to the stacking ensemble: a MultinomialNB trained on the charact... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
