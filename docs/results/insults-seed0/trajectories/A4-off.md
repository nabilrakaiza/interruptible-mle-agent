# Trajectory: A4-off_detecting-insults-in-social-commentary_seed0

- **Task** detecting-insults-in-social-commentary, **condition** A4-off, **seed** 0
- **Nodes** 51 (94% working), **budget used** 246.4 min, **LLM** 55 calls, 1,113,409 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Linear models on sparse bag-of-words text features, Calibrated random forest classifier, Custom stop-word-aware text vectorization, Out-of-core naive Bayes for large text streams, Sigmoid and isotonic calibration for classifiers
- **Search** 8 improve chains exhausted; longest stretch without a new best 10 nodes; selection regret 0.0012 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Build a fast text baseline using TF-IDF features that combine word unigrams/bigrams with character 3- to 5-... (val 0.8862) |
| n0 | new best | val 0.8862, probe 0.9110: Build a fast text baseline using TF-IDF features that combine word unigrams/bigrams wit... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Linear models on sparse bag-of-words text features" |
| n0 | card used | first script with TfidfVectorizer from the card "Custom stop-word-aware text vectorization" |
| n1 | draft | This first solution uses a text-only logistic regression trained with stochastic gradient descent, which is... (val 0.8443) |
| n1 | card used | first script with SGDClassifier from the card "Out-of-core naive Bayes for large text streams" |
| n2 | draft | This solution uses character n-gram TF-IDF features fed to a Complement Naive Bayes classifier, which is a ... (val 0.7781) |
| n3 | draft | This solution uses a random forest, which is a different model family from the earlier linear and naive-Bay... (val 0.8255) |
| n3 | card used | first script with RandomForestClassifier from the card "Calibrated random forest classifier" |
| n4 | draft | This first solution uses an ensemble of two complementary text classifiers rather than a single model: a re... (val 0.8508) |
| n6 | new best | val 0.8864, probe 0.9105, 0.02% better than n0: Clean each comment before vectorization by removing the literal `\xNN` and `\uNNNN` esc... |
| n7 | new best | val 0.8872, probe 0.9107, 0.09% better than n6: Keep the current preprocessing and feature pipeline intact, but expand the word-level T... |
| n7 | chain exhausted | the chain from n0 had 3 attempts without a real gain; the search moves elsewhere |
| n8 | no-op | same predictions as n4: Replace the Multinomial Naive Bayes component with Complement Naive Bayes, which is des... |
| n10 | new best | val 0.8890, probe 0.9215, 0.21% better than n7: Add a small handcrafted feature transformer to the existing FeatureUnion so the linear ... |
| n11 | new best | val 0.8898, probe 0.9221, 0.09% better than n10: Replace the fixed 0.5/0.5 rank blend between logistic regression and linear SVM with a ... |
| n12 | new best | val 0.8899, probe 0.9221, 0.01% better than n11: Add an interaction feature to CommentStats that captures profanity directed at a conver... |
| n13 | new best | val 0.8899, probe 0.9215, 0.01% better than n12: Replace the current profanity×second-person-product feature in CommentStats with a dire... |
| n13 | chain exhausted | the chain from n10 had 3 attempts without a real gain; the search moves elsewhere |
| n15 | new best | val 0.8910, probe 0.9185, 0.12% better than n13: Add two lexical directedness features to the existing ToneStats block: a second-person ... |
| n17 | new best | val 0.8911, probe 0.9189, 0.00% better than n15: Add TruncatedSVD latent semantic features derived from the combined word/character TF-I... |
| n18 | chain exhausted | the chain from n15 had 3 attempts without a real gain; the search moves elsewhere |
| n22 | new best | val 0.8933, probe 0.9141, 0.25% better than n17: Add a block of non-negative matrix factorization (NMF) topic features derived from the ... |
| n22 | overfitting | beat n21 on validation (0.8909 -> 0.8933) but got worse on test (0.9057 -> 0.8984) |
| n23 | new best | val 0.8997, probe 0.9180, 0.72% better than n22: Add a RandomForestClassifier trained on the existing sparse TF-IDF plus standardized NM... |
| n25 | new best | val 0.9050, probe 0.9146, 0.58% better than n23: Add date/time features extracted from the previously unused Date column to the feature ... |
| n27 | new best | val 0.9051, probe 0.9154, 0.02% better than n25: Improve the comment cleaning by actually decoding the unicode-escape sequences that rem... |
| n28 | chain exhausted | the chain from n25 had 3 attempts without a real gain; the search moves elsewhere |
| n30 | no-op | same predictions as n9: Add a binary feature derived from the id prefix ('c' vs 't') to the sparse TF-IDF matri... |
| n37 | new best | val 0.9064, probe 0.9227, 0.14% better than n27: Add a DirectedInsultFeatures transformer that explicitly models the target of an insult... |
| n40 | new best | val 0.9072, probe 0.9243, 0.09% better than n37: Add an ExtraTreesClassifier as a fourth equal-weight rank-blend member. ExtraTrees rand... |
| n41 | chain exhausted | the chain from n37 had 3 attempts without a real gain; the search moves elsewhere |
| n42 | crash | runtime_error: UnboundLocalError: cannot access local variable 'i' where it is not associated with a value |
| n45 | crash | runtime_error: ValueError: axis 0 index 20793 exceeds matrix dimension 6414 |
| n46 | fixed | debug fixed the crash in n42 after 2 attempt(s) |
| n50 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n40 | final pick | val 0.9072 (rank 1 of 48), test 0.9083 (rank 4 of 48) |
| n48 | best on test | test 0.9095, but val rank 7 of 48: Add date/time features from the previously unused Date column: a has-date indicator plu... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
