# Trajectory: C4_random-acts-of-pizza_seed4

- **Task** random-acts-of-pizza, **condition** C4, **seed** 4
- **Nodes** 111 (77% working), **budget used** 242.9 min, **LLM** 134 calls, 3,131,635 tokens
- **Interventions** 2 applied, 0 dropped
- **Model cards** TF-IDF with linear text classifier, Random forest with probability calibration, Calibrated classifier ensemble, Gradient-boosted decision trees, AdaBoost with shallow trees, N-gram text vectorization, Sparse bag-of-words linear pipeline, Sigmoid calibration for AUC preservation
- **Search** 18 improve chains exhausted; longest stretch without a new best 95 nodes; selection regret 0.0168 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF features from the request title, edit-aware request text, and subreddit list, combined with stan... (val 0.6279) |
| n0 | new best | val 0.6279, probe 0.6333: Use TF-IDF features from the request title, edit-aware request text, and subreddit list... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF with linear text classifier" |
| n0 | card used | first script with TfidfVectorizer from the card "N-gram text vectorization" |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "Sparse bag-of-words linear pipeline" |
| n1 | draft | I will use a two-model ensemble instead of a single logistic regression on all features. A TF-IDF logistic ... (val 0.6272) |
| n1 | card used | first script with RandomForestClassifier from the card "Random forest with probability calibration" |
| n2 | draft | I will use a gradient-boosted decision tree model instead of a linear TF-IDF model or a random-forest ensem... (val -) |
| n2 | crash | runtime_error: TypeError: Sparse data was passed for X, but dense data is required. Use '.toarray()' to convert to a dense numpy array. |
| n2 | card used | first script with GradientBoostingClassifier, HistGradientBoostingClassifier from the card "Gradient-boosted decision trees" |
| n3 | draft | Instead of a linear model or a random forest, I will train a histogram gradient-boosting classifier on a de... (val 0.6693) |
| n3 | new best | val 0.6693, probe 0.7090, 6.59% better than n0: Instead of a linear model or a random forest, I will train a histogram gradient-boostin... |
| n4 | draft | I will build a sparse linear model using a modified-Huber loss instead of plain logistic regression, which ... (val 0.5687) |
| n5 | fixed | debug fixed the crash in n2 after 1 attempt(s) |
| n7 | new best | val 0.6696, probe 0.7097, 0.04% better than n3: I will augment the gradient-boosting model with a logistic regression on the raw TF-IDF... |
| n8 | new best | val 0.6713, probe 0.7095, 0.25% better than n7: I will change the early-stopping criterion of the histogram gradient-boosting classifie... |
| n9 | new best | val 0.6749, probe 0.7026, 0.54% better than n8: I will add four derived activity-ratio features to the numeric metadata: RAOP comment r... |
| n12 | chain exhausted | the chain from n9 had 3 attempts without a real gain; the search moves elsewhere |
| n13 | new best | val 0.6909, probe 0.7095, 2.36% better than n9: I will add character n-gram TF-IDF features from the combined text, reduced by Truncate... |
| n15 | new best | val 0.6936, probe 0.7058, 0.38% better than n13: I will add a compact set of features derived from the requester's Reddit username: user... |
| n20 | chain exhausted | the chain from n15 had 3 attempts without a real gain; the search moves elsewhere |
| n24 | no-op | same predictions as n17: I will add a timezone-offset feature computed as the difference between the request's l... |
| n26 | no-op | same predictions as n8: I will add a single numeric feature that counts how many of a curated set of need-relat... |
| n34 | no-op | same predictions as n31: I will add two handcrafted features derived from the request text and title: a binary i... |
| n49 | no-op | same predictions as n44: Add URL/link features to the handcrafted feature block: counts of http/https/www links ... |
| n54 | intervention | divergence_prune: prune n51 {"anchor": "n50", "node": "n54", "steps": 2, "val_gain": 0.01017, "probe_loss": 0.04676, "consistent_share": 0.979}, applied - since n50, validation +1.0% but probe -4.7% over 2 nodes, ending at n54 |
| n56 | crash | runtime_error: TypeError: Sparse data was passed for X, but dense data is required. Use '.toarray()' to convert to a dense numpy array. |
| n58 | fixed | debug fixed the crash in n56 after 1 attempt(s) |
| n72 | intervention | divergence_prune: prune n57 {"anchor": "n50", "node": "n72", "steps": 4, "val_gain": 0.03048, "probe_loss": 0.06704, "consistent_share": 0.984}, applied - since n50, validation +3.0% but probe -6.7% over 4 nodes, ending at n72 |
| n76 | overfitting | beat n55 on validation (0.6347 -> 0.6573) but got worse on test (0.6534 -> 0.6186) |
| n83 | crash | runtime_error: TypeError: Sparse data was passed for X, but dense data is required. Use '.toarray()' to convert to a dense numpy array. |
| n84 | fixed | debug fixed the crash in n83 after 1 attempt(s) |
| n88 | crash | runtime_error: NameError: name 'X_test' is not defined. Did you mean: 'test'? |
| n90 | fixed | debug fixed the crash in n88 after 1 attempt(s) |
| n91 | crash | runtime_error: exit code 1 |
| n92 | fixed | debug fixed the crash in n91 after 1 attempt(s) |
| n93 | crash | runtime_error: TypeError: StringMethods.count() got an unexpected keyword argument 'regex' |
| n94 | fixed | debug fixed the crash in n93 after 1 attempt(s) |
| n98 | no-op | same predictions as n97: Add a block of one-hot indicator features for the 20 most common subreddits in `request... |
| n101 | crash | generation_error: empty reply |
| n110 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n15 | final pick | val 0.6936 (rank 1 of 85), test 0.6671 (rank 15 of 85) |
| n105 | best on test | test 0.6839, but val rank 40 of 85: Replace the SGDClassifier with a HistGradientBoostingClassifier, which should substanti... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
