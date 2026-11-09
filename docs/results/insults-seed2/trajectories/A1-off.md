# Trajectory: A1-off_detecting-insults-in-social-commentary_seed2

- **Task** detecting-insults-in-social-commentary, **condition** A1-off, **seed** 2
- **Nodes** 74 (95% working), **budget used** 240.6 min, **LLM** 85 calls, 1,657,576 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Random forest with sigmoid probability calibration, Stochastic gradient descent linear text classifiers, Out-of-core naive Bayes for text, Calibrated classifier ensemble for probability outputs, Polynomial feature expansion with linear models, Custom stop words and n-gram text vectorization, Encoding-aware text preprocessing for vectorization, Benchmarking text classifiers by accuracy and speed
- **Search** 14 improve chains exhausted; longest stretch without a new best 17 nodes; selection regret 0.0016 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF word unigrams and bigrams as features with a logistic regression classifier. Clean comments by s... (val 0.8660) |
| n0 | new best | val 0.8660, probe 0.8841: Use TF-IDF word unigrams and bigrams as features with a logistic regression classifier.... |
| n0 | card used | first script with TfidfVectorizer from the card "Random forest with sigmoid probability calibration" |
| n0 | card used | first script with TfidfVectorizer from the card "Stochastic gradient descent linear text classifiers" |
| n0 | card used | first script with TfidfVectorizer from the card "Custom stop words and n-gram text vectorization" |
| n1 | draft | Use a hashing vectorizer over character n-grams (2-5) rather than word TF-IDF, feeding a logistic-loss SGD ... (val 0.8802) |
| n1 | new best | val 0.8802, probe 0.8959, 1.65% better than n0: Use a hashing vectorizer over character n-grams (2-5) rather than word TF-IDF, feeding ... |
| n1 | card used | first script with HashingVectorizer from the card "Out-of-core naive Bayes for text" |
| n2 | draft | I will build a text classifier using TF-IDF word unigrams and bigrams fed into a Complement Naive Bayes mod... (val 0.7563) |
| n3 | draft | I will use character n-gram TF-IDF features with an L2-regularized logistic regression classifier, which is... (val 0.8886) |
| n3 | new best | val 0.8886, probe 0.9037, 0.96% better than n1: I will use character n-gram TF-IDF features with an L2-regularized logistic regression ... |
| n4 | draft | I will build a two-model probability ensemble on cleaned comment text: a logistic regression on TF-IDF word... (val -) |
| n4 | crash | runtime_error: TypeError: only integer scalar arrays can be converted to a scalar index |
| n5 | new best | val 0.8914, probe 0.9053, 0.31% better than n3: I will keep the existing character n-gram TF-IDF logistic regression pipeline but augme... |
| n6 | fixed | debug fixed the crash in n4 after 1 attempt(s) |
| n6 | new best | val 0.8917, probe 0.9013, 0.03% better than n5: The crash was caused by passing a pandas Arrow-backed string column to sklearn's cross_... |
| n7 | new best | val 0.9012, probe 0.9120, 1.07% better than n6: I will add a third model to the existing ensemble: a character n-gram TF-IDF logistic r... |
| n8 | new best | val 0.9026, probe 0.9151, 0.16% better than n7: I will keep the three-model ensemble identical but replace the fixed equal-weight avera... |
| n9 | no-op | same predictions as n8: I will add a fourth base model to the ensemble: a BernoulliNB classifier trained on bin... |
| n11 | chain exhausted | the chain from n8 had 3 attempts without a real gain; the search moves elsewhere |
| n18 | new best | val 0.9029, probe 0.9168, 0.03% better than n8: Add a third base model to the ensemble: a character n-gram HashingVectorizer (char_wb, ... |
| n19 | new best | val 0.9051, probe 0.9171, 0.24% better than n18: Add a fourth base model to the ensemble: a word-level TF-IDF logistic regression using ... |
| n22 | new best | val 0.9051, probe 0.9170, 0.00% better than n19: Increase the capacity of the character n-gram TF-IDF logistic regression, which is the ... |
| n22 | chain exhausted | the chain from n19 had 3 attempts without a real gain; the search moves elsewhere |
| n23 | no-op | same predictions as n17: Increase the number of folds in StratifiedKFold from 5 to 10 so each out-of-fold model ... |
| n24 | new best | val 0.9053, probe 0.9129, 0.03% better than n22: Replace the character n-gram TF-IDF logistic regression pipeline with a FeatureUnion th... |
| n25 | new best | val 0.9057, probe 0.9135, 0.04% better than n24: Give the word TF-IDF branch inside the FeatureUnion its own higher-capacity vectorizer ... |
| n26 | new best | val 0.9083, probe 0.9186, 0.29% better than n25: Tune the ensemble weight between the two existing out-of-fold prediction vectors instea... |
| n27 | new best | val 0.9095, probe 0.9192, 0.14% better than n26: Add a cross-word character n-gram TF-IDF branch to the logistic regression FeatureUnion... |
| n28 | new best | val 0.9097, probe 0.9186, 0.01% better than n27: Add a repeated-character normalization step to the shared text cleaner. Emphatic spelli... |
| n29 | new best | val 0.9099, probe 0.9193, 0.03% better than n28: Replace the fixed `class_weight='balanced'` in the logistic regression branch with a sm... |
| n30 | crash | timeout: killed after 1200s |
| n30 | chain exhausted | the chain from n27 had 3 attempts without a real gain; the search moves elsewhere |
| n31 | fixed | debug fixed the crash in n30 after 1 attempt(s) |
| n32 | no-op | same predictions as n26: Tune the BernoulliNB smoothing alpha in addition to the ensemble weight. Instead of fix... |
| n40 | new best | val 0.9103, probe 0.9213, 0.05% better than n29: Change the word tokenization pattern from `\b\w+\b` (which discards punctuation) to a p... |
| n42 | new best | val 0.9103, probe 0.9185, 0.00% better than n40: Add a case-sensitive word TF-IDF branch to the logistic-regression FeatureUnion. All cu... |
| n42 | chain exhausted | the chain from n39 had 3 attempts without a real gain; the search moves elsewhere |
| n47 | no-op | same predictions as n31: Add a third base model to the ensemble: a BernoulliNB on binary character n-grams (anal... |
| n51 | crash | runtime_error: NameError: name 'Pipeline' is not defined |
| n52 | fixed | debug fixed the crash in n51 after 1 attempt(s) |
| n54 | no-op | same predictions as n52: Change the out-of-fold evaluation from 5-fold to 10-fold StratifiedKFold. This trains e... |
| n57 | no-op | same predictions as n55: Add a third base model to the ensemble: a random forest trained on a 100-component Trun... |
| n60 | new best | val 0.9113, probe 0.9251, 0.10% better than n42: Replace the raw integer hour/dayofweek/month date features with cyclical sin/cos encodi... |
| n61 | new best | val 0.9114, probe 0.9253, 0.01% better than n60: Replace the single-split ensemble-weight search with a direct optimization of the ensem... |
| n63 | chain exhausted | the chain from n60 had 3 attempts without a real gain; the search moves elsewhere |
| n65 | new best | val 0.9118, probe 0.9263, 0.04% better than n61: Add second-harmonic sine/cosine encodings for hour and day-of-week to the temporal feat... |
| n67 | chain exhausted | the chain from n64 had 3 attempts without a real gain; the search moves elsewhere |
| n73 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n65 | final pick | val 0.9118 (rank 1 of 70), test 0.9127 (rank 9 of 70) |
| n40 | best on test | test 0.9143, but val rank 10 of 70: Change the word tokenization pattern from `\b\w+\b` (which discards punctuation) to a p... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
