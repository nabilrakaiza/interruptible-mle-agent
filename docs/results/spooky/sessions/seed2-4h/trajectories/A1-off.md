# Trajectory: A1-off_spooky-author-identification_seed2

- **Task** spooky-author-identification, **condition** A1-off, **seed** 2
- **Nodes** 78 (97% working), **budget used** 240.0 min, **LLM** 88 calls, 1,496,838 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Tfidf bag-of-words with linear classification, Temperature-scaled probability calibration, Out-of-core multinomial naive Bayes for large text collections, Feature hashing and dictionary vectorization for rich text features, Pipeline with tuned Tfidf hyperparameters, Linear multiclass classifier with probability outputs
- **Search** 9 improve chains exhausted; longest stretch without a new best 24 nodes; selection regret 0.0 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF bag-of-words features with unigrams and bigrams, sublinear term frequency, stop-word removal, an... (val 0.5995) |
| n0 | new best | val 0.5995, probe 0.5976: Use TF-IDF bag-of-words features with unigrams and bigrams, sublinear term frequency, s... |
| n0 | card used | first script with TfidfVectorizer from the card "Tfidf bag-of-words with linear classification" |
| n0 | card used | first script with TfidfVectorizer from the card "Pipeline with tuned Tfidf hyperparameters" |
| n0 | card used | first script with LogisticRegression from the card "Linear multiclass classifier with probability outputs" |
| n1 | draft | Use feature hashing instead of a vocabulary-based TF-IDF vectorizer to build a sparse bag-of-words represen... (val 0.6311) |
| n1 | card used | first script with TfidfTransformer from the card "Feature hashing and dictionary vectorization for rich text features" |
| n2 | draft | I will use a TF-IDF bag-of-words representation with unigrams and bigrams, sublinear term frequency, Englis... (val 0.4595) |
| n2 | new best | val 0.4595, probe 0.4457, 23.36% better than n0: I will use a TF-IDF bag-of-words representation with unigrams and bigrams, sublinear te... |
| n2 | card used | first script with MultinomialNB from the card "Out-of-core multinomial naive Bayes for large text collections" |
| n3 | draft | I will use TF-IDF unigram and bigram features with sublinear term frequency, stop-word removal, and documen... (val 0.5289) |
| n4 | draft | Use TF-IDF unigrams and bigrams with sublinear term frequency, stop-word removal, and document-frequency pr... (val 0.8212) |
| n6 | new best | val 0.4352, probe 0.4022, 5.27% better than n2: I will replace the word-level TF-IDF vectorizer with a character n-gram TF-IDF vectoriz... |
| n9 | new best | val 0.4342, probe 0.4034, 0.25% better than n6: Keep the exact character n-gram TF-IDF preprocessing and MultinomialNB classifier from ... |
| n12 | new best | val 0.4265, probe 0.4002, 1.76% better than n9: Expand the character n-gram window in the TF-IDF vectorizer from (3,5) to (2,6), keepin... |
| n13 | new best | val 0.4260, probe 0.3999, 0.12% better than n12: Change the character n-gram window in the TF-IDF vectorizer from (2,6) to (1,6), keepin... |
| n14 | crash | runtime_error: KeyError: 0 |
| n15 | fixed | debug fixed the crash in n14 after 1 attempt(s) |
| n18 | new best | val 0.4153, probe 0.3873, 2.51% better than n13: Keep the current character n-gram TF-IDF (1,6) with MultinomialNB(alpha=0.1) and temper... |
| n19 | new best | val 0.4153, probe 0.3873, 0.00% better than n18: Keep the current character n-gram TF-IDF (1,6) pipeline with MultinomialNB(alpha=0.1) a... |
| n20 | new best | val 0.3826, probe 0.3598, 7.86% better than n19: I will change the TF-IDF analyzer from `char_wb` to `char`. `char_wb` only extracts cha... |
| n22 | no-op | same predictions as n20: Add a text preprocessor to the TfidfVectorizer that normalizes typographic punctuation—... |
| n23 | new best | val 0.3821, probe 0.3588, 0.13% better than n20: I will set `binary=True` in the character n-gram TF-IDF vectorizer. The current pipelin... |
| n26 | chain exhausted | the chain from n23 had 3 attempts without a real gain; the search moves elsewhere |
| n27 | new best | val 0.3699, probe 0.3472, 3.20% better than n23: Reduce the MultinomialNB smoothing alpha from 0.1 to 0.05. The character n-gram TF-IDF ... |
| n29 | new best | val 0.3625, probe 0.3383, 2.00% better than n27: Lower the MultinomialNB smoothing alpha from 0.05 to 0.02. The character n-gram TF-IDF ... |
| n30 | new best | val 0.3606, probe 0.3349, 0.52% better than n29: Lower the MultinomialNB smoothing alpha from 0.02 to 0.01. The earlier reduction from 0... |
| n32 | new best | val 0.3291, probe 0.3161, 8.74% better than n30: Add a word-level TF-IDF branch to the existing character n-gram features using a Featur... |
| n33 | new best | val 0.3244, probe 0.3119, 1.42% better than n32: Expand the word-level TF-IDF branch from unigrams+bigrams to unigrams+bigrams+trigrams.... |
| n35 | new best | val 0.3232, probe 0.3073, 0.38% better than n33: The word-level TF-IDF branch currently uses scikit-learn's default token pattern, which... |
| n36 | no-op | same predictions as n35: The word-level TF-IDF branch currently discards any word appearing in more than 80% of ... |
| n37 | new best | val 0.3218, probe 0.3077, 0.43% better than n35: The word-level TF-IDF branch currently tokenizes only sequences of word characters, so ... |
| n40 | new best | val 0.3215, probe 0.3071, 0.11% better than n37: Add a handcrafted surface-feature branch to the FeatureUnion that captures stylistic si... |
| n43 | chain exhausted | the chain from n40 had 3 attempts without a real gain; the search moves elsewhere |
| n59 | no-op | same predictions as n58: Raise the word-level TF-IDF branch's max_df from 0.8 to 1.0. The current cap discards v... |
| n65 | new best | val 0.3176, probe 0.3068, 1.21% better than n40: Extend the word-level TF-IDF branch from unigrams and bigrams to include trigrams as we... |
| n66 | new best | val 0.3175, probe 0.3063, 0.03% better than n65: Binarize the character n-gram TF-IDF branch by adding `binary=True` to the existing cha... |
| n67 | new best | val 0.3171, probe 0.3060, 0.11% better than n66: Add a count of uppercase-initial words to the handcrafted surface-feature branch. The e... |
| n68 | new best | val 0.3167, probe 0.3055, 0.14% better than n67: Add a count of common English stopwords to the handcrafted surface-feature branch. The ... |
| n69 | new best | val 0.3164, probe 0.3053, 0.08% better than n68: Add a normalized stopword ratio (stopwords per word) to the handcrafted surface-feature... |
| n70 | new best | val 0.3162, probe 0.3054, 0.07% better than n69: Add scale-free punctuation-density and capitalization-density features to the handcraft... |
| n71 | new best | val 0.3161, probe 0.3054, 0.01% better than n70: Add a scale-free long-word density feature to the handcrafted surface branch. The branc... |
| n71 | chain exhausted | the chain from n68 had 3 attempts without a real gain; the search moves elsewhere |
| n74 | new best | val 0.3149, probe 0.3045, 0.38% better than n71: Add a fixed-vocabulary function-word TF-IDF branch to the FeatureUnion. It encodes clos... |
| n75 | new best | val 0.3145, probe 0.3049, 0.13% better than n74: Change the word-level TF-IDF branch's token_pattern so it also emits punctuation charac... |
| n77 | crash | generation_error: empty reply |
|  | stop | budget, final selection best_val |
| n75 | final pick | val 0.3145 (rank 1 of 76), test 0.3257 (rank 1 of 76) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
