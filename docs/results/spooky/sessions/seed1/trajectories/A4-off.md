# Trajectory: A4-off_spooky-author-identification_seed1

- **Task** spooky-author-identification, **condition** A4-off, **seed** 1
- **Nodes** 57 (98% working), **budget used** 126.8 min, **LLM** 59 calls, 816,006 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TF-IDF sparse features with linear classifiers, Temperature scaling for calibrated probabilities, One-vs-rest multiclass calibration, Out-of-core naive Bayes for text, Feature hashing for large-vocabulary text, PoS and context-window features with DictVectorizer
- **Search** 7 improve chains exhausted; longest stretch without a new best 16 nodes; selection regret 0.0007 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will use TF-IDF word unigram and bigram features with a multinomial logistic regression, which is a fast ... (val 0.5871) |
| n0 | new best | val 0.5871, probe 0.5815: I will use TF-IDF word unigram and bigram features with a multinomial logistic regressi... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF sparse features with linear classifiers" |
| n1 | draft | I will train a linear classifier on a hybrid sparse feature set: TF-IDF word unigrams/bigrams plus TF-IDF c... (val 0.5341) |
| n1 | new best | val 0.5341, probe 0.5313, 9.03% better than n0: I will train a linear classifier on a hybrid sparse feature set: TF-IDF word unigrams/b... |
| n2 | draft | I will use raw word-count features (unigrams and bigrams) with a Multinomial Naive Bayes model, which is a ... (val 0.4867) |
| n2 | new best | val 0.4867, probe 0.4746, 8.87% better than n1: I will use raw word-count features (unigrams and bigrams) with a Multinomial Naive Baye... |
| n2 | card used | first script with MultinomialNB from the card "Out-of-core naive Bayes for text" |
| n3 | draft | Instead of logistic regression or naive Bayes, I use a linear support vector machine (SGDClassifier with hi... (val 0.4665) |
| n3 | new best | val 0.4665, probe 0.4616, 4.14% better than n2: Instead of logistic regression or naive Bayes, I use a linear support vector machine (S... |
| n4 | draft | I will use a RidgeClassifier on TF-IDF word unigram+bigram features, which fits a linear least-squares mode... (val 0.5154) |
| n5 | new best | val 0.4319, probe 0.4306, 7.41% better than n3: I will replace the naive Bayes count-vectorizer pipeline with a linear SVM (SGDClassifi... |
| n6 | new best | val 0.4229, probe 0.4283, 2.08% better than n5: I will improve the current hybrid word+character TF-IDF linear SVM by switching the cha... |
| n7 | new best | val 0.4129, probe 0.4205, 2.38% better than n6: I will change the SGDClassifier to use averaged SGD by setting `average=True`. Averagin... |
| n10 | chain exhausted | the chain from n7 had 3 attempts without a real gain; the search moves elsewhere |
| n11 | new best | val 0.4122, probe 0.4118, 0.16% better than n7: I will keep the hybrid TF-IDF word/char feature union and the sigmoid-calibrated hinge-... |
| n12 | new best | val 0.4077, probe 0.4049, 1.09% better than n11: I will increase the character TF-IDF vectorizer’s max_features from 35,000 to 50,000 wh... |
| n13 | new best | val 0.3877, probe 0.3869, 4.91% better than n12: Switch the probability calibration from per-class sigmoid to temperature scaling while ... |
| n14 | new best | val 0.3831, probe 0.3837, 1.18% better than n13: Expand the word TF-IDF feature stream from unigrams+bigrams to unigrams+bigrams+trigram... |
| n15 | new best | val 0.3829, probe 0.3838, 0.06% better than n14: Increase the word TF-IDF vocabulary cap from 50,000 to 80,000 so the unigram/bigram/tri... |
| n16 | new best | val 0.3783, probe 0.3796, 1.21% better than n15: Increase the character TF-IDF feature cap from 50,000 to 80,000 so more rare, author-di... |
| n17 | new best | val 0.3765, probe 0.3766, 0.46% better than n16: Increase the character TF-IDF feature cap from 80,000 to 120,000 so the linear SVM can ... |
| n18 | no-op | same predictions as n17: Raise the character TF-IDF feature cap from 120,000 to 160,000 so the linear SVM can us... |
| n19 | no-op | same predictions as n17: Raise the word TF-IDF `max_features` from 80,000 to 120,000 so the linear SVM can use m... |
| n21 | no-op | same predictions as n18: . Then final model's decision values may be slightly different scale than OOF, but temp... |
| n21 | chain exhausted | the chain from n17 had 3 attempts without a real gain; the search moves elsewhere |
| n26 | overfitting | beat n15 on validation (0.3829 -> 0.3817) but got worse on test (0.3822 -> 0.3872) |
| n29 | new best | val 0.3763, probe 0.3896, 0.06% better than n17: I will replace the character TF-IDF analyzer from `char` to `char_wb`, keeping the same... |
| n32 | chain exhausted | the chain from n29 had 3 attempts without a real gain; the search moves elsewhere |
| n46 | new best | val 0.3755, probe 0.3734, 0.20% better than n29: Add a fifth FeatureUnion branch that extracts five sentence-level statistics: character... |
| n47 | new best | val 0.3725, probe 0.3699, 0.82% better than n46: I will extend the sentence-level statistics branch in the FeatureUnion. In addition to ... |
| n48 | new best | val 0.3720, probe 0.3713, 0.13% better than n47: Change the word TF-IDF token pattern from the default two-or-more-character pattern to ... |
| n51 | chain exhausted | the chain from n48 had 3 attempts without a real gain; the search moves elsewhere |
| n52 | no-op | same predictions as n47: Make the character n-gram streams case-sensitive by adding `lowercase=False` to both th... |
| n54 | new best | val 0.3715, probe 0.3676, 0.14% better than n48: I will add a second word-level TF-IDF stream to the FeatureUnion that lowercases the te... |
| n55 | new best | val 0.3712, probe 0.3699, 0.06% better than n54: I will add a separate rare-word TF-IDF stream to the FeatureUnion that uses `min_df=1` ... |
| n56 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n55 | final pick | val 0.3712 (rank 1 of 56), test 0.3651 (rank 2 of 56) |
| n54 | best on test | test 0.3645, but val rank 2 of 56: I will add a second word-level TF-IDF stream to the FeatureUnion that lowercases the te... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
