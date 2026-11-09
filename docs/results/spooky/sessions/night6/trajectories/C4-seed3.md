# Trajectory: C4_spooky-author-identification_seed3

- **Task** spooky-author-identification, **condition** C4, **seed** 3
- **Nodes** 55 (96% working), **budget used** 240.8 min, **LLM** 63 calls, 1,052,182 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Temperature-scaled multiclass text classifier, Tfidf bag-of-words with linear classifiers, Sparse dictionary-feature text classification, Out-of-core naive Bayes for large text corpora, Multiclass probability calibration via one-vs-rest, Feature hashing for text classification
- **Search** 2 improve chains exhausted; longest stretch without a new best 7 nodes; selection regret 0.0 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF word and bigram features with sublinear scaling and English stop-word removal to represent each ... (val 0.6149) |
| n0 | new best | val 0.6149, probe 0.6166: Use TF-IDF word and bigram features with sublinear scaling and English stop-word remova... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Tfidf bag-of-words with linear classifiers" |
| n0 | card used | first script with TfidfVectorizer from the card "Out-of-core naive Bayes for large text corpora" |
| n1 | draft | Use character-level TF-IDF features instead of word/bigram features to capture stylistic and orthographic p... (val 0.5267) |
| n1 | new best | val 0.5267, probe 0.5228, 14.34% better than n0: Use character-level TF-IDF features instead of word/bigram features to capture stylisti... |
| n2 | draft | Use feature hashing to avoid building an explicit vocabulary: hash word unigrams and bigrams into a fixed-s... (val 0.6686) |
| n2 | card used | first script with TfidfTransformer from the card "Sparse dictionary-feature text classification" |
| n2 | card used | first script with HashingVectorizer, TfidfTransformer from the card "Feature hashing for text classification" |
| n3 | draft | Use TF-IDF word unigrams and bigrams with sublinear term frequency, keeping function words because they are... (val -) |
| n3 | crash | runtime_error: TypeError: CalibratedClassifierCV.__init__() got an unexpected keyword argument 'random_state' |
| n4 | draft | Use a hybrid sparse text representation that combines word-level TF-IDF (unigrams and bigrams, sublinear te... (val 0.4643) |
| n4 | new best | val 0.4643, probe 0.4619, 11.85% better than n1: Use a hybrid sparse text representation that combines word-level TF-IDF (unigrams and b... |
| n5 | fixed | debug fixed the crash in n3 after 1 attempt(s) |
| n6 | new best | val 0.4063, probe 0.4089, 12.49% better than n4: Keep the hybrid word+character TF-IDF representation and the multinomial logistic regre... |
| n7 | new best | val 0.4050, probe 0.4079, 0.32% better than n6: Keep the hybrid word + character TF-IDF representation and the regularized multinomial ... |
| n9 | new best | val 0.3800, probe 0.3904, 6.17% better than n7: Add temperature scaling to recalibrate the multinomial logistic regression probabilitie... |
| n10 | no-op | same predictions as n9: Change the model-selection criterion so that the regularization strength C is chosen by... |
| n12 | chain exhausted | the chain from n9 had 3 attempts without a real gain; the search moves elsewhere |
| n17 | new best | val 0.3740, probe 0.3780, 1.58% better than n9: Add a fifth TF-IDF stream using word-level n-grams with `lowercase=False` and a token p... |
| n18 | new best | val 0.3684, probe 0.3720, 1.51% better than n17: Add a sixth TF-IDF stream that tokenizes case-sensitive words and punctuation runs as s... |
| n21 | new best | val 0.3663, probe 0.3701, 0.55% better than n18: Add a seventh TF-IDF stream based on word/punctuation skip-bigrams. For each pair of to... |
| n24 | new best | val 0.3663, probe 0.3701, 0.00% better than n21: Replace the final single logistic-regression model (selected by validation C) with a we... |
| n25 | new best | val 0.3654, probe 0.3698, 0.25% better than n24: Add a new TF-IDF feature stream based on long cross-boundary character n-grams (analyze... |
| n26 | new best | val 0.3634, probe 0.3692, 0.57% better than n25: Add temperature scaling to the ensemble probabilities instead of using the raw weighted... |
| n29 | new best | val 0.3630, probe 0.3703, 0.11% better than n26: Replace the single scalar temperature used for calibration with per-class temperatures ... |
| n30 | new best | val 0.3614, probe 0.3696, 0.42% better than n29: Replace the per-class temperature calibration with a full vector scaling calibration th... |
| n31 | new best | val 0.3612, probe 0.3690, 0.07% better than n30: Replace the final vector-scaling calibration with a strictly more general full matrix s... |
| n32 | new best | val 0.3576, probe 0.3681, 0.98% better than n31: Add a lowercased character-level TF-IDF stream using char_wb n-grams of length 2-5, cap... |
| n34 | no-op | same predictions as n32: Add a stochastic gradient descent logistic regression model (`SGDClassifier` with `loss... |
| n35 | new best | val 0.3540, probe 0.3647, 1.02% better than n32: Replace the hand-tuned ensemble-weight and temperature/vector/matrix calibration block ... |
| n36 | new best | val 0.3539, probe 0.3645, 0.01% better than n35: Standardize the out-of-fold logits before feeding them to the stacking meta-learner. Th... |
| n39 | new best | val 0.3525, probe 0.3634, 0.39% better than n36: Add a lowercased cross-boundary character TF-IDF stream (analyzer='char', ngram_range=(... |
| n41 | new best | val 0.3518, probe 0.3637, 0.22% better than n39: Change the stacker input from raw out-of-fold logits only to both logits and their soft... |
| n43 | new best | val 0.3513, probe 0.3633, 0.12% better than n41: Broaden the base-model ensemble by expanding the logistic-regression regularization gri... |
| n44 | new best | val 0.3457, probe 0.3595, 1.60% better than n43: Add a specialized base logistic-regression model trained only on the word/punctuation T... |
| n45 | new best | val 0.3454, probe 0.3596, 0.09% better than n44: Add a second specialist base model to the stacking ensemble, trained only on the existi... |
| n46 | new best | val 0.3427, probe 0.3583, 0.78% better than n45: Add a third specialist base model to the stacking ensemble, trained only on the existin... |
| n47 | new best | val 0.3422, probe 0.3585, 0.14% better than n46: Add a fourth specialist base model to the stacking ensemble, trained only on the existi... |
| n48 | new best | val 0.3396, probe 0.3587, 0.76% better than n47: Add a fifth specialist base model to the stacking ensemble, trained only on the existin... |
| n49 | new best | val 0.3389, probe 0.3592, 0.23% better than n48: Add a sixth specialist base model to the stacking ensemble, trained only on the existin... |
| n51 | new best | val 0.3199, probe 0.3301, 5.59% better than n49: Add one new stacking base model: a ComplementNB classifier trained only on the existing... |
| n53 | new best | val 0.3161, probe 0.3192, 1.19% better than n51: Add a BernoulliNB specialist base model trained only on the existing lowercased char_wb... |
| n54 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n53 | final pick | val 0.3161 (rank 1 of 53), test 0.3214 (rank 1 of 53) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
