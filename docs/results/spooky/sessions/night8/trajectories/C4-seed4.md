# Trajectory: C4_spooky-author-identification_seed4

- **Task** spooky-author-identification, **condition** C4, **seed** 4
- **Nodes** 159 (99% working), **budget used** 240.0 min, **LLM** 176 calls, 2,912,642 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Sparse TF-IDF with linear classifier, Multinomial naive Bayes for text, Multiclass probability calibration, Temperature scaling for logit classifiers, DictVectorizer and feature hashing for symbolic features, Polynomial feature linear models
- **Search** 25 improve chains exhausted; longest stretch without a new best 40 nodes; selection regret 0.0 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I’ll load the labeled training text and the unlabeled prediction text. I’ll convert the sentences to TF-IDF... (val 0.6115) |
| n0 | new best | val 0.6115, probe 0.6124: I’ll load the labeled training text and the unlabeled prediction text. I’ll convert the... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Sparse TF-IDF with linear classifier" |
| n0 | card used | first script with TfidfVectorizer from the card "Multinomial naive Bayes for text" |
| n0 | card used | first script with LogisticRegression from the card "DictVectorizer and feature hashing for symbolic features" |
| n0 | card used | first script with LogisticRegression from the card "Polynomial feature linear models" |
| n1 | draft | I’ll use a Multinomial Naive Bayes classifier on TF-IDF text features, which is a different model family fr... (val 0.4636) |
| n1 | new best | val 0.4636, probe 0.4656, 24.18% better than n0: I’ll use a Multinomial Naive Bayes classifier on TF-IDF text features, which is a diffe... |
| n2 | draft | I will use character n-gram TF-IDF features instead of word-level features to capture stylistic writing pat... (val 0.5284) |
| n3 | draft | I will use word unigram and bigram TF-IDF features, reduce them to 100 dense components with TruncatedSVD, ... (val 0.8566) |
| n4 | draft | I will represent each sentence with TF-IDF features using word unigrams and bigrams with sublinear term wei... (val 0.7854) |
| n5 | crash | runtime_error: ImportError: cannot import name 'FeatureUnion' from 'sklearn.feature_extraction.text' (/usr/local/lib/python3.13/site-packages/sklearn/fe... |
| n6 | fixed | debug fixed the crash in n5 after 1 attempt(s) |
| n8 | chain exhausted | the chain from n1 had 3 attempts without a real gain; the search moves elsewhere |
| n9 | new best | val 0.4547, probe 0.4465, 1.93% better than n1: I will make one targeted change to the current best script: remove the English stop-wor... |
| n10 | new best | val 0.4547, probe 0.4463, 0.00% better than n9: The current script already keeps English stop words, but its TF-IDF vectorizers still u... |
| n11 | new best | val 0.4189, probe 0.4071, 7.87% better than n10: I will replace the MultinomialNB base estimator with ComplementNB, which is often more ... |
| n12 | new best | val 0.4129, probe 0.4016, 1.43% better than n11: I will increase the number of folds in CalibratedClassifierCV from 3 to 5. This gives e... |
| n13 | new best | val 0.3964, probe 0.3889, 3.99% better than n12: I will keep the strong word+character TF-IDF FeatureUnion and calibrated ComplementNB c... |
| n14 | no-op | same predictions as n13: I will keep the current FeatureUnion of word and character TF-IDF, ComplementNB, and si... |
| n15 | new best | val 0.3850, probe 0.3741, 2.87% better than n13: Keep the existing word+character TF-IDF FeatureUnion, alpha grid search, and sigmoid ca... |
| n18 | new best | val 0.3779, probe 0.3674, 1.87% better than n15: Keep the current word+character TF-IDF FeatureUnion, ComplementNB alpha grid search, an... |
| n20 | new best | val 0.3779, probe 0.3665, 0.00% better than n18: Keep the current word+character TF-IDF FeatureUnion, ComplementNB alpha search, and sig... |
| n21 | new best | val 0.3778, probe 0.3662, 0.02% better than n20: Keep the current word+character TF-IDF FeatureUnion, ComplementNB alpha search, and sig... |
| n22 | new best | val 0.3772, probe 0.3629, 0.16% better than n21: Keep the current word (1,5) and char_wb (3,5) TF-IDF FeatureUnion with ComplementNB alp... |
| n23 | new best | val 0.3746, probe 0.3594, 0.69% better than n22: Keep the current word TF-IDF, character TF-IDF, punctuation TF-IDF FeatureUnion, Comple... |
| n24 | no-op | same predictions as n23: Add a lightweight text normalizer and apply it to all three TF-IDF vectorizers so curly... |
| n25 | new best | val 0.3608, probe 0.3442, 3.67% better than n23: Keep the existing word/char/punct TF-IDF FeatureUnion, ComplementNB alpha search, and s... |
| n26 | no-op | same predictions as n25: Keep the existing word/char/punct TF-IDF FeatureUnion, transductive fitting on train+te... |
| n29 | new best | val 0.3582, probe 0.3414, 0.74% better than n25: Keep the entire transductive TF-IDF FeatureUnion, ComplementNB alpha search, and predic... |
| n30 | new best | val 0.3572, probe 0.3411, 0.27% better than n29: Add a new style-pattern TF-IDF vectorizer to the existing FeatureUnion. The custom anal... |
| n31 | new best | val 0.3570, probe 0.3396, 0.04% better than n30: Add a dedicated function-word sequence TF-IDF vectorizer to the existing FeatureUnion. ... |
| n33 | new best | val 0.3465, probe 0.3342, 2.96% better than n31: I will split the word-level features: change the existing word TF-IDF vectorizer to pro... |
| n36 | new best | val 0.3445, probe 0.3420, 0.56% better than n33: Add a skip-gram TF-IDF vectorizer to the existing FeatureUnion. It extracts word pairs ... |
| n40 | new best | val 0.3434, probe 0.3370, 0.33% better than n36: Extend the existing skip-gram feature extractor so that, in addition to the current one... |
| n41 | new best | val 0.3423, probe 0.3383, 0.32% better than n40: Extend the existing skip-gram feature extractor so that, in addition to the current one... |
| n43 | no-op | same predictions as n41: Change only the model-selection step. Instead of picking the ComplementNB smoothing alp... |
| n44 | chain exhausted | the chain from n41 had 3 attempts without a real gain; the search moves elsewhere |
| n45 | new best | val 0.3402, probe 0.3331, 0.63% better than n41: The current punctuation vectorizer passes a callable analyzer, so scikit-learn ignores ... |
| n48 | chain exhausted | the chain from n45 had 3 attempts without a real gain; the search moves elsewhere |
| n61 | overfitting | beat n49 on validation (0.3465 -> 0.3465) but got worse on test (0.3547 -> 0.3562) |
| n70 | no-op | same predictions as n69: Currently alpha is selected by raw ComplementNB log loss, but the final pipeline applie... |
| n86 | new best | val 0.3396, probe 0.3339, 0.16% better than n45: Expand the skip-gram tokenizer from index gaps 2–3 to include index gap 4, so it captur... |
| n90 | new best | val 0.3385, probe 0.3314, 0.34% better than n86: Extend the punctuation analyzer so it also emits trigrams of consecutive punctuation ch... |
| n93 | chain exhausted | the chain from n90 had 3 attempts without a real gain; the search moves elsewhere |
| n94 | no-op | same predictions as n86: Lower the unigram vectorizer’s min_df from 2 to 1 so that words appearing in only a sin... |
| n106 | no-op | same predictions as n105: Extend the punctuation TF-IDF feature extractor to also emit trigrams by changing its n... |
| n110 | no-op | same predictions as n108: Replace the coarse ComplementNB alpha grid with a finer grid spanning 0.1 to 1.0 in ste... |
| n111 | no-op | same predictions as n108: Keep the existing feature union and isotonic calibration unchanged. Change only the smo... |
| n112 | new best | val 0.3241, probe 0.3219, 4.24% better than n90: Add a case-preserving word TF-IDF vectorizer to the FeatureUnion. The current word vect... |
| n115 | new best | val 0.3225, probe 0.3221, 0.49% better than n112: The current case-preserving word vectorizer uses a callable analyzer, so scikit-learn i... |
| n118 | chain exhausted | the chain from n115 had 3 attempts without a real gain; the search moves elsewhere |
| n119 | new best | val 0.3182, probe 0.3167, 1.33% better than n115: Add a stylometric summary TF-IDF vectorizer to the FeatureUnion. It emits document-leve... |
| n120 | new best | val 0.3164, probe 0.3161, 0.58% better than n119: Add a lexical-diversity stylometric vectorizer to the FeatureUnion. Its callable analyz... |
| n124 | chain exhausted | the chain from n120 had 3 attempts without a real gain; the search moves elsewhere |
| n129 | new best | val 0.3153, probe 0.3113, 0.34% better than n120: Replace the raw uncalibrated alpha selection with a nested calibration-aware selection:... |
| n132 | new best | val 0.3132, probe 0.3099, 0.69% better than n129: Replace the integer `cv=5` in every `CalibratedClassifierCV` with a seeded, shuffled `S... |
| n132 | overfitting | beat n129 on validation (0.3153 -> 0.3132) but got worse on test (0.3275 -> 0.3302) |
| n135 | chain exhausted | the chain from n132 had 3 attempts without a real gain; the search moves elsewhere |
| n147 | no-op | same predictions as n146: Change only the alpha-selection step so it scores each ComplementNB alpha after isotoni... |
| n148 | new best | val 0.3107, probe 0.3102, 0.78% better than n132: Replace the 5-fold StratifiedKFold used for alpha selection and out-of-fold calibration... |
| n150 | new best | val 0.3082, probe 0.3088, 0.81% better than n148: Add a compact document-level stylometric TF-IDF vectorizer to the FeatureUnion. It enco... |
| n151 | no-op | same predictions as n150: Normalize typographic punctuation before any feature extraction by mapping Unicode curl... |
| n153 | chain exhausted | the chain from n150 had 3 attempts without a real gain; the search moves elsewhere |
| n158 | crash | timeout: killed after 17s |
|  | stop | budget, final selection best_val |
| n150 | final pick | val 0.3082 (rank 1 of 157), test 0.3236 (rank 1 of 157) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
