# Trajectory: C4_detecting-insults-in-social-commentary_seed4

- **Task** detecting-insults-in-social-commentary, **condition** C4, **seed** 4
- **Nodes** 80 (99% working), **budget used** 243.5 min, **LLM** 95 calls, 1,998,348 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** SGD linear classifiers on TF-IDF sparse text features, Calibrated random forest for text classification probabilities, Polynomial feature expansion with linear models, Out-of-core naive Bayes for large text collections, Isotonic and sigmoid probability calibration, Text vectorization with n-grams and custom stop words
- **Search** 15 improve chains exhausted; longest stretch without a new best 39 nodes; selection regret 0.0052 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will load the training and prediction CSVs, clean each comment by stripping surrounding quotes and decodi... (val 0.8583) |
| n0 | new best | val 0.8583, probe 0.8810: I will load the training and prediction CSVs, clean each comment by stripping surroundi... |
| n0 | card used | first script with TfidfVectorizer from the card "SGD linear classifiers on TF-IDF sparse text features" |
| n0 | card used | first script with LogisticRegression from the card "Polynomial feature expansion with linear models" |
| n0 | card used | first script with TfidfVectorizer from the card "Out-of-core naive Bayes for large text collections" |
| n0 | card used | first script with TfidfVectorizer from the card "Text vectorization with n-grams and custom stop words" |
| n1 | draft | I will load both CSVs with pandas and clean each comment by removing surrounding quotes and decoding common... (val 0.8881) |
| n1 | new best | val 0.8881, probe 0.9237, 3.47% better than n0: I will load both CSVs with pandas and clean each comment by removing surrounding quotes... |
| n2 | draft | I will load both CSVs and clean each comment by removing the outer quoting layer, decoding escaped byte/uni... (val 0.8042) |
| n3 | draft | I will load the CSVs and clean each comment by stripping the outer quote layer and decoding escaped newline... (val 0.8654) |
| n4 | draft | I will parse both CSVs and clean each comment by removing the outer quote layer, collapsing doubled backsla... (val 0.8695) |
| n9 | chain exhausted | the chain from n1 had 3 attempts without a real gain; the search moves elsewhere |
| n10 | no-op | same predictions as n8: I will keep the proven Unicode cleaning, the char_wb TF-IDF (2-5) vectorizer, and the S... |
| n11 | new best | val 0.8892, probe 0.9219, 0.12% better than n1: I will keep the proven Unicode cleaning, the char_wb TF-IDF (2-5) vectorizer, and the b... |
| n14 | chain exhausted | the chain from n11 had 3 attempts without a real gain; the search moves elsewhere |
| n21 | new best | val 0.8895, probe 0.9230, 0.04% better than n11: I will keep the proven Unicode cleaning, the char_wb TF-IDF (2-5) vectorizer, and the S... |
| n22 | new best | val 0.8895, probe 0.9229, 0.00% better than n21: Keep the proven Unicode cleaning, char_wb TF-IDF (2-5) vectorizer, and SGD log-loss cla... |
| n24 | new best | val 0.8909, probe 0.9178, 0.15% better than n22: Keep the proven Unicode cleaning, char_wb TF-IDF (2-5) vectorizer, and SGD log-loss cla... |
| n24 | overfitting | beat n22 on validation (0.8895 -> 0.8909) but got worse on test (0.9020 -> 0.9000) |
| n25 | no-op | same predictions as n24: I will keep the proven Unicode cleaning, the transductive char_wb TF-IDF (2-5) vectoriz... |
| n26 | no-op | same predictions as n24: Increase the TF-IDF vocabulary cap from 200,000 to 300,000 character n-grams. Previous ... |
| n27 | chain exhausted | the chain from n24 had 3 attempts without a real gain; the search moves elsewhere |
| n29 | overfitting | beat n22 on validation (0.8895 -> 0.8909) but got worse on test (0.9020 -> 0.9000) |
| n31 | no-op | same predictions as n29: Keep the proven Unicode/byte-escape decoding, transductive char_wb TF-IDF (2-5) vectori... |
| n32 | new best | val 0.8910, probe 0.9178, 0.01% better than n24: Keep the proven Unicode/byte-escape decoding, transductive char_wb TF-IDF (2-5) vectori... |
| n32 | chain exhausted | the chain from n29 had 3 attempts without a real gain; the search moves elsewhere |
| n36 | overfitting | beat n35 on validation (0.8830 -> 0.8838) but got worse on test (0.9021 -> 0.9004) |
| n40 | no-op | same predictions as n39: I will make one targeted change to the current best script: increase the char_wb TF-IDF... |
| n49 | no-op | same predictions as n48: Increase `max_features` in the char_wb TF-IDF vectorizer from 50,000 to 75,000. Earlier... |
| n68 | no-op | same predictions as n67: Add whitespace normalization to the existing cleaning function by collapsing all runs o... |
| n72 | new best | val 0.8920, probe 0.9214, 0.11% better than n32: Add a FeatureUnion branch that computes a small set of hand-crafted discourse features ... |
| n74 | new best | val 0.8945, probe 0.9189, 0.28% better than n72: Add a targeted interaction feature to the existing hand-crafted meta-features: the prod... |
| n75 | new best | val 0.8961, probe 0.9216, 0.18% better than n74: Add a new hand-crafted feature to TextMetaFeatures: the number of times a second-person... |
| n76 | new best | val 0.8966, probe 0.9234, 0.06% better than n75: Expand the profanity/insult lexicon used by TextMetaFeatures to include common non-prof... |
| n77 | new best | val 0.8971, probe 0.9214, 0.06% better than n76: Expand the hand-crafted meta-feature lexicon in TextMetaFeatures to include additional ... |
| n78 | new best | val 0.8991, probe 0.9217, 0.22% better than n77: Expand the profanity lexicon in TextMetaFeatures with common compound insults that the ... |
| n79 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n78 | final pick | val 0.8991 (rank 1 of 79), test 0.9007 (rank 30 of 79) |
| n13 | best on test | test 0.9059, but val rank 39 of 79: I will replace the single char_wb TF-IDF vectorizer with a FeatureUnion that concatenat... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
