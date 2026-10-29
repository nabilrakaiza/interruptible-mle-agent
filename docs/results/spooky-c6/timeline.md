# Trajectory: C6_spooky-author-identification_seed100

- **Task** spooky-author-identification, **condition** C6, **seed** 100
- **Nodes** 52 (67% working), **budget used** 120.0 min, **LLM** 58 calls, 788,116 tokens
- **Interventions** 12 applied, 0 dropped
- **Model cards** TF-IDF with linear classifiers, Multinomial naive Bayes with bag-of-words, Calibrated multiclass probability pipeline, Temperature scaling for softmax probabilities, Feature hashing for large text corpora, DictVectorizer for sparse dictionary features
- **Search** 5 improve chains exhausted; longest stretch without a new best 11 nodes; selection regret 0.0001 on test

Lower scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Use TF-IDF vectorization with sublinear term frequency, English stop words, and frequency-based filtering t... (val 0.6151) |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF with linear classifiers" |
| n0 | card used | first script with TfidfVectorizer from the card "Multinomial naive Bayes with bag-of-words" |
| n1 | draft | Use a CountVectorizer with word unigrams and bigrams to convert the sentences into sparse count features, f... (val 0.6334) |
| n2 | draft | Use feature hashing to avoid building a full vocabulary, with 2^18 hash dimensions and word bigrams, follow... (val 0.7513) |
| n2 | card used | first script with HashingVectorizer, TfidfTransformer from the card "Feature hashing for large text corpora" |
| n2 | card used | first script with TfidfTransformer from the card "DictVectorizer for sparse dictionary features" |
| n3 | draft | Use character n-gram TF-IDF features instead of word-level representations, since character patterns captur... (val 0.4420) |
| n3 | new best | val 0.4420, probe 0.4534: Use character n-gram TF-IDF features instead of word-level representations, since chara... |
| n4 | draft | Build a multi-view TF-IDF feature set by combining word unigrams/bigrams with character 3-5 grams from the ... (val 0.4686) |
| n7 | new best | val 0.4393, probe 0.4499, 0.61% better than n3: Expand the character-level TF-IDF vocabulary from 200k to 400k features and include bou... |
| n8 | new best | val 0.4382, probe 0.4483, 0.24% better than n7: Fit the TF-IDF vectorizer on the concatenation of train and test texts instead of only ... |
| n9 | new best | val 0.4336, probe 0.4446, 1.07% better than n8: Use averaged SGD updates by adding `average=True` to the SGDClassifier while keeping th... |
| n10 | new best | val 0.4232, probe 0.4376, 2.40% better than n9: Add temperature scaling calibration to the existing averaged SGD classifier. Keep the c... |
| n13 | new best | val 0.4230, probe 0.4377, 0.04% better than n10: Change the SGD averaging schedule from averaging from the first update (average=True) t... |
| n14 | new best | val 0.4215, probe 0.4375, 0.35% better than n13: Replace the single SGDClassifier with a two-seed ensemble of otherwise identical SGDCla... |
| n15 | new best | val 0.4211, probe 0.4373, 0.10% better than n14: Use three independent averaged-SGD fits instead of two in both the temperature-calibrat... |
| n16 | new best | val 0.4210, probe 0.4363, 0.01% better than n15: Increase the number of independent averaged-SGD fits from three to five in both the tem... |
| n17 | new best | val 0.3821, probe 0.3944, 9.26% better than n16: Add a word-level TF-IDF view (word unigrams and bigrams) and concatenate it with the ex... |
| n18 | new best | val 0.3799, probe 0.3914, 0.55% better than n17: Add a compact set of sentence-shape features to the existing TF-IDF stack: log-transfor... |
| n18 | intervention | human: redirect n4 {"operator": "improve"}, applied - n4 close to n3 as a draft (0.469 vs 0.442), never expanded |
| n19 | intervention | human: correct f-738ab0da36 {"replacement": "As untuned drafts, word+char TF-IDF (n4, val 0.469) was slightly worse than char-only (n3, 0.442). But adding a word-level TF-IDF view to the tuned char pipeline (n17) gave the largest gain so far: val 0.421 to 0.382, probe 0.436 to 0.394. Word features add signal that character n-grams miss."}, applied - n17 contradicts this finding: adding word TF-IDF to the char pipeline gave the biggest gain so far, and the probe confirms it. |
| n20 | new best | val 0.3787, probe 0.3900, 0.33% better than n18: Add a compact set of surface-form features to the existing manual feature block: counts... |
| n21 | new best | val 0.3738, probe 0.3871, 1.30% better than n20: Add a third TF-IDF view using word n-grams with lowercase=False, which preserves capita... |
| n26 | new best | val 0.3699, probe 0.3788, 1.03% better than n21: Tune the L2 regularization strength (alpha) of the SGDClassifier on the existing valida... |
| n27 | new best | val 0.3660, probe 0.3752, 1.06% better than n26: Add a third character-level TF-IDF view using the `char` analyzer instead of the existi... |
| n28 | new best | val 0.3650, probe 0.3740, 0.28% better than n27: Add a block of function-word count features to the manual dense feature set. Function-w... |
| n29 | new best | val 0.3637, probe 0.3757, 0.34% better than n28: Add a rare-word unigram TF-IDF view to the existing feature stack. The current word vec... |
| n31 | intervention | human: prune n0, applied - far behind (val 0.615); with 60 min left and the main branch ~0.25 ahead, not worth exploring |
| n31 | intervention | human: prune n1, applied - far behind (val 0.633, probe 0.592); was waiting for a chance pick, but with 60 min left it can't catch up |
| n31 | intervention | human: prune n2, applied - branch stalled (n5 0.531, n12 0.535), far behind; prunes n5 and n12 too |
| n31 | intervention | human: prune n4, applied - redirect n19 showed no gain; its word+char idea is already used by the main branch (n17) |
| n32 | chain exhausted | the chain from n29 had 3 attempts without a real gain; the search moves elsewhere |
| n36 | new best | val 0.3636, probe 0.3763, 0.02% better than n29: Add a rare-word unigram TF-IDF view to the existing feature stack. The current word and... |
| n36 | intervention | human: redirect n30 {"operator": "improve"}, applied - n30 has the best probe score in the run (0.3688 vs 0.3757 for n29), but greedy follows validation (0.3661 vs 0.3637), so it would not be continued. Note: steering by the probe makes it a little less independent for the final pick. |
| n40 | intervention | human: prune n11, applied - duplicate of n9 (same predictions, val 0.434), ~0.07 behind the best; only takes random exploration picks |
| n40 | intervention | human: prune n22, applied - crashed exploration pick on an old node; its debug n23 scored 0.470, ~0.11 behind the best |
| n40 | intervention | human: prune n34, applied - n34 duplicated n7 (0.439) and its child n38 reached only 0.421, ~0.06 behind the best; dead-end side branch |
| n40 | intervention | human: prune n6, applied - early side branch (val 0.527, LBFGS instead of SGD), far behind; only takes random exploration picks |
| n41 | chain exhausted | the chain from n36 had 3 attempts without a real gain; the search moves elsewhere |
| n45 | intervention | human: prune n37, applied - n42 best on validation (0.3622) but probe got worse (0.3829 vs n30's 0.3688): validation and probe diverge since n30 |
| n48 | new best | val 0.3612, probe 0.3733, 0.66% better than n36: Add a content-word TF-IDF view that removes English stop words before vectorizing word ... |
| n49 | new best | val 0.3612, probe 0.3732, 0.01% better than n48: Add a dense archaic/formal-diction feature block to the existing manual feature stack. ... |
| n51 | crash | timeout: killed after 1s |
| n51 | chain exhausted | the chain from n48 had 3 attempts without a real gain; the search moves elsewhere |
|  | stop | budget, final selection best_val |
| n49 | final pick | val 0.3612 (rank 1 of 35), test 0.3684 (rank 2 of 35) |
| n48 | best on test | test 0.3683, but val rank 2 of 35: Add a content-word TF-IDF view that removes English stop words before vectorizing word ... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
