# Trajectory: C6_random-acts-of-pizza_seed100

- **Task** random-acts-of-pizza, **condition** C6, **seed** 100
- **Nodes** 126 (22% working), **budget used** 240.4 min, **LLM** 141 calls, 2,878,046 tokens
- **Interventions** 79 applied, 15 dropped
- **Model cards** TF-IDF bag-of-words with linear classifier, TF-IDF with word n-grams, Random forest with probability calibration, Calibrated classifier with sigmoid or isotonic regression, Gradient boosted trees for tabular features, AdaBoost with shallow decision trees, Metadata-stripped document text pipeline
- **Search** 27 improve chains exhausted; longest stretch without a new best 31 nodes; selection regret 0.0152 on test

Higher scores are better.

| Node | Event | Note |
|---|---|---|
| n0 | draft | Build a logistic regression baseline on a combination of TF-IDF text features and standardized numeric meta... (val 0.6514) |
| n0 | card used | first script with LogisticRegression, TfidfVectorizer from the card "TF-IDF bag-of-words with linear classifier" |
| n0 | card used | first script with TfidfVectorizer from the card "TF-IDF with word n-grams" |
| n0 | card used | first script with TfidfVectorizer from the card "Metadata-stripped document text pipeline" |
| n1 | draft | I will use a gradient-boosted tree model on dense features rather than a linear classifier. Features includ... (val -) |
| n1 | crash | runtime_error: re.PatternError: nothing to repeat at position 0 |
| n1 | card used | first script with GradientBoostingClassifier, HistGradientBoostingClassifier from the card "Gradient boosted trees for tabular features" |
| n2 | draft | I will build a random forest classifier on dense features derived from both text and metadata. The request ... (val 0.6693) |
| n2 | card used | first script with RandomForestClassifier from the card "Random forest with probability calibration" |
| n3 | draft | I will build a two-model ensemble that is distinct from the earlier baselines. The first model is a Complem... (val 0.5639) |
| n4 | draft | I will build a single linear model using SGD with modified Huber loss on a sparse matrix of TF-IDF unigrams... (val 0.5237) |
| n5 | fixed | debug fixed the crash in n1 after 1 attempt(s) |
| n5 | new best | val 0.6424, probe 0.6849: The crash was caused by pandas `str.count("?")`, which treats the pattern as a regex an... |
| n9 | intervention | human: prune n4, applied - Claude: weakest draft (SGD modified-Huber on TF-IDF), val 0.524, near chance and 0.15 below the best (n8 0.675). |
| n9 | intervention | human: prune n3, applied - Claude: weak draft (ComplementNB ensemble), val 0.564, 0.11 below the best; not worth improving. |
| n9 | intervention | human: prune n7, applied - Claude: regression. The n6->n7 debug of n2's branch scores 0.641, below its ancestor n2 (0.669); the handcrafted-feature path hurts. |
| n11 | intervention | human: prune n9, applied - Claude: duplicate of n8. Its RF+LR blend search picked w=1.0 (pure RF), so the predictions and val (0.67525) are identical to n8; it adds a slower, more complex script for no gain. |
| n11 | intervention | human: prune n10, applied - Claude: regression. Changing n8's RF max_features drops val to 0.651 from n8's 0.675. |
| n12 | new best | val 0.6814, probe 0.6984, 6.08% better than n5: Replace the HashingVectorizer with a TfidfVectorizer that uses sublinear term frequenci... |
| n13 | new best | val 0.6816, probe 0.6863, 0.03% better than n12: Add a smoothed out-of-fold target encoding of the requester's subreddit history as a ne... |
| n13 | overfitting | beat n12 on validation (0.6814 -> 0.6816) but got worse on test (0.6795 -> 0.6712) |
| n14 | new best | val 0.6849, probe 0.6823, 0.47% better than n13: Add a character n-gram TF-IDF representation of the same concatenated text (body, title... |
| n16 | new best | val 0.6912, probe 0.6720, 0.93% better than n14: Expand the word-level TF-IDF representation from bigrams to word trigrams and raise the... |
| n18 | new best | val 0.6965, probe 0.6834, 0.76% better than n16: Add a dedicated TF-IDF view of the request title, separate from the combined text field... |
| n21 | intervention | human: prune n11, applied - Claude: regression. Swapping n8's RF for ExtraTrees gives 0.672 < n8 0.675, and that branch now trails the best (n18 0.696) by 0.02. |
| n21 | intervention | human: prune n15, applied - Claude: regression. More char n-gram SVD components score 0.676 < parent n14 0.685. |
| n21 | intervention | human: prune n17, applied - Claude: regression. Username-derived features score 0.685 < parent n16 0.691. |
| n21 | intervention | human: prune n19, applied - Claude: regression. The OOF LR stacking feature scores 0.685 < parent n18 0.696 (the current best). |
| n21 | intervention | human: prune n0, applied - Claude: superseded. The LR baseline at 0.651 is 0.045 below the best; the GBM chain (n5->n18) already covers TF-IDF text. |
| n22 | chain exhausted | the chain from n18 had 3 attempts without a real gain; the search moves elsewhere |
| n30 | intervention | human: prune n20, applied - Claude: regression. The subreddit TF-IDF view scores 0.690 < parent n18 0.6965 (best). |
| n30 | intervention | human: prune n22, applied - Claude: regression. The HGB+LR weighted ensemble scores 0.685 < parent n18 0.6965. |
| n30 | intervention | human: prune n23, applied - Claude: regression and a near-duplicate of n18's title view (SVD-32 version); 0.684 < parent n16 0.691. |
| n30 | intervention | human: prune n24, applied - Claude: regression. Lower LR / more iterations scores 0.689 < parent n16 0.691. |
| n30 | intervention | human: prune n25, applied - Claude: regression. Title target encoding scores 0.685 < parent n21 0.685 (no gain). |
| n30 | intervention | human: prune n26, applied - Claude: regression. n-gram target encoding scores 0.682 < parent n21 0.685. |
| n30 | intervention | human: prune n27, applied - Claude: regression. NMF topics score 0.680 < parent n21 0.685. |
| n30 | intervention | human: prune n21, applied - Claude: weak side branch. Word target encoding at 0.685 is 0.012 below the best, and all 3 of its children regressed; focusing on the n18 chain. |
| n30 | intervention | human: prune n28, applied - Claude: regression. Text-style features score 0.681 < parent n14 0.685. |
| n30 | intervention | human: prune n29, applied - Claude: regression. Max subreddit target encoding scores 0.682 < parent n14 0.685. |
| n37 | new best | val 0.7018, probe 0.6747, 0.76% better than n18: Expand the word-level TF-IDF vectorizer from bigrams with a 50,000 vocabulary cap to tr... |
| n41 | intervention | human: prune n31, applied - Claude: regression. Categorical time columns score 0.650 < parent n30 0.688. |
| n41 | intervention | human: prune n32, applied - Claude: duplicate of n37. Same change (word trigrams, larger vocab) on the same parent n30, with identical val 0.70179; keeping n37, whose child n38 is the best. |
| n41 | intervention | human: prune n33, dropped (already pruned) - Claude: regression. Char n-gram SVD scores 0.688 < parent n32 0.702. |
| n41 | intervention | human: prune n35, dropped (already pruned) - Claude: regression. 128 SVD components score 0.685 < parent n32 0.702. |
| n41 | intervention | human: prune n36, dropped (already pruned) - Claude: regression. Username features score 0.700 < parent n32 0.702; it's also under the duplicate n32. |
| n41 | intervention | human: prune n34, applied - Claude: weak, regression. The OOF RF meta-feature scores 0.641 < parent n5 0.642, far below the best 0.703. |
| n41 | intervention | human: prune n39, applied - Claude: regression. Subreddit co-occurrence SVD scores 0.682 < parent n38 0.703 (best). |
| n41 | intervention | human: prune n40, applied - Claude: regression. A body-only TF-IDF view scores 0.688 < parent n38 0.703. |
| n48 | new best | val 0.7033, probe 0.6879, 0.21% better than n37: Add a dedicated TF-IDF view of the request title, separate from the combined request-te... |
| n49 | new best | val 0.7075, probe 0.6870, 0.60% better than n48: Replace the HistGradientBoostingClassifier settings with a lower learning rate (0.02), ... |
| n50 | new best | val 0.7133, probe 0.6842, 0.83% better than n49: Add a 32-component NMF topic-feature block derived from the combined TF-IDF matrix and ... |
| n52 | intervention | human: prune n38, applied - Claude: duplicate. n38, n42 and n48 are the same title-TF-IDF change on n37 with identical val 0.70327; keeping n48, whose line (n49 -> n50) is now the best. |
| n52 | intervention | human: prune n41, dropped (already pruned) - Claude: regression. The 5-HGB soft-vote scores 0.701 < parent n38 0.703. |
| n52 | intervention | human: prune n42, applied - Claude: duplicate of n48 (same change on n37, identical val 0.70327). |
| n52 | intervention | human: prune n44, dropped (already pruned) - Claude: regression. Dropping subreddit text scores 0.656 < parent n42 0.703. |
| n52 | intervention | human: prune n46, dropped (already pruned) - Claude: regression. The OOF LR meta-feature scores 0.685 < parent n42 0.703. |
| n52 | intervention | human: prune n47, dropped (already pruned) - Claude: regression. class_weight=balanced scores 0.694 < parent n42 0.703. |
| n52 | intervention | human: prune n45, applied - Claude: no effect. URL/verification counts give exactly the parent n12's val (0.68144), and the branch is 0.03 below the best. |
| n52 | intervention | human: prune n43, applied - Claude: regression in a weak family. The RF subreddit tweak scores 0.6686 < parent n2 0.669. |
| n52 | intervention | human: prune n8, applied - Claude: weak family. The RF line peaked at 0.675, 0.04 below the best (n50 0.713); not worth more steps. |
| n52 | intervention | human: prune n2, applied - Claude: weak family. The RF root (0.669) keeps being expanded with no gain; 0.04 below the best. |
| n53 | chain exhausted | the chain from n50 had 3 attempts without a real gain; the search moves elsewhere |
| n60 | intervention | human: prune n51, applied - Claude: regression. Title NMF scores 0.698 < parent n50 0.713 (best). |
| n60 | intervention | human: prune n52, applied - Claude: regression. 1200 iterations score 0.710 < parent n50 0.713. |
| n60 | intervention | human: prune n53, applied - Claude: regression. The extended subreddit target-encoding block scores 0.707 < parent n50 0.713. |
| n60 | intervention | human: prune n54, applied - Claude: regression. Username features score 0.703 < parent n49 0.707. |
| n60 | intervention | human: prune n55, applied - Claude: regression. Centroid-similarity features score 0.690 < parent n49 0.707. |
| n60 | intervention | human: prune n56, applied - Claude: regression. LDA topics score 0.692 < parent n49 0.707. |
| n60 | intervention | human: prune n58, applied - Claude: regression. Subreddit NMF scores 0.702 < parent n57 0.711. |
| n60 | intervention | human: prune n59, applied - Claude: regression. The LR text meta-feature scores 0.693 < parent n57 0.711. |
| n67 | intervention | human: prune n60, applied - Claude: no effect. Narrative-cue counts give exactly the parent n57's val (0.71125); dead end. |
| n67 | intervention | human: prune n61, applied - Claude: regression. Text-cue density features score 0.684 < parent n48 0.703. |
| n67 | intervention | human: prune n62, applied - Claude: regression. Logistics indicators score 0.700 < parent n48 0.703. |
| n67 | intervention | human: prune n63, applied - Claude: regression and a holdout concern. It fits TF-IDF/SVD on train+predict text (unsupervised, but it uses held-out rows); 0.677 < parent n48 0.703. |
| n67 | intervention | human: prune n66, applied - Claude: regression. Readability features score 0.704 < parent n65 0.711. |
| n69 | new best | val 0.7135, probe 0.6917, 0.02% better than n50: The current model captures keyword counts and TF-IDF topics but does not explicitly mea... |
| n73 | intervention | human: prune n67, applied - Claude: regression. Temporal request-volume features score 0.708 < parent n65 0.711. |
| n73 | intervention | human: prune n68, applied - Claude: regression in an old, weak line. The subreddit one-hot scores 0.681 < parent n12 0.681, 0.03 below the best. |
| n73 | intervention | human: prune n70, applied - Claude: regression. Refit after early stopping scores 0.703 < parent n69 0.7135 (best). |
| n73 | intervention | human: prune n71, applied - Claude: regression. A different early-stopping metric scores 0.693 < parent n64 0.706. |
| n73 | intervention | human: prune n72, applied - Claude: regression. Username features score 0.711 < parent n69 0.7135; username features have now failed 3 times (n17, n54, n72). |
| n74 | chain exhausted | the chain from n69 had 3 attempts without a real gain; the search moves elsewhere |
| n79 | intervention | human: prune n73, applied - Claude: regression. The OOF LR stacking feature scores 0.696 < parent n65 0.711 (stacking has now failed 3 times: n19, n46, n73). |
| n79 | intervention | human: prune n74, applied - Claude: regression. Title location features score 0.711 < parent n69 0.7135 (best). |
| n79 | intervention | human: prune n75, applied - Claude: regression. Subreddit TF-IDF/SVD scores 0.705 < parent n64 0.706. |
| n79 | intervention | human: prune n76, applied - Claude: duplicate of n65. The same LR 0.02 / 600-iteration change on n64 gives the identical val 0.7108964938064246. |
| n79 | intervention | human: prune n77, dropped (already pruned) - Claude: regression. Char TF-IDF scores 0.704 < parent n76 0.711. |
| n79 | intervention | human: prune n78, dropped (already pruned) - Claude: regression. The seed-averaged HGB ensemble scores 0.705 < parent n76 0.711. |
| n86 | intervention | human: prune n80, applied - Claude: duplicate of n65 (3rd time: n65, n76, n80). The same LR 0.02 / 600-iteration change on n64 gives the identical val 0.7108964938064246; this also prunes its children n81-n83. |
| n86 | intervention | human: prune n81, dropped (already pruned) - Claude: no effect. Count-weighted target encoding gives exactly the parent n80's val. |
| n86 | intervention | human: prune n82, dropped (already pruned) - Claude: regression. The OOF LR text feature scores 0.692 < parent n80 0.711 (stacking has failed 4 times). |
| n86 | intervention | human: prune n83, dropped (already pruned) - Claude: regression. The hardship lexicon scores 0.709 < parent n80 0.711. |
| n86 | intervention | human: prune n84, applied - Claude: regression. The binary n-gram decomposition scores 0.687 < parent n64 0.706. |
| n93 | intervention | human: prune n85, applied - Claude: near-duplicate. n85 and n90 both add specificity/verifiability cues to n37; n90 (0.708) beats n85 (0.706), and n90's child n91 (0.713) is near the best. Pruning n85 removes its weaker subtree. |
| n93 | intervention | human: prune n87, dropped (already pruned) - Claude: regression. Categorical calendar fields score 0.687 < parent n85 0.706 (this failed before as n31). |
| n93 | intervention | human: prune n88, dropped (already pruned) - Claude: regression. NMF scores 0.689 < parent n85 0.706. |
| n93 | intervention | human: prune n89, dropped (already pruned) - Claude: under the pruned near-duplicate n85. Word target encoding gives 0.707, below n90's line (n91 0.713) and the best n69 (0.7135). |
| n93 | intervention | human: prune n86, applied - Claude: regression in a weak old line. Readability features score 0.634 < parent n5 0.642. |
| n93 | intervention | human: prune n92, applied - Claude: regression. Char TF-IDF scores 0.700 < parent n91 0.713 (char n-grams have now failed 3 times: n15, n33, n92). |
| n100 | intervention | human: prune n93, applied - Claude: regression. Username features score 0.710 < parent n91 0.713 (username features have now failed 4 times). |
| n100 | intervention | human: prune n94, applied - Claude: regression. Splitting the combined-text view scores 0.688 < parent n91 0.713. |
| n100 | intervention | human: prune n97, applied - Claude: regression. The HGB iteration change scores 0.7126 < parent n96 0.7131. |
| n100 | intervention | human: prune n98, applied - Claude: regression. More SVD components score 0.707 < parent n96 0.713. |
| n101 | new best | val 0.7153, probe 0.6858, 0.25% better than n69: Add a compact location-specificity feature block to the dense feature matrix. Concrete ... |
| n106 | chain exhausted | the chain from n101 had 3 attempts without a real gain; the search moves elsewhere |
| n107 | intervention | human: prune n100, applied - Claude: regression. The body-only SVD view scores 0.688 < parent n37 0.702 (it failed before as n40). |
| n107 | intervention | human: prune n102, applied - Claude: regression. Title-location parsing scores 0.711 < parent n101 0.7153 (best). |
| n107 | intervention | human: prune n104, applied - Claude: regression. Verifiability/contact counts score 0.705 < parent n101 0.7153. |
| n107 | intervention | human: prune n106, applied - Claude: regression. Pizza-order specificity scores 0.710 < parent n101 0.7153. |
| n107 | intervention | human: prune n103, applied - Claude: regression. Narrative-engagement features score 0.708 < parent n99 0.710. |
| n107 | intervention | human: prune n105, applied - Claude: regression. NMF scores 0.707 < parent n99 0.710. |
| n114 | intervention | human: prune n107, applied - Claude: regression. The OOF HGB+RF ensemble scores 0.702 < parent n99 0.710. |
| n114 | intervention | human: prune n108, applied - Claude: regression. Title SVD on the old n30 scores 0.686 < parent n30 0.688; that line was superseded long ago. |
| n114 | intervention | human: prune n109, applied - Claude: regression. Char n-grams score 0.696 < parent n90 0.708 (4th char n-gram failure). |
| n114 | intervention | human: prune n112, applied - Claude: regression. The hardship lexicon scores 0.713 < parent n111 0.7137. |
| n114 | intervention | human: prune n113, applied - Claude: regression. Subreddit TF-IDF/SVD scores 0.683 < parent n111 0.714. |
| n123 | intervention | human: prune n114, applied - Claude: regression. Community-identity cues score 0.7134 < parent n111 0.7137. |
| n123 | intervention | human: prune n116, applied - Claude: regression. Function-word style features score 0.698 < parent n110 0.711. |
| n123 | intervention | human: prune n117, applied - Claude: regression. Location specificity on the old n30 scores 0.678 < parent n30 0.688. |
| n123 | intervention | human: prune n118, applied - Claude: regression. KMeans cluster distances score 0.707 < parent n110 0.711. |
| n123 | intervention | human: prune n119, applied - Claude: regression. The OOF LR meta-feature scores 0.686 < parent n110 0.711 (stacking has failed 5 times). |
| n123 | intervention | human: prune n122, applied - Claude: duplicate of n120. The same NMF block on n90 gives the identical val 0.7086031751158772. |
| n125 | crash | timeout: killed after 1s |
|  | stop | budget, final selection best_val |
| n101 | final pick | val 0.7153 (rank 1 of 28), test 0.6671 (rank 25 of 28) |
| n16 | best on test | test 0.6823, but val rank 23 of 28: Expand the word-level TF-IDF representation from bigrams to word trigrams and raise the... |

## Annotations

(Written by hand for the report: what this run shows, and what an intervention did or could have done.)
