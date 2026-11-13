# Trajectory: C5_spooky-author-identification_seed3

- **Task** spooky-author-identification, **condition** C5, **seed** 3
- **Nodes** 131 (98% working), **budget used** 240.1 min, **LLM** 145 calls, 2,474,996 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Sparse TF-IDF text classification with linear models, Multiclass temperature scaling for calibrated probabilities, One-vs-rest probability calibration for multiclass text models, Out-of-core Naive Bayes for large text corpora, Memory-efficient hashed or dictionary text features, Tuned text feature extraction and classification pipeline
- **Search** 20 improve chains exhausted; longest stretch without a new best 18 nodes; selection regret 0.0 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF vectorization (word unigrams and bigrams, sublinear term frequency, English stop-word removal, a... (val 0.6115) |
| n0 | new best | val 0.6115, probe 0.6124: Use TF-IDF vectorization (word unigrams and bigrams, sublinear term frequency, English ... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Sparse TF-IDF text classification with linear models" |
| n0 | card used | first script with TfidfVectorizer from the card "Tuned text feature extraction and classification pipeline" |
| n1 | draft | I will use a TF-IDF pipeline (word 1-2 grams, sublinear term frequencies, English stop-word removal, and fr... (val 0.5084) |
| n1 | new best | val 0.5084, probe 0.5056, 16.86% better than n0: I will use a TF-IDF pipeline (word 1-2 grams, sublinear term frequencies, English stop-... |
| n1 | card used | first script with MultinomialNB from the card "Out-of-core Naive Bayes for large text corpora" |
| n2 | draft | I’ll build a text classifier using character n-gram TF-IDF features (2-5 grams with word boundaries) to cap... (val 0.5983) |
| n3 | draft | I will use a memory-efficient hashing vectorizer (word unigrams and bigrams) followed by TF-IDF transformat... (val 0.5779) |
| n3 | card used | first script with TfidfTransformer from the card "Memory-efficient hashed or dictionary text features" |
| n4 | draft | I will use a memory-efficient hashing vectorizer for word unigrams and bigrams, avoiding a fixed vocabulary... (val 0.5946) |
| n5 | new best | val 0.5001, probe 0.4994, 1.64% better than n1: The current best uses MultinomialNB, which often produces poorly calibrated and biased ... |
| n6 | new best | val 0.4977, probe 0.4968, 0.47% better than n5: The current best model uses ComplementNB with its default alpha=1.0 on TF-IDF features.... |
| n7 | new best | val 0.4976, probe 0.4968, 0.01% better than n6: The current best model uses word unigram and bigram TF-IDF features with ComplementNB a... |
| n8 | new best | val 0.4518, probe 0.4483, 9.21% better than n7: Keep the existing word unigram/bigram/trigram TF-IDF stream, ComplementNB classifier, a... |
| n9 | new best | val 0.4207, probe 0.4043, 6.89% better than n8: Keep the current word+character TF-IDF ComplementNB pipeline and calibration. The only ... |
| n11 | new best | val 0.4128, probe 0.3972, 1.88% better than n9: Keep the current word+character TF-IDF FeatureUnion, ComplementNB, and sigmoid calibrat... |
| n12 | new best | val 0.4001, probe 0.3882, 3.06% better than n11: Increase the number of folds in the existing sigmoid calibration from 3 to 5 while keep... |
| n13 | new best | val 0.3816, probe 0.3707, 4.64% better than n12: Lower min_df from 3 to 2 in both TfidfVectorizer blocks so rare word and character n-gr... |
| n14 | new best | val 0.3764, probe 0.3649, 1.36% better than n13: Lower ComplementNB's smoothing alpha from 0.1 to 0.05 while keeping the word+character ... |
| n15 | new best | val 0.3751, probe 0.3629, 0.33% better than n14: Halve ComplementNB's smoothing alpha from 0.05 to 0.025, keeping the word+character TF-... |
| n18 | chain exhausted | the chain from n15 had 3 attempts without a real gain; the search moves elsewhere |
| n19 | new best | val 0.3726, probe 0.3614, 0.68% better than n15: Replace the sigmoid calibration in CalibratedClassifierCV with isotonic calibration whi... |
| n20 | new best | val 0.3708, probe 0.3600, 0.49% better than n19: Lower ComplementNB's smoothing alpha from 0.05 to 0.03 while keeping the word+character... |
| n22 | new best | val 0.3706, probe 0.3597, 0.04% better than n20: Widen the character n-gram range from (2,5) to (1,5) in the existing char_wb TF-IDF str... |
| n23 | chain exhausted | the chain from n20 had 3 attempts without a real gain; the search moves elsewhere |
| n24 | crash | runtime_error: TypeError: CalibratedClassifierCV.__init__() got an unexpected keyword argument 'random_state' |
| n25 | fixed | debug fixed the crash in n24 after 1 attempt(s) |
| n29 | new best | val 0.3578, probe 0.3438, 3.47% better than n22: Lower the word TF-IDF stream's `min_df` from 2 to 1 while keeping the character n-gram ... |
| n30 | new best | val 0.3553, probe 0.3420, 0.68% better than n29: The current best pipeline keeps word TF-IDF at `min_df=1` but character n-grams at `min... |
| n33 | no-op | same predictions as n30: Keep the tuned word+character TF-IDF FeatureUnion, ComplementNB, and 5-fold isotonic ca... |
| n33 | chain exhausted | the chain from n30 had 3 attempts without a real gain; the search moves elsewhere |
| n46 | new best | val 0.3539, probe 0.3410, 0.42% better than n30: Switch the calibration method in CalibratedClassifierCV from sigmoid to isotonic while ... |
| n49 | chain exhausted | the chain from n46 had 3 attempts without a real gain; the search moves elsewhere |
| n54 | no-op | same predictions as n51: Change only the word TfidfVectorizer's `max_df` from 0.9 to 1.0, so very frequent word ... |
| n58 | new best | val 0.3496, probe 0.3337, 1.21% better than n46: Keep the pre-fitted word+character TF-IDF pipeline with ComplementNB and 5-fold isotoni... |
| n61 | chain exhausted | the chain from n58 had 3 attempts without a real gain; the search moves elsewhere |
| n62 | overfitting | beat n56 on validation (0.3539 -> 0.3539) but got worse on test (0.3597 -> 0.3642) |
| n66 | new best | val 0.3493, probe 0.3378, 0.07% better than n58: Keep the pre-fitted word+character_wb TF-IDF pipeline and isotonic-calibrated Complemen... |
| n68 | new best | val 0.3489, probe 0.3385, 0.11% better than n66: Lower ComplementNB's additive smoothing from alpha=0.035 to alpha=0.030 while keeping t... |
| n71 | new best | val 0.3480, probe 0.3367, 0.28% better than n68: Add a supplementary word-level TF-IDF stream that extracts only single-character word t... |
| n75 | chain exhausted | the chain from n71 had 3 attempts without a real gain; the search moves elsewhere |
| n79 | new best | val 0.3451, probe 0.3321, 0.81% better than n71: Keep the pre-fitted word+character_wb TF-IDF stack and isotonic-calibrated ComplementNB... |
| n83 | chain exhausted | the chain from n79 had 3 attempts without a real gain; the search moves elsewhere |
| n84 | overfitting | beat n64 on validation (0.3539 -> 0.3539) but got worse on test (0.3597 -> 0.3642) |
| n98 | new best | val 0.3445, probe 0.3307, 0.19% better than n79: Change only the CalibratedClassifierCV configuration by setting `ensemble=False` instea... |
| n101 | chain exhausted | the chain from n98 had 3 attempts without a real gain; the search moves elsewhere |
| n104 | new best | val 0.3410, probe 0.3249, 1.01% better than n98: Modify only the word-level TfidfVectorizer’s token pattern so that, in addition to the ... |
| n105 | new best | val 0.3406, probe 0.3249, 0.11% better than n104: Add a small set of sentence-level stylometric features as extra columns to the existing... |
| n109 | chain exhausted | the chain from n105 had 3 attempts without a real gain; the search moves elsewhere |
| n110 | new best | val 0.3363, probe 0.3203, 1.27% better than n105: Add a complementary lowercased word-level TF-IDF stream alongside the existing case-sen... |
| n112 | new best | val 0.3251, probe 0.3113, 3.34% better than n110: Tune the ComplementNB smoothing and weighting hyperparameters (`alpha` and `norm`) on a... |
| n115 | new best | val 0.3191, probe 0.3109, 1.84% better than n112: Add a second model family, SGDClassifier with log loss, to the holdout model selection ... |
| n116 | new best | val 0.3184, probe 0.3109, 0.22% better than n115: Add a third model family—a calibrated linear SVM (SGDClassifier with hinge loss)—to the... |
| n117 | new best | val 0.3183, probe 0.3113, 0.03% better than n116: Replace the coarse 0.1-step grid search over the three blend weights with a continuous ... |
| n120 | chain exhausted | the chain from n116 had 3 attempts without a real gain; the search moves elsewhere |
| n122 | new best | val 0.3021, probe 0.2976, 5.09% better than n117: Keep the existing pre-fitted TF-IDF streams, holdout tuning of ComplementNB and SGD, an... |
| n123 | new best | val 0.3015, probe 0.2987, 0.17% better than n122: Add a compact set of sentence-shape and punctuation-density features as a fourth sparse... |
| n124 | new best | val 0.3014, probe 0.2987, 0.05% better than n123: Add a compact stylometric feature block to the existing handcrafted sparse stream: coun... |
| n126 | chain exhausted | the chain from n123 had 3 attempts without a real gain; the search moves elsewhere |
| n128 | new best | val 0.2969, probe 0.2973, 1.50% better than n124: Keep the existing TF-IDF streams, holdout tuning, and isotonic-calibrated model fits un... |
| n130 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n128 | final pick | val 0.2969 (rank 1 of 129), test 0.3001 (rank 1 of 129) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
