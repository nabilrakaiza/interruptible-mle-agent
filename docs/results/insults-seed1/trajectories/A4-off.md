# Trajectory: A4-off_detecting-insults-in-social-commentary_seed1

- **Task** detecting-insults-in-social-commentary, **condition** A4-off, **seed** 1
- **Nodes** 200 (99% working), **budget used** 233.1 min, **LLM** 204 calls, 3,311,174 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** SGD linear classifiers on TF-IDF text features, Random forest with probability calibration, SVM or linear model calibrated with sigmoid or isotonic, Text vectorization with n-grams and stop-word tuning, Out-of-core Naive Bayes for large text streams, Linear models with polynomial feature expansion
- **Search** 40 improve chains exhausted; longest stretch without a new best 145 nodes; selection regret 0.0 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will build a simple, robust text classifier using TF-IDF features and logistic regression. First I will p... (val 0.8563) |
| n0 | new best | val 0.8563, probe 0.8778: I will build a simple, robust text classifier using TF-IDF features and logistic regres... |
| n0 | card used | first script with TfidfVectorizer from the card "SGD linear classifiers on TF-IDF text features" |
| n0 | card used | first script with TfidfVectorizer from the card "Text vectorization with n-grams and stop-word tuning" |
| n0 | card used | first script with TfidfVectorizer from the card "Out-of-core Naive Bayes for large text streams" |
| n1 | draft | I will use a text-only pipeline based on TF-IDF n-grams and a Complement Naive Bayes classifier, which is a... (val 0.8072) |
| n2 | draft | I will build a text-only classifier using TF-IDF word and word-pair features plus a linear SVM trained with... (val 0.7833) |
| n3 | draft | I will use a random forest on TF-IDF word and word-pair features. This is a different model family from the... (val 0.8366) |
| n3 | card used | first script with RandomForestClassifier from the card "Random forest with probability calibration" |
| n4 | draft | I will build a text-only classifier using TF-IDF word and word-pair features with a linear SVM whose raw de... (val 0.8573) |
| n4 | new best | val 0.8573, probe 0.8866, 0.13% better than n0: I will build a text-only classifier using TF-IDF word and word-pair features with a lin... |
| n5 | new best | val 0.8791, probe 0.9043, 2.53% better than n4: I will keep the existing cleaning, word TF-IDF vectorizer, and logistic regression exac... |
| n6 | new best | val 0.8853, probe 0.9076, 0.71% better than n5: I will keep the existing cleaning, word/character TF-IDF vectorizers, and logistic regr... |
| n7 | crash | runtime_error: ValueError: Cannot center sparse matrices: pass `with_mean=False` instead. See docstring for motivation and alternatives. |
| n8 | fixed | debug fixed the crash in n7 after 1 attempt(s) |
| n10 | new best | val 0.8858, probe 0.9043, 0.06% better than n6: Replace the fixed 0.5 average of the word and character logistic-regression probabiliti... |
| n12 | new best | val 0.8880, probe 0.9101, 0.25% better than n10: Replace the hard-coded C=1.0 for the base logistic regressions with a small cross-valid... |
| n14 | new best | val 0.8900, probe 0.9119, 0.23% better than n12: Use the unlabeled comments from predict.csv to fit the TF-IDF vectorizers, so vocabular... |
| n16 | new best | val 0.8943, probe 0.9120, 0.49% better than n14: Add handcrafted surface features to the meta-learner in the stacking ensemble, rather t... |
| n20 | chain exhausted | the chain from n16 had 3 attempts without a real gain; the search moves elsewhere |
| n21 | new best | val 0.8970, probe 0.8984, 0.30% better than n16: Add two direct-address features to the existing handcrafted surface set: a count of sec... |
| n23 | new best | val 0.8970, probe 0.9048, 0.00% better than n21: Expand the lexicon used for the direct-address insult feature only. I will keep the ori... |
| n25 | new best | val 0.8975, probe 0.9097, 0.05% better than n23: Add a new handcrafted surface feature that counts how often an insult token from the br... |
| n25 | chain exhausted | the chain from n21 had 3 attempts without a real gain; the search moves elsewhere |
| n29 | new best | val 0.9000, probe 0.9046, 0.28% better than n25: Add date/time features derived from the previously unused Date column to the handcrafte... |
| n30 | new best | val 0.9062, probe 0.9094, 0.69% better than n29: Add four lexical surface features—word count, average word length, first-person pronoun... |
| n31 | new best | val 0.9067, probe 0.9094, 0.06% better than n30: I will expand the word-level TF-IDF vectorizer from bigrams to trigrams by changing `ng... |
| n33 | chain exhausted | the chain from n30 had 3 attempts without a real gain; the search moves elsewhere |
| n151 | no-op | same predictions as n149: Fix the unicode decoding of comments before feature extraction. The current `clean_comm... |
| n165 | overfitting | beat n149 on validation (0.8977 -> 0.8992) but got worse on test (0.8984 -> 0.8847) |
| n172 | crash | generation_error: empty reply |
| n177 | new best | val 0.9078, probe 0.9337, 0.12% better than n31: Add an out-of-fold Multinomial Naive Bayes probability feature computed from the combin... |
| n178 | new best | val 0.9080, probe 0.9351, 0.02% better than n177: Add an out-of-fold SGDClassifier probability feature trained on the combined word+chara... |
| n181 | chain exhausted | the chain from n177 had 3 attempts without a real gain; the search moves elsewhere |
| n183 | no-op | same predictions as n175: The current text cleaning uses `ast.literal_eval`, which turns stored UTF-8 byte escape... |
| n184 | new best | val 0.9089, probe 0.9312, 0.10% better than n178: Add an out-of-fold Random Forest probability feature computed from SVD-reduced word+cha... |
| n188 | chain exhausted | the chain from n184 had 3 attempts without a real gain; the search moves elsewhere |
| n192 | new best | val 0.9106, probe 0.9310, 0.19% better than n184: Add an out-of-fold RBF-kernel SVM probability feature computed from the same SVD-reduce... |
| n195 | chain exhausted | the chain from n192 had 3 attempts without a real gain; the search moves elsewhere |
| n199 | new best | val 0.9108, probe 0.9267, 0.02% better than n192: Add a new surface feature that counts imperative insults where an insult word is follow... |
|  | stop | max_nodes, final selection best_val |
| n199 | final pick | val 0.9108 (rank 1 of 198), test 0.9127 (rank 1 of 198) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
