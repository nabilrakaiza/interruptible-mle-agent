import os
OUTPUT_DIR = os.environ["OUTPUT_DIR"]

import os
import re
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss
from scipy.optimize import minimize_scalar

train = pd.read_csv("input/train.csv")
test = pd.read_csv("input/predict.csv")

train["text"] = train["text"].fillna("").astype(str)
test["text"] = test["text"].fillna("").astype(str)

char_vectorizer = TfidfVectorizer(
    analyzer="char_wb",
    ngram_range=(2, 5),
    min_df=3,
    max_df=0.9,
    max_features=400000,
    sublinear_tf=True,
    strip_accents="unicode",
    lowercase=True,
    dtype=np.float32,
)

word_vectorizer = TfidfVectorizer(
    analyzer="word",
    ngram_range=(1, 2),
    min_df=3,
    max_df=0.9,
    max_features=100000,
    sublinear_tf=True,
    strip_accents="unicode",
    lowercase=True,
    dtype=np.float32,
)

case_vectorizer = TfidfVectorizer(
    analyzer="word",
    ngram_range=(1, 2),
    min_df=3,
    max_df=0.9,
    max_features=50000,
    sublinear_tf=True,
    strip_accents=None,
    lowercase=False,
    dtype=np.float32,
)

char_cross_vectorizer = TfidfVectorizer(
    analyzer="char",
    ngram_range=(3, 5),
    min_df=3,
    max_df=0.9,
    max_features=200000,
    sublinear_tf=True,
    strip_accents="unicode",
    lowercase=True,
    dtype=np.float32,
)

content_vectorizer = TfidfVectorizer(
    analyzer="word",
    ngram_range=(1, 2),
    min_df=3,
    max_df=0.9,
    max_features=100000,
    sublinear_tf=True,
    strip_accents="unicode",
    lowercase=True,
    stop_words="english",
    dtype=np.float32,
)

FUNCTION_WORDS = [
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on",
    "at", "by", "for", "with", "from", "as", "was", "were", "be", "been",
    "is", "are", "it", "this", "that", "these", "those", "i", "you", "he",
    "she", "we", "they", "my", "your", "his", "her", "our", "their", "me",
    "him", "us", "them", "not", "no", "so", "if", "then", "than", "too",
    "very", "there", "which", "who", "what", "when", "where", "why", "how",
    "all", "any", "some", "each", "every", "more", "most", "other", "such",
    "only", "into", "upon", "over", "under", "again", "here", "about",
    "between", "through", "during", "before", "after", "since", "until",
    "while", "against", "among", "because", "though", "whether"
]

ARCHAIC_GROUPS = {
    "archaic_pronouns": [
        "thou", "thee", "thy", "thine", "ye", "thyself"
    ],
    "archaic_verbs": [
        "wast", "wert", "hast", "hath", "dost", "doth", "shalt",
        "wilt", "canst", "couldst", "wouldst", "shouldst", "mayst",
        "mightst", "saith", "quoth"
    ],
    "archaic_contractions": [
        "'tis", "'twas", "'twere", "'twill", "'twould",
        "o'er", "ne'er", "'twixt"
    ],
    "archaic_connectives": [
        "ere", "anon", "nigh", "whence", "thence", "whither", "thither",
        "wherefore", "whereof", "wherein", "whereon", "thereupon",
        "hereupon", "albeit", "betwixt", "twixt", "unto", "peradventure",
        "perchance", "perforce", "sooth", "verily", "fain", "oft",
        "oftentimes", "haply", "methinks", "methought", "forsooth",
        "aught", "naught", "nought"
    ],
}

def make_model(seed, alpha=1e-5):
    return SGDClassifier(
        loss="log_loss",
        penalty="l2",
        alpha=alpha,
        max_iter=1000,
        tol=1e-3,
        random_state=seed,
        average=1000,
    )

def build_manual_features(texts):
    char_len = texts.str.len().astype(np.float32).to_numpy()
    word_count = (texts.str.count(" ") + 1).astype(np.float32).to_numpy()
    punct_count = texts.str.count(r"[,.!?;:]").astype(np.float32).to_numpy()
    mean_word_len = (char_len - (word_count - np.float32(1.0))) / np.maximum(
        word_count, np.float32(1.0)
    )
    capitalized = texts.str.count(r"\b[A-Z][a-z]*\b").astype(np.float32).to_numpy()
    all_caps = texts.str.count(r"\b[A-Z]{2,}\b").astype(np.float32).to_numpy()
    quotes = texts.str.count("[\"']").astype(np.float32).to_numpy()
    dashes = texts.str.count(r"-|—|–").astype(np.float32).to_numpy()
    semicolons = texts.str.count(r";").astype(np.float32).to_numpy()
    colons = texts.str.count(r":").astype(np.float32).to_numpy()
    exclamations = texts.str.count(r"!").astype(np.float32).to_numpy()
    questions = texts.str.count(r"\?").astype(np.float32).to_numpy()

    feats = np.log1p(
        np.column_stack([
            char_len,
            word_count,
            punct_count,
            mean_word_len,
            capitalized,
            all_caps,
            quotes,
            dashes,
            semicolons,
            colons,
            exclamations,
            questions,
        ])
    ).astype(np.float32)
    return feats / np.float32(10.0)

def build_function_word_features(texts):
    lower = texts.str.lower()
    cols = []
    for word in FUNCTION_WORDS:
        cols.append(
            lower.str.count(r"\b" + re.escape(word) + r"\b")
            .astype(np.float32)
            .to_numpy()
        )
    arr = np.column_stack(cols)
    arr = np.log1p(arr).astype(np.float32)
    return arr / np.float32(10.0)

def build_archaic_features(texts):
    lower = texts.str.lower()
    cols = []
    for words in ARCHAIC_GROUPS.values():
        total = np.zeros(len(texts), dtype=np.float32)
        for word in words:
            total += lower.str.count(
                r"(?<![A-Za-z])" + re.escape(word) + r"(?![A-Za-z])"
            ).astype(np.float32).to_numpy()
        cols.append(total)
    arr = np.column_stack(cols)
    arr = np.log1p(arr).astype(np.float32)
    return arr / np.float32(10.0)

all_text = pd.concat([train["text"], test["text"]], axis=0)
char_vectorizer.fit(all_text)
word_vectorizer.fit(all_text)
case_vectorizer.fit(all_text)
char_cross_vectorizer.fit(all_text)
content_vectorizer.fit(all_text)

X_char_train = char_vectorizer.transform(train["text"])
X_word_train = word_vectorizer.transform(train["text"])
X_case_train = case_vectorizer.transform(train["text"])
X_char_cross_train = char_cross_vectorizer.transform(train["text"])
X_content_train = content_vectorizer.transform(train["text"])
X_char_test = char_vectorizer.transform(test["text"])
X_word_test = word_vectorizer.transform(test["text"])
X_case_test = case_vectorizer.transform(test["text"])
X_char_cross_test = char_cross_vectorizer.transform(test["text"])
X_content_test = content_vectorizer.transform(test["text"])

train_manual = build_manual_features(train["text"])
test_manual = build_manual_features(test["text"])
train_function = build_function_word_features(train["text"])
test_function = build_function_word_features(test["text"])
train_archaic = build_archaic_features(train["text"])
test_archaic = build_archaic_features(test["text"])

X_train = sp.hstack([
    X_char_train,
    X_word_train,
    X_case_train,
    X_char_cross_train,
    X_content_train,
    sp.csr_matrix(train_manual),
    sp.csr_matrix(train_function),
    sp.csr_matrix(train_archaic),
]).tocsr()

X_test = sp.hstack([
    X_char_test,
    X_word_test,
    X_case_test,
    X_char_cross_test,
    X_content_test,
    sp.csr_matrix(test_manual),
    sp.csr_matrix(test_function),
    sp.csr_matrix(test_archaic),
]).tocsr()

labels = sorted(train["author"].unique())
y = train["author"].values

train_idx, valid_idx = train_test_split(
    np.arange(len(train)),
    test_size=0.1,
    random_state=42,
    stratify=y,
)

X_fit = X_train[train_idx]
X_valid = X_train[valid_idx]

alpha_candidates = [1e-6, 3e-6, 1e-5, 3e-5, 1e-4]
best_alpha = 1e-5
best_score = np.inf
for alpha in alpha_candidates:
    model = make_model(42, alpha)
    model.fit(X_fit, y[train_idx])
    proba = model.predict_proba(X_valid)
    score = log_loss(y[valid_idx], proba, labels=labels)
    if score < best_score:
        best_score = score
        best_alpha = alpha

seeds = (42, 43, 44, 45, 46)

calib_models = [make_model(seed, best_alpha) for seed in seeds]
for model in calib_models:
    model.fit(X_fit, y[train_idx])

calib_proba = np.mean([model.predict_proba(X_valid) for model in calib_models], axis=0)

def scale_proba(proba, temperature):
    eps = 1e-15
    logits = np.log(np.clip(proba, eps, 1.0))
    logits = logits / temperature
    logits = logits - logits.max(axis=1, keepdims=True)
    exp_logits = np.exp(logits)
    probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)
    probs = np.clip(probs, 1e-15, 1 - 1e-15)
    return probs / probs.sum(axis=1, keepdims=True)

def temperature_loss(temperature):
    scaled = scale_proba(calib_proba, temperature)
    return log_loss(y[valid_idx], scaled, labels=labels)

res = minimize_scalar(
    temperature_loss,
    bounds=(0.1, 10.0),
    method="bounded",
    options={"xatol": 1e-4},
)
temperature = res.x

# --- added for the check: a ComplementNB component, blended with the SGD ensemble ---
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import ComplementNB

nb_vectorizer = CountVectorizer(ngram_range=(1, 2), token_pattern=r"(?u)\b\w+\b", min_df=1)
nb_vectorizer.fit(train["text"])
N_train = nb_vectorizer.transform(train["text"])
N_test = nb_vectorizer.transform(test["text"])

sgd_valid = scale_proba(calib_proba, temperature)
best = None
for nb_alpha in [0.03, 0.1, 0.3, 1.0]:
    nb = ComplementNB(alpha=nb_alpha).fit(N_train[train_idx], y[train_idx])
    nb_raw = nb.predict_proba(N_train[valid_idx])
    t_nb = minimize_scalar(lambda t: log_loss(y[valid_idx], scale_proba(nb_raw, t), labels=labels),
                           bounds=(0.05, 20.0), method="bounded").x
    nb_valid = scale_proba(nb_raw, t_nb)
    for w in np.linspace(0, 1, 21):
        blend = np.clip(w * sgd_valid + (1 - w) * nb_valid, 1e-15, 1)
        s = log_loss(y[valid_idx], blend / blend.sum(1, keepdims=True), labels=labels)
        if best is None or s < best[0]:
            best = (s, nb_alpha, t_nb, w)
sgd_only = log_loss(y[valid_idx], sgd_valid, labels=labels)
print(f"internal split: SGD alone {sgd_only:.4f}, blend {best[0]:.4f} (nb_alpha {best[1]}, nb_temperature {best[2]:.3f}, SGD weight {best[3]:.2f})")
_, NB_ALPHA, NB_T, W_SGD = best

final_models = [make_model(seed, best_alpha) for seed in seeds]
for model in final_models:
    model.fit(X_train, train["author"])

proba = np.mean([model.predict_proba(X_test) for model in final_models], axis=0)
proba = scale_proba(proba, temperature)
nb_final = ComplementNB(alpha=NB_ALPHA).fit(N_train, train["author"])
proba = W_SGD * proba + (1 - W_SGD) * scale_proba(nb_final.predict_proba(N_test), NB_T)
proba = np.clip(proba, 1e-15, 1 - 1e-15)
proba = proba / proba.sum(axis=1, keepdims=True)

submission = pd.DataFrame(proba, columns=labels)
submission.insert(0, "id", test["id"].astype(str).values)
submission = submission[["id"] + labels]

os.makedirs(OUTPUT_DIR, exist_ok=True)
submission.to_csv(os.path.join(OUTPUT_DIR, "predictions.csv"), index=False)
