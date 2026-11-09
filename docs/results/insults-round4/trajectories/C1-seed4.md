# Trajectory: C1_detecting-insults-in-social-commentary_seed4

- **Task** detecting-insults-in-social-commentary, **condition** C1, **seed** 4
- **Nodes** 104 (99% working), **budget used** 252.1 min, **LLM** 119 calls, 2,292,439 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Linear models on TF-IDF text features, Random forest with probability calibration, Calibrated classifier ensembles with sigmoid or isotonic, Stochastic gradient descent linear models, Out-of-core naive Bayes for text
- **Search** 20 improve chains exhausted; longest stretch without a new best 29 nodes; selection regret 0.0038 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF word unigrams and bigrams on decoded comment text and train a logistic regression classifier. De... (val 0.8607) |
| n0 | new best | val 0.8607, probe 0.8817: Use TF-IDF word unigrams and bigrams on decoded comment text and train a logistic regre... |
| n0 | card used | first script with TfidfVectorizer from the card "Linear models on TF-IDF text features" |
| n0 | card used | first script with TfidfVectorizer from the card "Out-of-core naive Bayes for text" |
| n1 | draft | Parse the CSV files with pandas, strip the surrounding double quotes from each comment, decode backslash an... (val 0.8881) |
| n1 | new best | val 0.8881, probe 0.9240, 3.18% better than n0: Parse the CSV files with pandas, strip the surrounding double quotes from each comment,... |
| n1 | card used | first script with SGDClassifier from the card "Stochastic gradient descent linear models" |
| n2 | draft | Parse the CSV comment fields with pandas, strip the surrounding quotes, decode Python-style escapes (includ... (val 0.7828) |
| n3 | draft | Parse the CSV comment fields with pandas, strip the surrounding literal double quotes, and repeatedly decod... (val 0.8244) |
| n4 | draft | Parse the CSVs with pandas, strip the literal outer quotes from each comment, collapse doubled backslashes,... (val 0.8864) |
| n8 | chain exhausted | the chain from n1 had 3 attempts without a real gain; the search moves elsewhere |
| n21 | no-op | same predictions as n20: Increase `max_features` in the character n-gram TF-IDF vectorizer from 50,000 to 200,00... |
| n26 | no-op | same predictions as n25: Change the character n-gram TF-IDF vectorizer to drop character n-grams that appear in ... |
| n29 | no-op | same predictions as n25: Normalize whitespace in the decoded comments by collapsing all runs of whitespace (newl... |
| n31 | new best | val 0.8884, probe 0.9234, 0.03% better than n1: Change the character n-gram range from (2,6) to (2,5) in the TF-IDF vectorizer. Earlier... |
| n32 | new best | val 0.8884, probe 0.9229, 0.01% better than n31: Replace the single SGDClassifier with a CalibratedClassifierCV ensemble that wraps the ... |
| n33 | new best | val 0.8885, probe 0.9234, 0.01% better than n32: Increase the number of folds in the CalibratedClassifierCV ensemble from 5 to 10. This ... |
| n34 | chain exhausted | the chain from n31 had 3 attempts without a real gain; the search moves elsewhere |
| n42 | no-op | same predictions as n41: Add `max_df=0.95` to the character n-gram TfidfVectorizer. Character n-grams that appea... |
| n47 | new best | val 0.8900, probe 0.9213, 0.17% better than n33: Switch the SGD logistic regression from pure L2 regularization to elasticnet with l1_ra... |
| n48 | new best | val 0.8917, probe 0.9213, 0.20% better than n47: Increase the elasticnet `l1_ratio` from 0.1 to 0.2 in the SGD logistic regression. The ... |
| n50 | new best | val 0.8920, probe 0.9204, 0.04% better than n48: Increase the elasticnet L1 mixing parameter from 0.2 to 0.3 in the SGD logistic regress... |
| n52 | new best | val 0.8922, probe 0.9201, 0.02% better than n50: Wrap the SGD logistic regression in `CalibratedClassifierCV` with 10-fold sigmoid calib... |
| n52 | chain exhausted | the chain from n48 had 3 attempts without a real gain; the search moves elsewhere |
| n58 | new best | val 0.8927, probe 0.9211, 0.05% better than n52: Change the character n-gram TF-IDF vectorizer's min_df from 2 to 3. Earlier experiments... |
| n59 | new best | val 0.8927, probe 0.9211, 0.00% better than n58: Average the elasticnet SGD logistic predictions over three different random seeds in ad... |
| n60 | chain exhausted | the chain from n57 had 3 attempts without a real gain; the search moves elsewhere |
| n62 | no-op | same predictions as n61: Add `max_df=0.95` to the character n-gram TF-IDF vectorizer. The current pipeline only ... |
| n67 | new best | val 0.8946, probe 0.9215, 0.21% better than n59: Keep the character n-gram TF-IDF pipeline and SGD logistic regression unchanged, but ad... |
| n68 | new best | val 0.8998, probe 0.9161, 0.58% better than n67: Add a directed-insult proximity feature to the dense discourse block: for each comment,... |
| n72 | new best | val 0.9013, probe 0.9244, 0.18% better than n68: Make the directed-insult proximity feature negation-aware. Currently it counts any seco... |
| n74 | new best | val 0.9032, probe 0.9246, 0.21% better than n72: Add `class_weight="balanced"` to the SGDClassifier so the minority insult class receive... |
| n77 | chain exhausted | the chain from n74 had 3 attempts without a real gain; the search moves elsewhere |
| n82 | no-op | same predictions as n80: Add a binary source feature derived from the id prefix (`t` vs. other) to the dense dis... |
| n85 | new best | val 0.9048, probe 0.9220, 0.17% better than n74: Add a word-level TF-IDF feature block (unigrams and bigrams) to the existing character ... |
| n88 | new best | val 0.9050, probe 0.9235, 0.02% better than n85: Expand the word-level TF-IDF block from unigrams+bigrams to unigrams+bigrams+trigrams a... |
| n90 | new best | val 0.9053, probe 0.9224, 0.04% better than n88: Expand the word-level TF-IDF block from trigrams to include 4-grams and increase its fe... |
| n90 | chain exhausted | the chain from n85 had 3 attempts without a real gain; the search moves elsewhere |
| n103 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n90 | final pick | val 0.9053 (rank 1 of 103), test 0.9030 (rank 6 of 103) |
| n13 | best on test | test 0.9067, but val rank 61 of 103: Change the character n-gram range from (3,5) to (2,5) while keeping the existing decodi... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
