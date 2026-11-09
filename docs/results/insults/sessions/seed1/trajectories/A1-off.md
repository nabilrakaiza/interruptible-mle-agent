# Trajectory: A1-off_detecting-insults-in-social-commentary_seed1

- **Task** detecting-insults-in-social-commentary, **condition** A1-off, **seed** 1
- **Nodes** 118 (92% working), **budget used** 240.0 min, **LLM** 134 calls, 2,372,963 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Sparse text classification with TF-IDF and linear models, Probability calibration for classifiers, Calibrated random forest probabilities, Linear models with polynomial features, Out-of-core naive Bayes for large text, Benchmarking text classifiers, SGD linear classifiers for large-scale text
- **Search** 21 improve chains exhausted; longest stretch without a new best 56 nodes; selection regret 0.0052 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use a simple TF-IDF bag-of-words representation with a logistic regression classifier. Hold out 20% of the ... (val -) |
| n0 | crash | runtime_error: TypeError: only integer scalar arrays can be converted to a scalar index |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Sparse text classification with TF-IDF and linear models" |
| n0 | card used | first script with TfidfVectorizer from the card "Out-of-core naive Bayes for large text" |
| n0 | card used | first script with LogisticRegression from the card "Benchmarking text classifiers" |
| n1 | draft | Use a TF-IDF bag-of-words representation with character n-grams to capture both word-level insults and comm... (val 0.8591) |
| n1 | new best | val 0.8591, probe 0.8770: Use a TF-IDF bag-of-words representation with character n-grams to capture both word-le... |
| n2 | draft | I will build a logistic regression classifier on a combined feature set: word TF-IDF, character n-gram TF-I... (val -) |
| n2 | crash | runtime_error: exit code 1 |
| n3 | draft | I will use a character n-gram hashing vectorizer with TF-IDF weighting and a stochastic gradient descent lo... (val 0.8961) |
| n3 | new best | val 0.8961, probe 0.9043, 4.30% better than n1: I will use a character n-gram hashing vectorizer with TF-IDF weighting and a stochastic... |
| n3 | card used | first script with SGDClassifier from the card "SGD linear classifiers for large-scale text" |
| n4 | draft | I will use character n-gram TF-IDF features with a Complement Naive Bayes classifier, which is a different ... (val -) |
| n4 | crash | runtime_error: TypeError: only integer scalar arrays can be converted to a scalar index |
| n5 | fixed | debug fixed the crash in n0 after 1 attempt(s) |
| n5 | new best | val 0.8971, probe 0.9055, 0.11% better than n3: The failure was caused by passing pandas Arrow-backed Series into `train_test_split`, w... |
| n6 | fixed | debug fixed the crash in n4 after 1 attempt(s) |
| n8 | crash | runtime_error: TypeError: StringMethods.count() got an unexpected keyword argument 'regex' |
| n9 | fixed | debug fixed the crash in n2 after 2 attempt(s) |
| n10 | new best | val 0.8985, probe 0.9066, 0.16% better than n5: I will keep the same SGD logistic regression classifier and train/validation split, but... |
| n11 | new best | val 0.8986, probe 0.9063, 0.01% better than n10: I will keep the current word+character hashing feature pipeline and the same train/vali... |
| n11 | overfitting | beat n10 on validation (0.8985 -> 0.8986) but got worse on test (0.9042 -> 0.8975) |
| n12 | new best | val 0.9011, probe 0.9067, 0.28% better than n11: I will add a lightweight text-cleaning step that converts common unicode and escape seq... |
| n15 | chain exhausted | the chain from n12 had 3 attempts without a real gain; the search moves elsewhere |
| n22 | new best | val 0.9052, probe 0.9097, 0.45% better than n12: Replace the SGD classifier with exact LogisticRegression (lbfgs) while keeping the same... |
| n24 | new best | val 0.9054, probe 0.9113, 0.03% better than n22: Change the word-level hashing features from bigrams to word trigrams by setting `ngram_... |
| n25 | chain exhausted | the chain from n22 had 3 attempts without a real gain; the search moves elsewhere |
| n38 | no-op | same predictions as n17: The current SGD logistic regression is run with max_iter=1000 and tol=1e-4, so it can s... |
| n39 | crash | runtime_error: AttributeError: 'BM25Transformer' object has no attribute 'fit_transform'. Did you mean: 'transform'? |
| n40 | new best | val 0.9085, probe 0.9096, 0.34% better than n24: Extend the existing text cleaning step to normalize URLs, email addresses, and @usernam... |
| n43 | fixed | debug fixed the crash in n39 after 1 attempt(s) |
| n44 | chain exhausted | the chain from n40 had 3 attempts without a real gain; the search moves elsewhere |
| n48 | new best | val 0.9088, probe 0.9030, 0.04% better than n40: Replace the fixed `class_weight="balanced"` with a small grid search over positive-clas... |
| n48 | chain exhausted | the chain from n43 had 3 attempts without a real gain; the search moves elsewhere |
| n71 | overfitting | beat n68 on validation (0.9032 -> 0.9055) but got worse on test (0.9037 -> 0.8957) |
| n79 | crash | runtime_error: ImportError: cannot import name 'BM25Transformer' from 'sklearn.feature_extraction.text' (/tmp/venv/lib/python3.13/site-packages/sklearn/... |
| n80 | crash | generation_error: empty reply |
| n83 | no-op | same predictions as n82: Keep the current cleaning, hashed word/character TF-IDF features, and LogisticRegressio... |
| n89 | no-op | same predictions as n87: Keep the hashed word/character TF-IDF features and alpha grid exactly as they are, but ... |
| n93 | crash | runtime_error: ImportError: cannot import name 'BM25Transformer' from 'sklearn.feature_extraction.text' (/tmp/venv/lib/python3.13/site-packages/sklearn/... |
| n95 | fixed | debug fixed the crash in n93 after 1 attempt(s) |
| n96 | overfitting | beat n94 on validation (0.9065 -> 0.9066) but got worse on test (0.9061 -> 0.9037) |
| n100 | no-op | same predictions as n99: The current alpha grid is coarse and may place the best regularization between or beyon... |
| n103 | no-op | same predictions as n90: Remove the whitespace-collapsing step in `clean_comment` (`re.sub(r"\s+", " ", text)`).... |
| n105 | new best | val 0.9093, probe 0.9122, 0.06% better than n48: Replace the approximate SGDClassifier with an exact full-batch LogisticRegression (lbfg... |
| n107 | new best | val 0.9108, probe 0.9135, 0.16% better than n105: Extend the logistic-regression model-selection loop to also search over class_weight se... |
| n108 | new best | val 0.9162, probe 0.9143, 0.59% better than n107: Add a compact block of handcrafted binary features to the existing hashed TF-IDF matrix... |
| n108 | overfitting | beat n107 on validation (0.9108 -> 0.9162) but got worse on test (0.9070 -> 0.9004) |
| n109 | new best | val 0.9167, probe 0.9220, 0.05% better than n108: Add two binary interaction features to the existing handcrafted block: one that fires w... |
| n110 | new best | val 0.9180, probe 0.9173, 0.14% better than n109: Add a new handcrafted binary feature that fires when a second-person pronoun (you, your... |
| n111 | new best | val 0.9186, probe 0.9194, 0.07% better than n110: Add a new handcrafted binary feature that fires only for canonical direct-attack constr... |
| n112 | new best | val 0.9191, probe 0.9182, 0.06% better than n111: Add a new handcrafted binary feature for direct-address insults: a second-person pronou... |
| n113 | chain exhausted | the chain from n110 had 3 attempts without a real gain; the search moves elsewhere |
| n115 | new best | val 0.9192, probe 0.9156, 0.01% better than n112: Add one new handcrafted binary feature that detects common insulting phrases and direct... |
| n115 | overfitting | beat n114 on validation (0.9189 -> 0.9192) but got worse on test (0.9040 -> 0.9021) |
| n116 | no-op | same predictions as n115: Add one new handcrafted binary feature that detects vocative/direct-address insults: an... |
| n117 | crash | timeout: killed after 576s |
| n117 | chain exhausted | the chain from n114 had 3 attempts without a real gain; the search moves elsewhere |
|  | stop | budget, final selection best_val |
| n115 | final pick | val 0.9192 (rank 1 of 109), test 0.9021 (rank 51 of 109) |
| n110 | best on test | test 0.9073, but val rank 6 of 109: Add a new handcrafted binary feature that fires when a second-person pronoun (you, your... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
