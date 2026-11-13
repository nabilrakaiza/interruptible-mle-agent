# Trajectory: C1_spooky-author-identification_seed4

- **Task** spooky-author-identification, **condition** C1, **seed** 4
- **Nodes** 48 (94% working), **budget used** 240.5 min, **LLM** 54 calls, 748,772 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** Tfidf plus linear text classifier, Feature hashing and dictionary vectorization for text, Probability calibration for multiclass text classification, Out-of-core naive Bayes for large text corpora, Sparse-feature document classification with Tfidf weighting
- **Search** 7 improve chains exhausted; longest stretch without a new best 22 nodes; selection regret 0.0 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use a TF-IDF word-level representation with sublinear term frequency and 1-2 word n-grams, then train a mul... (val 0.5312) |
| n0 | new best | val 0.5312, probe 0.5363: Use a TF-IDF word-level representation with sublinear term frequency and 1-2 word n-gra... |
| n0 | card used | first script with TfidfVectorizer from the card "Tfidf plus linear text classifier" |
| n0 | card used | first script with TfidfVectorizer from the card "Out-of-core naive Bayes for large text corpora" |
| n0 | card used | first script with TfidfVectorizer from the card "Sparse-feature document classification with Tfidf weighting" |
| n1 | draft | Use a character n-gram TF-IDF representation instead of word-level bag-of-words, which captures punctuation... (val 0.5280) |
| n1 | new best | val 0.5280, probe 0.5235, 0.60% better than n0: Use a character n-gram TF-IDF representation instead of word-level bag-of-words, which ... |
| n2 | draft | I will use a hashing vectorizer with word 1-grams and 2-grams, followed by TF-IDF weighting with sublinear ... (val 0.5608) |
| n2 | card used | first script with TfidfTransformer from the card "Feature hashing and dictionary vectorization for text" |
| n3 | draft | Use raw word counts with a CountVectorizer (1-2 n-grams, English stop words removed, min_df=3, max_df=0.9) ... (val 0.5211) |
| n3 | new best | val 0.5211, probe 0.5097, 1.31% better than n1: Use raw word counts with a CountVectorizer (1-2 n-grams, English stop words removed, mi... |
| n4 | draft | Use a TF-IDF word representation with 1-2 word n-grams and sublinear term frequency, then train a Complemen... (val 0.4772) |
| n4 | new best | val 0.4772, probe 0.4808, 8.42% better than n3: Use a TF-IDF word representation with 1-2 word n-grams and sublinear term frequency, th... |
| n5 | new best | val 0.4600, probe 0.4552, 3.62% better than n4: Keep the calibrated ComplementNB pipeline and word TF-IDF features, but augment them wi... |
| n6 | new best | val 0.4085, probe 0.4164, 11.18% better than n5: Keep the current word-level TF-IDF vectorizer and logistic regression settings, but add... |
| n7 | no-op | same predictions as n6: Keep the current word + character n-gram TF-IDF features and multinomial logistic regre... |
| n8 | new best | val 0.4020, probe 0.4174, 1.61% better than n6: Keep the word+character TF-IDF features and logistic regression with C tuning, but add ... |
| n9 | new best | val 0.4015, probe 0.4162, 0.13% better than n8: Expand the word-level TF-IDF n-gram range from (1,2) to (1,3) so the logistic regressio... |
| n12 | new best | val 0.3806, probe 0.3946, 5.20% better than n9: Replace the English stop-word removal in the word-level TF-IDF vectorizer with no stop-... |
| n15 | new best | val 0.3765, probe 0.3925, 1.06% better than n12: Change the word-level TF-IDF vectorizer's token_pattern from the default `r"(?u)\b\w\w+... |
| n16 | new best | val 0.3739, probe 0.3905, 0.70% better than n15: Extend the character TF-IDF vectorizer from character 2-grams through 5-grams to 2-gram... |
| n20 | new best | val 0.3692, probe 0.3811, 1.25% better than n16: Add a second character-level TF-IDF vectorizer using analyzer='char' alongside the exis... |
| n21 | new best | val 0.3616, probe 0.3774, 2.06% better than n20: Add a case-sensitive word TF-IDF vectorizer as an additional feature block. The current... |
| n22 | new best | val 0.3616, probe 0.3777, 0.01% better than n21: Extend the case-sensitive word TF-IDF vectorizer from 1-2 grams to 1-3 grams. The exist... |
| n24 | chain exhausted | the chain from n21 had 3 attempts without a real gain; the search moves elsewhere |
| n37 | no-op | same predictions as n33: Replace the manual C grid search (which evaluates each candidate on the held-out valida... |
| n41 | no-op | same predictions as n38: Add a binary-presence word TF-IDF feature block alongside the existing count-weighted w... |
| n43 | crash | runtime_error: ValueError: Negative values in data passed to ComplementNB (input X). |
| n44 | crash | runtime_error: ValueError: empty vocabulary; perhaps the documents only contain stop words |
| n45 | fixed | debug fixed the crash in n44 after 1 attempt(s) |
| n45 | new best | val 0.3587, probe 0.3782, 0.81% better than n22: The crash is caused by the proper-noun TF-IDF vectorizer using the default `lowercase=T... |
| n47 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n45 | final pick | val 0.3587 (rank 1 of 45), test 0.3608 (rank 1 of 45) |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
