# Trajectory: A4-off_detecting-insults-in-social-commentary_seed2

- **Task** detecting-insults-in-social-commentary, **condition** A4-off, **seed** 2
- **Nodes** 129 (98% working), **budget used** 240.5 min, **LLM** 136 calls, 2,944,197 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Random forest with probability calibration, Efficient text feature extraction, N-gram vectorization with stop-word handling, Bag-of-words with linear classifiers, Sigmoid and isotonic calibration, SGD linear classifiers for large-scale text, Calibrated classifier ensembles, Out-of-core naive Bayes
- **Search** 27 improve chains exhausted; longest stretch without a new best 53 nodes; selection regret 0.0022 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will build a simple text classification pipeline using TF-IDF word and word-pair features followed by log... (val 0.8649) |
| n0 | new best | val 0.8649, probe 0.8899: I will build a simple text classification pipeline using TF-IDF word and word-pair feat... |
| n0 | card used | first script with TfidfVectorizer from the card "N-gram vectorization with stop-word handling" |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Bag-of-words with linear classifiers" |
| n1 | draft | I will parse the CSV files with Python's csv module and a custom escape decoder that handles \x, \u, and do... (val 0.8862) |
| n1 | new best | val 0.8862, probe 0.9129, 2.46% better than n0: I will parse the CSV files with Python's csv module and a custom escape decoder that ha... |
| n2 | draft | I will parse the CSV files with Python's csv module and a custom escape decoder that turns \x, \u, and comm... (val 0.6579) |
| n2 | card used | first script with SGDClassifier from the card "SGD linear classifiers for large-scale text" |
| n3 | draft | Parse the CSV files with Python's csv module, then decode each Comment field by first attempting `ast.liter... (val 0.8059) |
| n3 | card used | first script with MultinomialNB from the card "Out-of-core naive Bayes" |
| n4 | draft | I will parse the CSV files with Python's csv module and a custom decoder that handles the outer quoting, un... (val 0.8657) |
| n7 | chain exhausted | the chain from n1 had 3 attempts without a real gain; the search moves elsewhere |
| n14 | new best | val 0.8871, probe 0.9024, 0.10% better than n1: I will replace the word-level ComplementNB ensemble member with a NBSVM model. Using th... |
| n15 | new best | val 0.8896, probe 0.9060, 0.28% better than n14: Add a fourth base model: logistic regression on TF-IDF character n-grams. This captures... |
| n18 | chain exhausted | the chain from n15 had 3 attempts without a real gain; the search moves elsewhere |
| n19 | new best | val 0.8957, probe 0.9206, 0.69% better than n15: Replace the character-level ComplementNB member with a character-level NBSVM model. I c... |
| n21 | new best | val 0.8964, probe 0.9192, 0.08% better than n19: Increase the character n-gram range for the character-level NBSVM member from (3,6) to ... |
| n22 | chain exhausted | the chain from n19 had 3 attempts without a real gain; the search moves elsewhere |
| n24 | no-op | same predictions as n23: I will increase the character NBSVM CountVectorizer's max_features from 100000 to 20000... |
| n25 | new best | val 0.8975, probe 0.9254, 0.12% better than n21: I will apply log1p sublinear scaling to the count matrices used by the word and charact... |
| n27 | crash | generation_error: empty reply |
| n28 | new best | val 0.8983, probe 0.9262, 0.09% better than n25: Replace the fixed 0.5/0.25/0.25 probability blend with a logistic-regression stacker. I... |
| n28 | chain exhausted | the chain from n25 had 3 attempts without a real gain; the search moves elsewhere |
| n30 | new best | val 0.9024, probe 0.9311, 0.46% better than n28: Augment the TF-IDF logistic regression with handcrafted discourse features: second-pers... |
| n31 | new best | val 0.9049, probe 0.9329, 0.28% better than n30: Add a directed-insult co-occurrence feature to the handcrafted discourse feature block.... |
| n32 | new best | val 0.9057, probe 0.9343, 0.08% better than n31: Add a tight directed-insult feature to the handcrafted discourse block. For each second... |
| n33 | new best | val 0.9082, probe 0.9351, 0.27% better than n32: Expand the second-person pronoun set used by the handcrafted discourse features to incl... |
| n34 | new best | val 0.9086, probe 0.9344, 0.05% better than n33: Change the token_pattern in both word-level vectorizers (the TF-IDF vectorizer for the ... |
| n36 | chain exhausted | the chain from n33 had 3 attempts without a real gain; the search moves elsewhere |
| n38 | new best | val 0.9088, probe 0.9358, 0.03% better than n34: Add a character n-gram TF-IDF representation to the main logistic regression. A new Tfi... |
| n39 | new best | val 0.9098, probe 0.9363, 0.11% better than n38: Change the word NBSVM CountVectorizer from word 1-2 grams to word 1-3 grams. Trigrams c... |
| n40 | no-op | same predictions as n39: Increase the word NBSVM CountVectorizer's max_features from 100000 to 200000. The recen... |
| n42 | chain exhausted | the chain from n39 had 3 attempts without a real gain; the search moves elsewhere |
| n45 | no-op | same predictions as n38: Add a binary source indicator derived from the id prefix (`t` vs `c`) to the handcrafte... |
| n46 | no-op | same predictions as n37: Increase the max_features limit of the word TF-IDF vectorizer used by the main logistic... |
| n59 | new best | val 0.9103, probe 0.9350, 0.06% better than n39: Add character n-gram TF-IDF features directly to the main logistic-regression feature m... |
| n62 | chain exhausted | the chain from n59 had 3 attempts without a real gain; the search moves elsewhere |
| n64 | crash | generation_error: empty reply |
| n70 | new best | val 0.9106, probe 0.9338, 0.03% better than n59: Add temporal features derived from the Date column to the handcrafted feature vector: h... |
| n71 | new best | val 0.9107, probe 0.9325, 0.01% better than n70: Add normalized density features to the handcrafted feature vector used by the main logi... |
| n72 | new best | val 0.9124, probe 0.9339, 0.18% better than n71: Tune the regularization strength C of the three logistic-regression base models on a st... |
| n74 | new best | val 0.9130, probe 0.9332, 0.07% better than n72: Change the character n-gram range of the character NBSVM base model from (3,6) to (2,7)... |
| n75 | new best | val 0.9139, probe 0.9343, 0.10% better than n74: Tune the NBSVM smoothing alpha on the validation split for both the word and character ... |
| n75 | chain exhausted | the chain from n72 had 3 attempts without a real gain; the search moves elsewhere |
| n128 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n75 | final pick | val 0.9139 (rank 1 of 126), test 0.9111 (rank 22 of 126) |
| n80 | best on test | test 0.9133, but val rank 40 of 126: Add a fifth base model to the ensemble: a logistic regression trained on TF-IDF word-le... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
