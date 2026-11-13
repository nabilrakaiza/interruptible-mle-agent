# Trajectory: A1-off_detecting-insults-in-social-commentary_seed0

- **Task** detecting-insults-in-social-commentary, **condition** A1-off, **seed** 0
- **Nodes** 86 (96% working), **budget used** 241.6 min, **LLM** 97 calls, 1,676,772 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Calibrated Random Forest for Text, Hashing Vectorizer with Linear Models, Stop-Word Aware Text Classification, Sigmoid Calibration for Kernel SVMs, Large-Scale Linear Text Classification with SGD, Out-of-Core Naive Bayes for Text, Calibrated Classifier Ensembles
- **Search** 16 improve chains exhausted; longest stretch without a new best 29 nodes; selection regret 0.0046 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use a simple TF-IDF word/bigram pipeline with balanced logistic regression as the classifier. First unescap... (val 0.8578) |
| n0 | new best | val 0.8578, probe 0.8772: Use a simple TF-IDF word/bigram pipeline with balanced logistic regression as the class... |
| n0 | card used | first script with LogisticRegression from the card "Hashing Vectorizer with Linear Models" |
| n0 | card used | first script with TfidfVectorizer from the card "Stop-Word Aware Text Classification" |
| n1 | draft | Use a fast hashing vectorizer with unigram and bigram features and a stochastic gradient descent logistic r... (val 0.8721) |
| n1 | new best | val 0.8721, probe 0.8665, 1.67% better than n0: Use a fast hashing vectorizer with unigram and bigram features and a stochastic gradien... |
| n1 | card used | first script with SGDClassifier from the card "Large-Scale Linear Text Classification with SGD" |
| n1 | card used | first script with HashingVectorizer from the card "Out-of-Core Naive Bayes for Text" |
| n2 | draft | I’ll use a TF-IDF word/bigram pipeline feeding a linear SVM whose decision values are sigmoid-calibrated by... (val 0.8680) |
| n3 | draft | I will build a fast text classification pipeline using CountVectorizer and Complement Naive Bayes, a differ... (val 0.8052) |
| n4 | draft | I’ll use a class-weighted RandomForestClassifier on TF-IDF word/bigram features. This is a different model ... (val -) |
| n4 | crash | runtime_error: TypeError: only integer scalar arrays can be converted to a scalar index |
| n4 | card used | first script with RandomForestClassifier from the card "Calibrated Random Forest for Text" |
| n5 | new best | val 0.8874, probe 0.8978, 1.74% better than n1: Keep the existing comment cleaning, 80/20 stratified validation split, and balanced SGD... |
| n6 | fixed | debug fixed the crash in n4 after 1 attempt(s) |
| n7 | new best | val 0.8961, probe 0.8988, 0.98% better than n5: Keep the existing two-vectorizer hashing representation (word unigrams+bigrams and char... |
| n10 | new best | val 0.8962, probe 0.8982, 0.01% better than n7: Keep the same two-vectorizer hashing/TF-IDF features and balanced SGD logistic setup, b... |
| n10 | chain exhausted | the chain from n7 had 3 attempts without a real gain; the search moves elsewhere |
| n16 | new best | val 0.8978, probe 0.9002, 0.18% better than n10: The only change is to apply TF-IDF weighting to the hashed feature matrices inside the ... |
| n17 | new best | val 0.8982, probe 0.9002, 0.04% better than n16: Keep the current cleaning, stratified hold-out, dual hashing vectorizers, TF-IDF weight... |
| n18 | new best | val 0.8984, probe 0.9002, 0.02% better than n17: Keep the existing cleaning, stratified hold-out, dual hashing vectorizers, TF-IDF weigh... |
| n19 | chain exhausted | the chain from n16 had 3 attempts without a real gain; the search moves elsewhere |
| n32 | new best | val 0.8986, probe 0.9115, 0.01% better than n18: Add a third feature extractor to the existing FeatureUnion: a character-level TfidfVect... |
| n35 | no-op | same predictions as n1: Add a chi-square feature-selection step after the existing word/bigram hashing vectoriz... |
| n36 | chain exhausted | the chain from n32 had 3 attempts without a real gain; the search moves elsewhere |
| n39 | no-op | same predictions as n38: The current grid search caps the logistic regression regularization parameter at C=3.0,... |
| n42 | crash | runtime_error: TypeError: TfidfTransformer.__init__() got an unexpected keyword argument 'dtype' |
| n43 | fixed | debug fixed the crash in n42 after 1 attempt(s) |
| n47 | overfitting | beat n46 on validation (0.8971 -> 0.8972) but got worse on test (0.8943 -> 0.8914) |
| n62 | new best | val 0.8991, probe 0.9187, 0.06% better than n32: Add a small grid search over the LinearSVC regularization parameter C, evaluated on the... |
| n65 | new best | val 0.8992, probe 0.9179, 0.01% better than n62: Add one-shot pseudo-labelling to the current tuned LinearSVC pipeline. After the C grid... |
| n65 | chain exhausted | the chain from n62 had 3 attempts without a real gain; the search moves elsewhere |
| n66 | new best | val 0.9044, probe 0.9152, 0.58% better than n65: Add a custom surface-feature block to the existing FeatureUnion, capturing comment leng... |
| n66 | overfitting | beat n61 on validation (0.8972 -> 0.9044) but got worse on test (0.9037 -> 0.8973) |
| n67 | new best | val 0.9044, probe 0.9135, 0.00% better than n66: Extend the custom surface-feature block with additional lexical cues: total punctuation... |
| n69 | new best | val 0.9133, probe 0.9118, 0.98% better than n67: Add a date/time feature block to the FeatureUnion. A ColumnSelector is used to feed the... |
| n70 | new best | val 0.9140, probe 0.9141, 0.08% better than n69: The default TfidfVectorizer token pattern requires at least two word characters, so com... |
| n71 | new best | val 0.9180, probe 0.9179, 0.44% better than n70: Add a combined surface feature that flags comments containing both a second-person pron... |
| n75 | chain exhausted | the chain from n71 had 3 attempts without a real gain; the search moves elsewhere |
| n78 | new best | val 0.9181, probe 0.9183, 0.01% better than n71: Add an ordered co-occurrence surface feature that records whether the first second-pers... |
| n80 | new best | val 0.9184, probe 0.9234, 0.04% better than n78: The profanity regex currently requires a trailing word boundary, so common inflected fo... |
| n80 | chain exhausted | the chain from n77 had 3 attempts without a real gain; the search moves elsewhere |
| n85 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n80 | final pick | val 0.9184 (rank 1 of 83), test 0.9037 (rank 11 of 83) |
| n65 | best on test | test 0.9083, but val rank 17 of 83: Add one-shot pseudo-labelling to the current tuned LinearSVC pipeline. After the C grid... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
