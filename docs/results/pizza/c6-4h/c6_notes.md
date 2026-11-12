# C6 notes: random-acts-of-pizza seed 100 (4 h)

All monitoring and interventions in this run are by Claude (Claude Code), not a human. The user was busy, so Claude was the intervener.

## Setup
- 3rd launch, started 13:04 12 Nov 2026. Earlier tries are in runs/aborted/:
  - `_nodocker` (12:20): docker was not on the launch shell's PATH; it failed at n0. Claude's mistake.
  - `_crbug` (12:23-12:40): every node was invalid because predict.csv parsed as 2027 rows vs 2026 labels. See its c6_notes.md.
- Fix (local, uncommitted, approved by the user): `src/imle/stand_in_evaluation.py` writes pizza's train.csv and predict.csv with `quoting=csv.QUOTE_NONNUMERIC`. One test post (and 4 train posts) in MLE-bench's data has a bare `\r` that pandas left unquoted. With the fix, the frames read back exactly the same as before on all rows without a CR. Other tasks are unchanged. Stand-in tests pass 7/7.
- Machine: MacBook Pro M-series, Docker sandbox on Colima (2 CPU, 5 GB), CPU only. Nabil's pizza grid ran on Kaggle CPU in a subprocess sandbox, so the setups differ.
- At launch: battery 91% and discharging (the user will plug in at 70-80%), disk 1.6 GB free, swap 2.4 GB.

## 13:06 (Claude)
- n0 (TF-IDF + numeric, LR) working, val 0.6514. No action.

## 13:27 (Claude)
- Battery 88%, discharging. DISK 309 MB (swap 3.6 GB), below the floor. Claude cleared only re-downloadable caches (pip cache 37 MB, Homebrew downloads, 4 conda tarballs 78 MB), which brought it to 539 MB. Asked the user about Chrome's 4.1 GB cache.
- Nodes: n0 LR 0.651; n1 GBM buggy (str.count("?") regex) -> n5 debug 0.642; n2 RF 0.669 -> n8 (class weighting) 0.675 = best; n6 (n2 + handcrafted feats) buggy -> n7 0.641; n3 CNB 0.564; n4 SGD 0.524.
- Claude interventions (3 prunes): n4 (near chance), n3 (weak), n7 (regression below its ancestor n2). Kept: n8/n2 branch (best), n0 (linear text baseline), n5 (GBM, a different family).
- 13:3x: with the user's OK, Claude cleared Chrome's Cache/Code Cache folders (about 4 GB; Storage kept). Disk now 4.6 GB free, swap 3.75 GB.

## 13:30 (Claude)
- Battery 88%, disk 4.6 GB, swap 3.7 GB. Alive, no errors. The 3 prunes from 13:27 (n4, n3, n7) were applied.
- New: n9 (n8 + LR blend) val 0.67525, identical to n8 because the blend chose pure RF; n10 (n8, RF max_features change) val 0.651.
- Claude interventions: pruned n9 (duplicate of n8) and n10 (regression). n8 is still the best and is kept.

## 13:44 (Claude)
- Battery 85%, discharging. Disk 3.6 GB (down 1 GB in 15 min), swap 4.6 GB; told the user to close heavy apps. Alive, no errors. n9/n10 prunes applied.
- The GBM chain took off: n5 0.642 -> n12 (sublinear TF-IDF) 0.681 -> n13 (OOF subreddit target encoding) 0.682 -> n14 (char n-grams) 0.685 -> n16 (word trigrams) 0.691 -> n18 (separate title TF-IDF) 0.6965 = new best. No label peeking seen in n13/n18 (target encoding is out-of-fold on train).
- Claude interventions: pruned n11, n15, n17, n19 (each below its parent) and n0 (superseded baseline). Kept: the n18 chain (best), n8 (RF, 0.675) as a second family.

## 13:59 (Claude)
- Battery 82%, discharging; reminded the user to plug in. Disk 3.6 GB, swap 4.8 GB (stable since 13:44). Alive, no errors. 13:44 prunes applied (10 lines in applied.jsonl).
- 10 new nodes (n20-n29), none beating n18 (0.6965). Each is below its parent, except n21 (0.685 vs n13 0.682), whose 3 children all regressed.
- Claude interventions: pruned n20, n22, n23, n24, n25, n26, n27, n21, n28, n29 to focus the search on the n18 chain. I deliberately did NOT prune interior ancestors of n18 (n5/n12/n13/n14/n16), in case a prune cascades to the best node.

## 14:14 (Claude)
- Battery 80%, discharging; told the user to plug in NOW. Disk 3.6 GB, swap 5.0 GB. Alive, no errors. The 10 prunes from 13:59 were applied (20 applied total).
- New best: n38 val 0.7033 (n13 -> n30 activity-density feats 0.688 -> n37 word trigrams 0.702 -> n38 separate title TF-IDF 0.703). n32 and n37 are the same change on the same parent (identical val).
- Claude interventions: pruned n31, n33, n35, n36, n34, n39, n40 (regressions vs parent) and n32 (duplicate of n37). Kept n30/n37/n38 (best chain) and n18 (0.6965, second line).

## 14:29 (Claude)
- AC power, 78% and charging (the user plugged in). Disk 3.2 GB, swap 4.9 GB. Dashboard started at the user's request (localhost:8501). Alive, no errors; 28 interventions applied so far.
- New best: n50 val 0.7133 (n37 -> n48 title TF-IDF 0.703 -> n49 lower LR/more trees 0.707 -> n50 NMF topics 0.713). n38, n42 and n48 are the same change on n37 (identical val).
- Claude interventions: pruned n38 and n42 (duplicates of n48), n41/n44/n46/n47 (regressions), n45 (no effect), and the RF family n2/n8/n43 (0.04 behind). Kept: the n50 line, and n18 (0.6965) as a second line.
- Note: the code of n42 and n48 differs textually from n38 (rewritten), but all three have val 0.7032736316800983 to the last digit, so their predictions are effectively identical. That's the basis for calling them duplicates.

## 14:44 (Claude)
- AC power, 81%. Disk 2.8 GB (falling about 0.4 GB per 15 min since the dashboard started), swap 5.4 GB. Alive, no errors; 38 applied.
- Best is still n50 (0.7133). n57 (n48 + subreddit TF-IDF view) 0.7113 is a good second line; kept.
- Claude interventions: pruned n51, n52, n53, n54, n55, n56, n58, n59 (each below its parent).

## 14:59 (Claude)
- AC power, 86%. Disk 2.8 GB (stable), swap 5.2 GB. Alive, no errors; 46 applied.
- Best is still n50 (0.7133). n64 (n37 + NMF) 0.706 -> n65 (lower LR, more trees) 0.711 rebuilds n50's recipe on another path; kept as a near-best line, along with n57 (0.711).
- Claude interventions: pruned n60 (no effect), n61, n62, n66 (regressions), and n63 (regression; it also fits its vectorizers on predict.csv text, i.e. held-out rows, though without labels).

## 15:14 (Claude)
- AC power, 91%. Disk 2.8 GB, swap 5.2 GB, both stable. Alive, no errors; 51 applied.
- New best: n69 val 0.71348 (n64 -> n65 -> n69 concreteness/verifiability text cues), just above n50 0.71332. The two lines (n50 via n48/n49 and n69 via n64/n65) have converged on similar recipes.
- Claude interventions: pruned n67, n68, n70, n71, n72 (each below its parent). I did not prune n12, an ancestor of both best lines.

## 15:29 (Claude)
- On battery again, 95% (the charger was unplugged), disk 2.7 GB, swap 5.4 GB. Alive, no errors; 56 applied.
- Best is still n69 (0.7135). No new node beat its parent.
- Claude interventions: pruned n73, n74, n75, n77, n78 (regressions) and n76 (duplicate of n65, identical val). n64 is an ancestor of the best (n65 -> n69), so I didn't prune it.

## 15:44 (Claude)
- Battery 95%, discharging. Disk 2.4 GB, swap 5.1 GB. Alive, no errors; 62 applied.
- n79 showed as already `pruned`: pruning n76 at 15:29 cascaded to its child. This confirms that a prune removes the whole subtree, so keeping ancestors of the best was right.
- Best is still n69 (0.7135). The agent re-created n65's change on n64 a third time (n80).
- Claude interventions: pruned n80 (duplicate) plus n81 (no effect), n82, n83, n84 (regressions). Kept n85 (n37 + specificity cues, 0.706; improves on its parent).

## 15:59 (Claude)
- Battery 95%. Disk 2.7 GB, swap 5.6 GB. Alive, no errors; 67 applied.
- Best is still n69 (0.7135). New near-best line: n37 -> n90 (specificity cues) 0.708 -> n91 (extra title/subreddit decomposition views) 0.7129; kept.
- Claude interventions: pruned n85 (near-duplicate of n90, weaker) with n87/n88/n89 under it, n86 and n92 (regressions).

## 16:14 (Claude)
- Battery 93%. Disk 2.7 GB, swap 5.7 GB. Alive, no errors; 73 applied.
- Best is still n69 (0.7135). Close behind: n96 0.7131 (n90 -> n95 title view 0.7124 -> n96 HGB stage change), n91 0.7129. n99 (reciprocity cues) 0.710 improves on its parent n90; kept.
- Claude interventions: pruned n93, n94, n97, n98 (each below its parent).

## 16:29 (Claude)
- Battery 92%. Disk 2.6 GB, swap 5.5 GB. Alive, no errors; 77 applied.
- New best: n101 val 0.7153 (n37 -> n90 specificity 0.708 -> n99 reciprocity 0.710 -> n101 location-specificity 0.7153). n99, which I kept at 16:14 although it was below the best, is the parent of the new best.
- Claude interventions: pruned n100, n102, n103, n104, n105, n106 (each below its parent).

## 16:44 (Claude)
- Battery 90%. Disk 2.5 GB, swap 5.3 GB. Alive, no errors; 83 applied.
- Best is still n101 (0.7153). n90 -> n110 (reciprocity, a near-repeat of n99) 0.711 -> n111 (skill-offer/barter cues) 0.7137 is improving; kept.
- Claude interventions: pruned n107, n108, n109, n112, n113 (each below its parent).

## 16:59 (Claude), last check before the budget ends (~6 min left)
- Battery 89%. Disk 2.5 GB, swap 5.6 GB. Alive, no errors; 88 applied.
- Best is still n101 (0.7153). No new node beat it.
- Claude interventions: pruned n114, n116, n117, n118, n119 (regressions) and n122 (duplicate of n120). Left n115 (a slight gain on n37) and n120 -> n121 (0.712) alone.

## End of run, 17:04 (budget), and grading (Claude)
- Done: 143 steps, 126 nodes (28 working, 96 pruned, 2 buggy), 141 LLM calls, $0.35, 0 failed calls, 1 timeout. Final pick by best_val: n101 (val 0.7153, probe 0.6858).
- Graded by MLE-bench: test **0.66711**, valid, above median (0.5996), no medal (bronze 0.6921).
- 94 prunes queued by Claude, 79 applied, 15 dropped (already pruned by a cascade).
- In hindsight, on test (Claude did not look at test scores during the run): the pick ranks 94th of 123 scored nodes. The best node on test, n15 (0.6923, just above bronze), was one Claude pruned at 13:44 as a "regression" (val 0.676 < parent 0.685). 69 of the 93 nodes that beat the pick on test were pruned. The rule "prune any child below its parent on validation" was too strict for pizza: its validation split has only 576 rows, so differences of 0.01-0.02 AUC are noise. Seed 102 used a noise cutoff; this run did not.
- C4 rule replayed: fires once (after n30: prune n13's subtree, validation +1.0% while probe -2.7%). Its pick would have been n12, test 0.6795 (+0.012).
