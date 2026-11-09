# Trajectory: C1_spooky-author-identification_seed3

- **Task** spooky-author-identification, **condition** C1, **seed** 3
- **Nodes** 32 (97% working), **budget used** 240.0 min, **LLM** 39 calls, 715,588 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TF-IDF Bag-of-Words with Linear Classifier, Multiclass Probability Calibration via Temperature Scaling, Out-of-Core Naive Bayes for Large Text Corpora, Calibrated Multiclass Text Classifier, Sparse Feature Hashing and DictVectorizer Pipelines, TfidfVectorizer Pipeline with Hyperparameter Tuning
- **Search** 1 improve chains exhausted; longest stretch without a new best 10 nodes; selection regret 0.0 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF features with 1- and 2-word n-grams, sublinear term frequencies, stop-word removal, and document... (val 0.5227) |
| n0 | new best | val 0.5227, probe 0.5309: Use TF-IDF features with 1- and 2-word n-grams, sublinear term frequencies, stop-word r... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF Bag-of-Words with Linear Classifier" |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TfidfVectorizer Pipeline with Hyperparameter Tuning" |
| n1 | draft | Use character n-gram count features instead of word-level TF-IDF, because character patterns capture punctu... (val 3.1706) |
| n1 | card used | first script with MultinomialNB from the card "Out-of-Core Naive Bayes for Large Text Corpora" |
| n2 | draft | Use TF-IDF character n-grams (char_wb, 2-5) with sublinear term frequency and document-frequency cutoffs to... (val 0.4418) |
| n2 | new best | val 0.4418, probe 0.4466, 15.47% better than n0: Use TF-IDF character n-grams (char_wb, 2-5) with sublinear term frequency and document-... |
| n3 | draft | To move beyond single-representation TF-IDF, this solution stacks word-level and character-level TF-IDF fea... (val 0.4664) |
| n4 | draft | Use word-level TF-IDF features with 1- and 2-word n-grams, sublinear term frequencies, and document-frequen... (val 0.4635) |
| n6 | new best | val 0.4343, probe 0.4355, 1.71% better than n2: Keep the strong character n-gram TF-IDF backbone and logistic regression, but augment t... |
| n7 | new best | val 0.4307, probe 0.4309, 0.83% better than n6: Replace the character n-gram range from (2,5) to (2,6) in both the validation and final... |
| n8 | new best | val 0.4299, probe 0.4302, 0.17% better than n7: Extend the character n-gram range from (2,6) to (2,7) in both TfidfVectorizer instances... |
| n9 | new best | val 0.4299, probe 0.4297, 0.01% better than n8: Extend the character n-gram range from (2,7) to (2,8) in both TfidfVectorizer instances... |
| n10 | new best | val 0.4229, probe 0.4236, 1.64% better than n9: Change the TfidfVectorizer settings from the default lowercase=True to lowercase=False ... |
| n13 | new best | val 0.4059, probe 0.4121, 4.01% better than n10: Widen the logistic regression regularization search from the current three C values to ... |
| n14 | new best | val 0.4011, probe 0.4143, 1.17% better than n13: Extend the handcrafted feature block with normalized stylistic ratios and lexical stati... |
| n16 | new best | val 0.3861, probe 0.3967, 3.75% better than n14: Add a complementary character-level TF-IDF view using analyzer="char" alongside the exi... |
| n17 | new best | val 0.3860, probe 0.3969, 0.02% better than n16: Add character unigrams to both TF-IDF views by changing `ngram_range` from `(2,7)` to `... |
| n18 | new best | val 0.3858, probe 0.3970, 0.05% better than n17: Add temperature scaling calibration on the held-out validation set. After selecting the... |
| n19 | chain exhausted | the chain from n16 had 3 attempts without a real gain; the search moves elsewhere |
| n29 | new best | val 0.3732, probe 0.3919, 3.28% better than n18: Add a content-word TF-IDF view that removes English stopwords and keeps the remaining c... |
| n30 | new best | val 0.3650, probe 0.3810, 2.19% better than n29: Add a full word-level TF-IDF view on the original text with original casing, word n-gra... |
| n31 | crash | timeout: killed after 5s |
|  | stop | budget, final selection best_val |
| n30 | final pick | val 0.3650 (rank 1 of 31), test 0.3672 (rank 1 of 31) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
