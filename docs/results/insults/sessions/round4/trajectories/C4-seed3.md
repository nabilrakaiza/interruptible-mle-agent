# Trajectory: C4_detecting-insults-in-social-commentary_seed3

- **Task** detecting-insults-in-social-commentary, **condition** C4, **seed** 3
- **Nodes** 108 (97% working), **budget used** 241.0 min, **LLM** 125 calls, 2,321,024 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TfidfVectorizer with SGD linear classifiers, Random forest with probability calibration, CalibratedClassifierCV with sigmoid or isotonic, Polynomial feature expansion with linear models, Out-of-core Naive Bayes for text streams, Text preprocessing and vectorization pipeline
- **Search** 21 improve chains exhausted; longest stretch without a new best 38 nodes; selection regret 0.0004 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will parse the CSV files, clean each comment by stripping the surrounding quotes and decoding unicode esc... (val 0.8598) |
| n0 | new best | val 0.8598, probe 0.8803: I will parse the CSV files, clean each comment by stripping the surrounding quotes and ... |
| n0 | card used | first script with TfidfVectorizer from the card "TfidfVectorizer with SGD linear classifiers" |
| n0 | card used | first script with LogisticRegression from the card "Polynomial feature expansion with linear models" |
| n0 | card used | first script with TfidfVectorizer from the card "Out-of-core Naive Bayes for text streams" |
| n0 | card used | first script with TfidfVectorizer from the card "Text preprocessing and vectorization pipeline" |
| n1 | draft | Use a TF-IDF feature union of word n-grams and character n-grams to capture both vocabulary and spelling pa... (val 0.8322) |
| n2 | draft | Use character n-gram TF-IDF features (char_wb, 2-5 grams) with a regularized logistic regression classifier... (val 0.8542) |
| n3 | draft | I will parse and clean each comment by interpreting the CSV/JSON-style quoted field with `ast.literal_eval`... (val 0.8349) |
| n4 | draft | Use HashingVectorizer with word unigram/bigram features and an SGD logistic-regression classifier to predic... (val 0.8573) |
| n5 | new best | val 0.8852, probe 0.9140, 2.95% better than n0: I will add a character n-gram TF-IDF vectorizer to the existing word-level TF-IDF featu... |
| n6 | new best | val 0.8860, probe 0.9102, 0.10% better than n5: I will add a handcrafted text-statistics feature block to the existing word+character T... |
| n7 | new best | val 0.8981, probe 0.9240, 1.37% better than n6: I will extend the existing handcrafted statistics block with lexical signal features: c... |
| n10 | chain exhausted | the chain from n7 had 3 attempts without a real gain; the search moves elsewhere |
| n26 | overfitting | beat n11 on validation (0.8902 -> 0.8904) but got worse on test (0.8996 -> 0.8983) |
| n37 | overfitting | beat n36 on validation (0.8926 -> 0.8939) but got worse on test (0.9008 -> 0.8952) |
| n46 | new best | val 0.9020, probe 0.9150, 0.44% better than n7: Add a positional second-person negation feature to the DiscourseFeatures transformer. F... |
| n49 | chain exhausted | the chain from n46 had 3 attempts without a real gain; the search moves elsewhere |
| n50 | new best | val 0.9039, probe 0.9170, 0.20% better than n46: Add a positional addressivity feature to DiscourseFeatures: a binary indicator for whet... |
| n54 | chain exhausted | the chain from n50 had 3 attempts without a real gain; the search moves elsewhere |
| n56 | new best | val 0.9049, probe 0.9238, 0.11% better than n50: Add parsed date/time features to the current pipeline by introducing a DateFeatures tra... |
| n59 | chain exhausted | the chain from n56 had 3 attempts without a real gain; the search moves elsewhere |
| n75 | crash | runtime_error: TypeError: PolynomialFeatures.__init__() got an unexpected keyword argument 'sparse_output' |
| n76 | new best | val 0.9083, probe 0.9219, 0.37% better than n56: Enhance the DateFeatures transformer with cyclical encodings for hour, day-of-week, and... |
| n77 | crash | runtime_error: sklearn.exceptions.NotFittedError: This Pipeline instance is not fitted yet. Call 'fit' with appropriate arguments before using this esti... |
| n79 | fixed | debug fixed the crash in n75 after 2 attempt(s) |
| n81 | new best | val 0.9102, probe 0.9225, 0.21% better than n76: Add a dedicated identity-based slur lexicon feature to the DiscourseFeatures transforme... |
| n83 | new best | val 0.9110, probe 0.9224, 0.09% better than n81: Add a negated-insult count feature to the DiscourseFeatures transformer. For each token... |
| n84 | new best | val 0.9111, probe 0.9224, 0.01% better than n83: Add a reverse-targeted insult count feature to the DiscourseFeatures transformer. For e... |
| n84 | chain exhausted | the chain from n81 had 3 attempts without a real gain; the search moves elsewhere |
| n107 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n84 | final pick | val 0.9111 (rank 1 of 105), test 0.9083 (rank 3 of 105) |
| n82 | best on test | test 0.9087, but val rank 4 of 105: Add a targeted second-person insult feature to the DiscourseFeatures transformer. This ... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
