# Trajectory: C1_detecting-insults-in-social-commentary_seed3

- **Task** detecting-insults-in-social-commentary, **condition** C1, **seed** 3
- **Nodes** 63 (95% working), **budget used** 240.2 min, **LLM** 76 calls, 1,646,005 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Large-scale linear text classification with SGD, Calibrated text classifier probabilities, Naive Bayes for out-of-core text classification, Text feature extraction with stop-word and n-gram choices, Polynomial feature expansion for linear classifiers
- **Search** 12 improve chains exhausted; longest stretch without a new best 11 nodes; selection regret 0.0166 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I’ll use a TF-IDF bag-of-words/ngram representation of the cleaned comments and train a logistic regression... (val 0.8580) |
| n0 | new best | val 0.8580, probe 0.8823: I’ll use a TF-IDF bag-of-words/ngram representation of the cleaned comments and train a... |
| n0 | card used | first script with TfidfVectorizer from the card "Large-scale linear text classification with SGD" |
| n0 | card used | first script with TfidfVectorizer from the card "Text feature extraction with stop-word and n-gram choices" |
| n1 | draft | I will use hashing vectorizers to build word and character n-gram features, which avoids storing a vocabula... (val 0.8731) |
| n1 | new best | val 0.8731, probe 0.9094, 1.76% better than n0: I will use hashing vectorizers to build word and character n-gram features, which avoid... |
| n2 | draft |  (val -) |
| n2 | crash | generation_error: empty reply |
| n3 | draft | I will decode the unicode-escaped comments with a custom parser that handles byte-level escapes (\\xNN), un... (val 0.7374) |
| n4 | draft | I will parse the CSV with Python’s csv module, strip the outer quotes from each comment, and decode escaped... (val 0.8480) |
| n6 | new best | val 0.8744, probe 0.9075, 0.15% better than n1: I will expand the n-gram ranges of both hashing vectorizers: word n-grams from (1,2) to... |
| n6 | overfitting | beat n1 on validation (0.8731 -> 0.8744) but got worse on test (0.8964 -> 0.8949) |
| n9 | chain exhausted | the chain from n6 had 3 attempts without a real gain; the search moves elsewhere |
| n11 | no-op | same predictions as n1: I will keep the current hashing vectorizers, preprocessing, and SGD settings, but repla... |
| n12 | new best | val 0.8862, probe 0.9147, 1.35% better than n6: I will augment the existing TF-IDF word n-gram pipeline with a character-level TF-IDF v... |
| n13 | new best | val 0.8867, probe 0.9141, 0.06% better than n12: I will expand the n-gram ranges of both TF-IDF vectorizers in the current best pipeline... |
| n14 | new best | val 0.8883, probe 0.9173, 0.17% better than n13: I will keep the current TF-IDF feature union and preprocessing unchanged, but replace t... |
| n15 | new best | val 0.8883, probe 0.9195, 0.00% better than n14: Keep the current TF-IDF feature union, preprocessing, and C-selection grid search uncha... |
| n17 | new best | val 0.8894, probe 0.9189, 0.12% better than n15: Add a chi-square feature-selection step between the TF-IDF FeatureUnion and the logisti... |
| n19 | new best | val 0.8902, probe 0.9200, 0.10% better than n17: Keep the current TF-IDF word/character features, chi-square selection, and logistic-reg... |
| n20 | chain exhausted | the chain from n17 had 3 attempts without a real gain; the search moves elsewhere |
| n29 | overfitting | beat n0 on validation (0.8580 -> 0.8662) but got worse on test (0.8837 -> 0.8673) |
| n31 | new best | val 0.8933, probe 0.9139, 0.34% better than n19: Keep the existing NB-weighted binary word/character CountVectorizer pipeline and balanc... |
| n31 | overfitting | beat n30 on validation (0.8897 -> 0.8933) but got worse on test (0.8841 -> 0.8822) |
| n32 | crash | generation_error: empty reply |
| n33 | new best | val 0.8955, probe 0.9170, 0.24% better than n31: Keep the NB-weighted binary word/character CountVectorizer pipeline and balanced logist... |
| n35 | new best | val 0.8995, probe 0.9278, 0.45% better than n33: Add a compact set of surface-level features to the existing NB-weighted sparse feature ... |
| n39 | no-op | same predictions as n33: Tune the relative contribution of the word and character NB-weighted feature blocks by ... |
| n40 | new best | val 0.8996, probe 0.9278, 0.01% better than n35: Add a word-level TF-IDF feature block to the existing NB-weighted binary word/character... |
| n40 | chain exhausted | the chain from n35 had 3 attempts without a real gain; the search moves elsewhere |
| n50 | new best | val 0.9013, probe 0.9273, 0.19% better than n40: Replace the single logistic regression with a two-model stacking ensemble. The first ba... |
| n54 | new best | val 0.9014, probe 0.9253, 0.01% better than n50: Add an RBF-support vector classifier as a third base model in the stacking ensemble. It... |
| n54 | chain exhausted | the chain from n50 had 3 attempts without a real gain; the search moves elsewhere |
| n59 | new best | val 0.9017, probe 0.9254, 0.03% better than n54: Replace binary presence with sublinear 1+log term-frequency weighting in the two NB-wei... |
| n60 | new best | val 0.9037, probe 0.9303, 0.22% better than n59: Add a compact date/time feature block to the current NB-weighted logistic regression pi... |
| n61 | new best | val 0.9037, probe 0.9303, 0.00% better than n60: Add a linear time-trend feature to the existing date block. The current date features o... |
| n62 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n61 | final pick | val 0.9037 (rank 1 of 60), test 0.8928 (rank 36 of 60) |
| n17 | best on test | test 0.9094, but val rank 33 of 60: Add a chi-square feature-selection step between the TF-IDF FeatureUnion and the logisti... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
