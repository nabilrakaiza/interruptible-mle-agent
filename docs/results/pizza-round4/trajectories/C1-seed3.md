# Trajectory: C1_random-acts-of-pizza_seed3

- **Task** random-acts-of-pizza, **condition** C1, **seed** 3
- **Nodes** 100 (97% working), **budget used** 240.0 min, **LLM** 113 calls, 2,111,695 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TF-IDF with Sparse Linear Classifier, Bag-of-Words with Word N-grams, Random Forest with Sigmoid Calibration, Calibrated Classifier for Stable Rankings, Gradient Boosted Trees, AdaBoost with Weak Learners, Metadata-Stripped Text Classification
- **Search** 15 improve chains exhausted; longest stretch without a new best 17 nodes; selection regret 0.0021 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Combine TF-IDF features from the request text and title with standardized numeric metadata features, then t... (val 0.6165) |
| n0 | new best | val 0.6165, probe 0.6348: Combine TF-IDF features from the request text and title with standardized numeric metad... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF with Sparse Linear Classifier" |
| n0 | card used | first script with TfidfVectorizer from the card "Bag-of-Words with Word N-grams" |
| n1 | draft | Use a two-model ensemble rather than a single linear model. A TF-IDF logistic regression will capture the r... (val 0.6303) |
| n1 | new best | val 0.6303, probe 0.6994, 2.24% better than n0: Use a two-model ensemble rather than a single linear model. A TF-IDF logistic regressio... |
| n1 | card used | first script with RandomForestClassifier from the card "Random Forest with Sigmoid Calibration" |
| n2 | draft | Use a gradient-boosted tree model (HistGradientBoostingClassifier) on engineered tabular features instead o... (val 0.6571) |
| n2 | new best | val 0.6571, probe 0.6954, 4.25% better than n1: Use a gradient-boosted tree model (HistGradientBoostingClassifier) on engineered tabula... |
| n3 | draft | Use a pure text bag-of-words approach with TF-IDF and logistic regression, avoiding the earlier metadata/TF... (val 0.5699) |
| n4 | draft | I will build a linear classifier on hashed TF-IDF text features combined with scaled numeric metadata. The ... (val 0.5373) |
| n7 | chain exhausted | the chain from n2 had 3 attempts without a real gain; the search moves elsewhere |
| n10 | new best | val 0.6629, probe 0.6986, 0.88% better than n2: Add a HistGradientBoostingClassifier on the same numeric metadata features as a third b... |
| n11 | new best | val 0.6721, probe 0.6995, 1.38% better than n10: Add a character n-gram TF-IDF logistic regression as a fourth base model in the out-of-... |
| n12 | new best | val 0.6757, probe 0.6904, 0.54% better than n11: Add a logistic regression base model on the standardized numeric metadata features to t... |
| n15 | new best | val 0.6784, probe 0.6890, 0.40% better than n12: Add a title-only TF-IDF logistic regression as an additional base model in the out-of-f... |
| n15 | overfitting | beat n12 on validation (0.6757 -> 0.6784) but got worse on test (0.6884 -> 0.6842) |
| n18 | chain exhausted | the chain from n15 had 3 attempts without a real gain; the search moves elsewhere |
| n23 | new best | val 0.6794, probe 0.6894, 0.15% better than n15: Add an AdaBoost classifier with shallow decision trees as a new base model on the numer... |
| n23 | card used | first script with AdaBoostClassifier from the card "AdaBoost with Weak Learners" |
| n26 | new best | val 0.6797, probe 0.6907, 0.04% better than n23: Add an RBF support vector classifier on the standardized numeric metadata as a new base... |
| n29 | chain exhausted | the chain from n23 had 3 attempts without a real gain; the search moves elsewhere |
| n30 | new best | val 0.6839, probe 0.6861, 0.62% better than n26: Add a multi-layer perceptron classifier on the standardized numeric metadata as a new b... |
| n32 | new best | val 0.6840, probe 0.6852, 0.02% better than n30: Add a title-only word-level TF-IDF logistic regression as an additional base model in t... |
| n32 | overfitting | beat n30 on validation (0.6839 -> 0.6840) but got worse on test (0.6894 -> 0.6854) |
| n33 | chain exhausted | the chain from n30 had 3 attempts without a real gain; the search moves elsewhere |
| n35 | crash | runtime_error: ValueError: np.nan is an invalid document, expected byte or unicode string. |
| n37 | fixed | debug fixed the crash in n35 after 1 attempt(s) |
| n39 | new best | val 0.6887, probe 0.6931, 0.69% better than n32: Add a quantile-transformed numeric logistic regression as an additional base model in t... |
| n40 | new best | val 0.6888, probe 0.6930, 0.00% better than n39: Change the stacking combination step. Instead of averaging each base model's test predi... |
| n42 | new best | val 0.6940, probe 0.6885, 0.76% better than n40: Add a post-hoc Platt scaling step for the three tree/boosting base models (RandomForest... |
| n45 | new best | val 0.6943, probe 0.6855, 0.04% better than n42: Add a new base model to the stacking ensemble that uses handcrafted text statistics ext... |
| n45 | chain exhausted | the chain from n42 had 3 attempts without a real gain; the search moves elsewhere |
| n51 | crash | runtime_error: KeyError: 'request_hour' |
| n52 | fixed | debug fixed the crash in n51 after 1 attempt(s) |
| n63 | new best | val 0.6956, probe 0.6848, 0.18% better than n45: Calibrate the AdaBoost base model with sigmoid (Platt) scaling using CalibratedClassifi... |
| n67 | new best | val 0.6997, probe 0.6907, 0.59% better than n63: Replace the single hashed-SGD model with a stacking ensemble. The stack uses out-of-fol... |
| n70 | new best | val 0.7034, probe 0.6891, 0.54% better than n67: Add a Complement Naive Bayes base model on the same combined title/body/subreddit text.... |
| n74 | chain exhausted | the chain from n70 had 3 attempts without a real gain; the search moves elsewhere |
| n75 | overfitting | beat n67 on validation (0.6997 -> 0.7027) but got worse on test (0.7033 -> 0.6951) |
| n76 | new best | val 0.7042, probe 0.6914, 0.11% better than n70: Add a dedicated TF-IDF logistic regression base model trained on the request title alon... |
| n79 | chain exhausted | the chain from n76 had 3 attempts without a real gain; the search moves elsewhere |
| n83 | new best | val 0.7061, probe 0.6889, 0.27% better than n76: Add a continuous timestamp feature (seconds since Unix epoch) derived from `unix_timest... |
| n84 | new best | val 0.7083, probe 0.6870, 0.31% better than n83: Add a new base model to the stacking ensemble that uses handcrafted text statistics fro... |
| n87 | new best | val 0.7083, probe 0.6854, 0.00% better than n84: Add a new base model to the stacking ensemble: a linear classifier on TF-IDF text featu... |
| n87 | chain exhausted | the chain from n84 had 3 attempts without a real gain; the search moves elsewhere |
| n93 | new best | val 0.7097, probe 0.6871, 0.20% better than n87: Add a polynomial logistic regression base model to the stacking ensemble. It applies me... |
| n95 | new best | val 0.7117, probe 0.6874, 0.28% better than n93: Add a dedicated title-only character n-gram TF-IDF logistic regression base model to th... |
| n98 | new best | val 0.7123, probe 0.6873, 0.09% better than n95: Add a small multi-layer perceptron base model on the standardized numeric metadata to t... |
| n99 | crash | timeout: killed after 33s |
| n99 | chain exhausted | the chain from n95 had 3 attempts without a real gain; the search moves elsewhere |
|  | stop | budget, final selection best_val |
| n98 | final pick | val 0.7123 (rank 1 of 97), test 0.7013 (rank 7 of 97) |
| n74 | best on test | test 0.7034, but val rank 22 of 97: Replace the TfidfVectorizer in the ComplementNB text base model with a CountVectorizer.... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
