# Trajectory: A1-off_random-acts-of-pizza_seed1

- **Task** random-acts-of-pizza, **condition** A1-off, **seed** 1
- **Nodes** 113 (96% working), **budget used** 240.0 min, **LLM** 128 calls, 2,439,534 tokens
- **Interventions** 0 applied, 0 dropped
- **Model cards** TF-IDF vectorization with linear classification, Random forest with probability calibration, Metadata-stripping text classifier, N-gram TF-IDF text features, Iterative ensemble fitting with warm start, Gradient boosted decision trees, AdaBoost with weak learners, Calibrated classifier pipeline
- **Search** 17 improve chains exhausted; longest stretch without a new best 24 nodes; selection regret 0.0034 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | I will build a simple text-plus-metadata classifier. I’ll vectorize the combined request title and body wit... (val 0.6463) |
| n0 | new best | val 0.6463, probe 0.6245: I will build a simple text-plus-metadata classifier. I’ll vectorize the combined reques... |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF vectorization with linear classification" |
| n0 | card used | first script with TfidfVectorizer from the card "Metadata-stripping text classifier" |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "N-gram TF-IDF text features" |
| n1 | draft | I will build a text-plus-metadata classifier using a hashing TF-IDF representation of the request title and... (val -) |
| n1 | crash | runtime_error: ValueError: Input contains NaN. |
| n2 | draft | I will build a text-plus-metadata classifier that differs from the earlier linear baselines by using trunca... (val 0.6724) |
| n2 | new best | val 0.6724, probe 0.6987, 4.03% better than n0: I will build a text-plus-metadata classifier that differs from the earlier linear basel... |
| n2 | card used | first script with RandomForestClassifier from the card "Random forest with probability calibration" |
| n2 | card used | first script with RandomForestClassifier from the card "Iterative ensemble fitting with warm start" |
| n3 | draft | I will build a text-plus-metadata classifier using TF-IDF on the combined title and edit-aware request body... (val 0.6338) |
| n3 | card used | first script with GradientBoostingClassifier, HistGradientBoostingClassifier from the card "Gradient boosted decision trees" |
| n4 | draft | I will build a text-plus-metadata classifier using TF-IDF on the title and edit-aware request body, reduced... (val -) |
| n4 | crash | runtime_error: exit code 1 |
| n5 | crash | runtime_error: sklearn.exceptions.NotFittedError: This TruncatedSVD instance is not fitted yet. Call 'fit' with appropriate arguments before using this ... |
| n6 | fixed | debug fixed the crash in n1 after 2 attempt(s) |
| n7 | new best | val 0.6756, probe 0.6713, 0.48% better than n2: I will add the requester’s subreddit history as an additional text signal. Specifically... |
| n8 | fixed | debug fixed the crash in n4 after 1 attempt(s) |
| n10 | new best | val 0.6756, probe 0.6712, 0.00% better than n7: Add temporal features derived from the request timestamp (hour, day of week, month, yea... |
| n12 | new best | val 0.6775, probe 0.6664, 0.28% better than n10: Add a set of linguistic/pragmatic features extracted from the request text: counts of f... |
| n14 | new best | val 0.6791, probe 0.6804, 0.23% better than n12: Change the TfidfVectorizer to keep stop words instead of removing English stop words. I... |
| n17 | new best | val 0.6848, probe 0.6878, 0.84% better than n14: Add cyclic encoding of the temporal features (hour, day-of-week, month) as sine/cosine ... |
| n22 | new best | val 0.7055, probe 0.6818, 3.02% better than n17: Add a second text stream using character n-gram TF-IDF followed by truncated SVD, runni... |
| n25 | chain exhausted | the chain from n22 had 3 attempts without a real gain; the search moves elsewhere |
| n47 | new best | val 0.7074, probe 0.6775, 0.27% better than n22: Increase the random forest's `n_estimators` from 200 to 500 while keeping `max_samples=... |
| n50 | chain exhausted | the chain from n47 had 3 attempts without a real gain; the search moves elsewhere |
| n57 | new best | val 0.7105, probe 0.6745, 0.43% better than n47: Relax the random forest regularization by removing the max_depth constraint and lowerin... |
| n62 | chain exhausted | the chain from n57 had 3 attempts without a real gain; the search moves elsewhere |
| n69 | new best | val 0.7129, probe 0.6699, 0.34% better than n57: Replace the fixed-weight soft-voting ensemble with a stacking ensemble that learns the ... |
| n71 | new best | val 0.7199, probe 0.6786, 0.98% better than n69: Apply a sign-preserving log1p transformation to the skewed numeric features (account ag... |
| n75 | chain exhausted | the chain from n71 had 3 attempts without a real gain; the search moves elsewhere |
| n85 | new best | val 0.7215, probe 0.6814, 0.21% better than n71: Add a HistGradientBoostingClassifier as a third base learner inside the StackingClassif... |
| n88 | chain exhausted | the chain from n85 had 3 attempts without a real gain; the search moves elsewhere |
| n97 | overfitting | beat n95 on validation (0.7180 -> 0.7190) but got worse on test (0.6974 -> 0.6876) |
| n104 | new best | val 0.7240, probe 0.6780, 0.35% better than n85: Add a HistGradientBoostingClassifier as a third base learner in the stacking ensemble, ... |
| n105 | new best | val 0.7255, probe 0.6750, 0.21% better than n104: Add `class_weight='balanced'` to the HistGradientBoostingClassifier base learner in the... |
| n106 | new best | val 0.7255, probe 0.6757, 0.01% better than n105: I will add `class_weight='balanced'` to the LogisticRegression used as the final estima... |
| n109 | chain exhausted | the chain from n105 had 3 attempts without a real gain; the search moves elsewhere |
| n110 | new best | val 0.7256, probe 0.6781, 0.01% better than n106: Replace the raw `requester_upvotes_minus_downvotes_at_request` numeric feature with a s... |
| n112 | crash | timeout: killed after 7s |
|  | stop | budget, final selection best_val |
| n110 | final pick | val 0.7256 (rank 1 of 109), test 0.6954 (rank 20 of 109) |
| n111 | best on test | test 0.6988, but val rank 23 of 109: Change the word-level TF-IDF vectorizer's n-gram range from `(1, 3)` to `(1, 2)`. Trigr... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
