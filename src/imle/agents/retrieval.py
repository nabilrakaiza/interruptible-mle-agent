"""A2: retrieval agent.

On draft operations, returns model cards in a fixed schema from allowlisted
sources. Never returns free text, and never retrieves competition solutions,
notebooks, or leaderboard discussion.

Scope cut (docs/plan.md): web retrieval is replaced by a few hand-written cards
per modality, in the same fixed schema. They describe general model families
and contain nothing specific to any competition. Every card only uses packages
the sandbox has (see PACKAGES in agents/coding.py).
"""

from __future__ import annotations

# Card schema: name, modality, use_when, recipe, watch_out.
CARDS: list[dict[str, str]] = [
    {
        "name": "TF-IDF + logistic regression",
        "modality": "text",
        "use_when": "Classification of short or medium texts; a strong first baseline with good probabilities.",
        "recipe": "TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2) then "
                  "LogisticRegression(C between 1 and 10, max_iter=2000). Tune C on a held-out part of train.",
        "watch_out": "Fit the vectorizer on training rows only. For log loss, keep the predicted probabilities "
                     "rather than hard labels.",
    },
    {
        "name": "Character n-gram TF-IDF + linear model",
        "modality": "text",
        "use_when": "Style, spelling or wording matters (authorship, insults, slang).",
        "recipe": "TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 5), max_features=200000), optionally "
                  "stacked with word features via scipy.sparse.hstack, then LogisticRegression.",
        "watch_out": "Memory grows quickly with n-gram range; cap max_features.",
    },
    {
        "name": "Naive Bayes on counts",
        "modality": "text",
        "use_when": "Very fast baseline, or a second model to blend with a linear model.",
        "recipe": "CountVectorizer or TfidfVectorizer, then MultinomialNB or ComplementNB (alpha around 0.1 to 1).",
        "watch_out": "Probabilities are overconfident; for log loss, calibrate (CalibratedClassifierCV) "
                     "or average with logistic regression.",
    },
    {
        "name": "Histogram gradient boosting",
        "modality": "tabular",
        "use_when": "Most tabular problems, mixed numeric and categorical columns, missing values.",
        "recipe": "HistGradientBoostingClassifier or HistGradientBoostingRegressor with early_stopping=True; "
                  "tune learning_rate (0.03 to 0.1), max_leaf_nodes (15 to 63), l2_regularization.",
        "watch_out": "Pass categorical columns through categorical_features or encode them as integers first.",
    },
    {
        "name": "Random forest / extra trees",
        "modality": "tabular",
        "use_when": "A robust baseline that needs little tuning, or a model to average with boosting.",
        "recipe": "RandomForest or ExtraTrees with n_estimators 300 to 500, min_samples_leaf 1 to 5, n_jobs=2.",
        "watch_out": "Slow and memory-hungry on very wide data; use the CPU limit of 2 cores.",
    },
    {
        "name": "Regularised linear model with preprocessing",
        "modality": "tabular",
        "use_when": "Few rows, mostly linear signal, or as a sanity baseline.",
        "recipe": "ColumnTransformer(StandardScaler on numeric, OneHotEncoder(handle_unknown='ignore') on "
                  "categorical) then Ridge or LogisticRegression.",
        "watch_out": "For skewed regression targets or RMSLE-type metrics, fit on log1p(target) and invert.",
    },
    {
        "name": "Pixel features + PCA + linear model",
        "modality": "image",
        "use_when": "Small images (for example 32x32) on CPU only.",
        "recipe": "Load with PIL or numpy, flatten, scale to [0, 1], PCA(50 to 150 components), then "
                  "LogisticRegression or an SVC trained on a subsample.",
        "watch_out": "Loading thousands of files is slow; read each image once and cache the array in OUTPUT_DIR.",
    },
    {
        "name": "Handcrafted image features + gradient boosting",
        "modality": "image",
        "use_when": "Colour or texture separates the classes.",
        "recipe": "Per-channel mean, std and histogram, plus edge statistics from np.gradient, then "
                  "HistGradientBoostingClassifier.",
        "watch_out": "Compute features identically for train and predict rows.",
    },
    {
        "name": "Small multilayer perceptron on pixels",
        "modality": "image",
        "use_when": "Pixel models plateau and there is time left in the script budget.",
        "recipe": "MLPClassifier(hidden_layer_sizes=(256, 64), early_stopping=True) on scaled, possibly "
                  "downsampled pixels.",
        "watch_out": "CPU only: keep layers small and cap max_iter so the script finishes well inside the timeout.",
    },
    {
        "name": "Linear and nearest-neighbour models on precomputed features",
        "modality": "image_features",
        "use_when": "The data already has numeric shape, margin or texture features per image.",
        "recipe": "StandardScaler then LogisticRegression (multinomial, C tuned) or "
                  "LinearDiscriminantAnalysis; KNeighborsClassifier as a second model.",
        "watch_out": "Many classes with few rows each: use stratified folds and strong regularisation.",
    },
]

# Modalities per task, from docs/experiments.md.
TASK_MODALITIES: dict[str, list[str]] = {
    "spooky-author-identification": ["text"],
    "detecting-insults-in-social-commentary": ["text"],
    "random-acts-of-pizza": ["text", "tabular"],
    "nomad2018-predict-transparent-conductors": ["tabular"],
    "aerial-cactus-identification": ["image"],
    "leaf-classification": ["image_features", "tabular"],
}


def cards_for(task: str) -> list[dict[str, str]]:
    """The model cards for a task's modalities. Unknown tasks get none."""
    modalities = TASK_MODALITIES.get(task, [])
    return [card for card in CARDS if card["modality"] in modalities]
