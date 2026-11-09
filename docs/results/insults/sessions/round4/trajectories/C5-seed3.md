# Trajectory: C5_detecting-insults-in-social-commentary_seed3

- **Task** detecting-insults-in-social-commentary, **condition** C5, **seed** 3
- **Nodes** 35 (97% working), **budget used** 241.3 min, **LLM** 43 calls, 922,767 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Sparse bag-of-words with logistic regression, SGD linear classifiers for large-scale text, Calibrated classifiers for ranking, Random forest with probability calibration, Out-of-core naive Bayes for text, Dictionary feature extraction for text, Polynomial feature linear models
- **Search** 4 improve chains exhausted; longest stretch without a new best 9 nodes; selection regret 0.0048 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Decode the unicode/byte escape sequences and strip the wrapper quotes from each comment, then represent the... (val 0.8838) |
| n0 | new best | val 0.8838, probe 0.9083: Decode the unicode/byte escape sequences and strip the wrapper quotes from each comment... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Sparse bag-of-words with logistic regression" |
| n0 | card used | first script with TfidfVectorizer from the card "SGD linear classifiers for large-scale text" |
| n0 | card used | first script with TfidfVectorizer from the card "Random forest with probability calibration" |
| n0 | card used | first script with LogisticRegression from the card "Polynomial feature linear models" |
| n1 | draft | Use a character n-gram TF-IDF representation of the decoded comments and a linear SVM whose scores are conv... (val 0.8833) |
| n2 | draft | I will decode the CSV comments by stripping the outer wrapper quotes and interpreting backslash escapes, in... (val 0.8880) |
| n2 | new best | val 0.8880, probe 0.9203, 0.48% better than n0: I will decode the CSV comments by stripping the outer wrapper quotes and interpreting b... |
| n2 | card used | first script with HashingVectorizer from the card "Out-of-core naive Bayes for text" |
| n3 | draft | I will decode the CSV comments by stripping the wrapper quotes and unescaping the stored backslash sequence... (val 0.8432) |
| n4 | draft | I will parse the CSV comments by using `ast.literal_eval` on the quoted field to undo the outer CSV quoting... (val 0.8041) |
| n5 | new best | val 0.8908, probe 0.9188, 0.32% better than n2: I will make one targeted change to the best-performing script: expand the HashingVector... |
| n8 | new best | val 0.8909, probe 0.9184, 0.01% better than n5: Replace the approximate SGDClassifier with an exact LogisticRegression on the same hash... |
| n8 | chain exhausted | the chain from n5 had 3 attempts without a real gain; the search moves elsewhere |
| n16 | new best | val 0.8926, probe 0.9194, 0.19% better than n8: Add a small set of normalized structural features (log length, log word count, uppercas... |
| n18 | new best | val 0.8964, probe 0.9218, 0.42% better than n16: I will augment the existing structural-statistics branch with two lexicon features: a l... |
| n19 | new best | val 0.8998, probe 0.9243, 0.38% better than n18: I will add a targeted-insult interaction feature to the existing structural-statistics ... |
| n20 | new best | val 0.9012, probe 0.9277, 0.16% better than n19: I will replace the approximate HashingVectorizer with an exact CountVectorizer for the ... |
| n22 | new best | val 0.9016, probe 0.9275, 0.04% better than n20: The current best model uses exact word-boundary character n-grams with min_df=2. I will... |
| n23 | new best | val 0.9031, probe 0.9255, 0.17% better than n22: I will keep the exact word-boundary character n-gram TF-IDF pipeline and the existing s... |
| n25 | no-op | same predictions as n20: I will add `max_df=0.95` to the exact CountVectorizer so character n-grams appearing in... |
| n29 | chain exhausted | the chain from n23 had 3 attempts without a real gain; the search moves elsewhere |
| n33 | new best | val 0.9035, probe 0.9268, 0.04% better than n23: Add a metadata feature branch to the model using a ColumnTransformer, so the text branc... |
| n34 | crash | timeout: killed after 772s |
|  | stop | budget, final selection best_val |
| n33 | final pick | val 0.9035 (rank 1 of 34), test 0.9020 (rank 12 of 34) |
| n17 | best on test | test 0.9069, but val rank 16 of 34: Add a word-level hashed TF-IDF branch to the existing FeatureUnion, alongside the curre... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
