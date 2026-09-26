#!/usr/bin/env bash
# Prepare the six MLE-bench Lite tasks used in this project.
# Requires: mle-bench installed (see its README), Kaggle credentials in ~/.kaggle/kaggle.json
# or KAGGLE_USERNAME / KAGGLE_KEY, and the rules accepted for each competition on Kaggle.
set -euo pipefail

TASKS=(
  spooky-author-identification
  detecting-insults-in-social-commentary
  random-acts-of-pizza
  nomad2018-predict-transparent-conductors
  aerial-cactus-identification
  leaf-classification
)

for t in "${TASKS[@]}"; do
  echo "== preparing $t"
  mlebench prepare -c "$t"
done
