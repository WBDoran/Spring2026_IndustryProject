"""
Generates HMM_LightGBM_Validation.ipynb

Validates the NVIDIA HMM Journey Analysis v2 outputs using LightGBM across three tasks:
  Task 1 - Multiclass: predict HMM latest state (8 classes) from developer profile
           features. Near-perfect accuracy validates states are feature-driven, not
           algorithmic artifacts.
  Task 2 - Binary: predict each of the three business signal flags from developer profile
           features (early_warning_active, recovery_candidate, dormant_reactivation).
  Task 3 - Incremental HMM value: predict HDBSCAN lifecycle stratum with profile features
           only vs. profile + HMM state features. The AUC/F1 delta measures how much
           sequential information HMM adds over the static profile snapshot.
"""
import json, uuid

def _id():
    return str(uuid.uuid4())[:8]

def md(text):
    lines = text.split("\n")
    src = [l + "\n" for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    return {"cell_type": "markdown", "id": _id(), "metadata": {}, "source": src}

def code(text):
    lines = text.split("\n")
    src = [l + "\n" for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": _id(),
        "metadata": {},
        "outputs": [],
        "source": src,
    }

cells = []

# ── Title ────────────────────────────────────────────────────────────────────
cells.append(md("""\
# HMM Journey Analysis v2 - LightGBM Validation

Validates the HMM outputs from `NVIDIA_HMM_Journey_Analysis_v2.ipynb` using LightGBM.

| Task | Target | Purpose |
|------|--------|---------|
| 1 | `hmm_hidden_state` (8-class) | Confirm HMM states are feature-driven, not algorithmic artifacts |
| 2 | Business signal flags (3 binary) | Confirm early-warning, recovery, and reactivation flags are detectable from profile |
| 3 | HDBSCAN `stratum` (4-class) | Measure incremental predictive value of HMM state over static profile alone |

**Source tables required:**
- `dev_hmm_business_signals_v2` (150K rows, from HMM v2 notebook)
- `dev_profile_final_v4` (feature source, from FeatureEngineering_v3)
- `dev_hmm_state_labels_v2` (HMM state label mapping)"""))

# ── 0  Setup ─────────────────────────────────────────────────────────────────
cells.append(md("## 0. Setup"))
cells.append(code("""\
import warnings
warnings.filterwarnings("ignore")

import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path

pd.set_option("display.max_columns", 60)
pd.set_option("display.float_format", "{:.4f}".format)

DB_PATH      = "developer_project.duckdb"
RANDOM_STATE = 42
NVIDIA_GREEN = "#76B900"
np.random.seed(RANDOM_STATE)

SIGNALS_TABLE  = "dev_hmm_business_signals_v2"
PROFILE_TABLE  = "dev_profile_final_v4"
LABELS_TABLE   = "dev_hmm_state_labels_v2"

con = duckdb.connect(DB_PATH, read_only=True)

existing = set(con.execute("SHOW TABLES").df().iloc[:, 0].astype(str))
missing  = [t for t in [SIGNALS_TABLE, PROFILE_TABLE, LABELS_TABLE] if t not in existing]
if missing:
    raise RuntimeError(f"Missing required tables: {missing}. Run HMM v2 and FeatureEngineering_v3 first.")

for t in [SIGNALS_TABLE, PROFILE_TABLE, LABELS_TABLE]:
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"{t}: {n:,} rows")"""))

# ── 1  Load data ──────────────────────────────────────────────────────────────
cells.append(md("""\
## 1. Load and join HMM signals with developer profile features

Profile features are a union of the stratum-specific feature lists used in the V11
supervised cluster labeling, covering recency windows, effort, build signals, velocity,
and lifetime depth."""))

cells.append(code("""\
PROFILE_FEATURES = [
    # Recency windows
    "log_activity_count_0_30d",
    "log_activity_count_30_90d",
    "log_activity_count_90_180d",
    "unique_activity_types_0_30d",
    "unique_modalities_0_30d",
    # Effort
    "developer_effort_score",
    "weighted_recent_confidence_effort",
    "high_effort_share_lifetime",
    # Build signals
    "recent_build_flag",
    "log_build_count_0_30d",
    "log_build_count_30_90d",
    "log_build_count_90_180d",
    "build_share_lifetime",
    # Velocity & recency flags
    "activity_velocity_0_30_vs_30_90",
    "has_activity_0_30d",
    "has_activity_30_90d",
    "has_activity_90_180d",
    "avg_effort_rank_0_30d",
    "avg_effort_rank_30_90d",
    "avg_effort_rank_90_180d",
    # Lifetime depth
    "log_clipped_lifetime_activity_count_p99",
    "persona_entropy",
]

profile_cols = con.execute(f"DESCRIBE {PROFILE_TABLE}").df()["column_name"].tolist()
PROFILE_FEATURES = [f for f in PROFILE_FEATURES if f in profile_cols]
print(f"Profile features available: {len(PROFILE_FEATURES)}")

feat_select = ", ".join([f"p.{f}" for f in PROFILE_FEATURES])
df = con.execute(f'''
    SELECT
        s.developer_id,
        s.hmm_hidden_state,
        s.hmm_state_label,
        s.hmm_state_probability,
        s.stratum,
        s.cluster_key,
        s.adoption_direction,
        s.early_warning_active_flag,
        s.recovery_candidate_flag,
        s.dormant_reactivation_signal_flag,
        {feat_select}
    FROM {SIGNALS_TABLE} s
    JOIN {PROFILE_TABLE} p USING (developer_id)
''').df()

df.replace([np.inf, -np.inf], np.nan, inplace=True)
print(f"Joined dataset: {len(df):,} rows  |  {df.shape[1]} columns")
print("\\nHMM state distribution:")
display(df["hmm_state_label"].value_counts().reset_index(name="n"))
print("\\nStratum distribution:")
display(df["stratum"].value_counts().reset_index(name="n"))"""))

# ── 2  Preprocessing helpers ──────────────────────────────────────────────────
cells.append(md("## 2. Preprocessing & shared utilities"))
cells.append(code("""\
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, f1_score,
    roc_auc_score, average_precision_score, brier_score_loss,
    confusion_matrix, classification_report,
)
try:
    import lightgbm as lgb
except ImportError:
    raise ImportError("pip install lightgbm")

def make_lgbm_multiclass(n_classes):
    return lgb.LGBMClassifier(
        objective="multiclass",
        num_class=n_classes,
        n_estimators=400,
        learning_rate=0.05,
        max_depth=-1,
        num_leaves=63,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=1.0,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1,
    )

def make_lgbm_binary(pos_weight):
    return lgb.LGBMClassifier(
        objective="binary",
        scale_pos_weight=pos_weight,
        n_estimators=400,
        learning_rate=0.05,
        max_depth=-1,
        num_leaves=63,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_lambda=1.0,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1,
    )

imputer = SimpleImputer(strategy="median")

# Clip each feature at 99th percentile
X_raw = df[PROFILE_FEATURES].copy()
for col in X_raw.columns:
    p99 = X_raw[col].quantile(0.99)
    if pd.notna(p99):
        X_raw[col] = X_raw[col].clip(upper=p99)

X_profile = pd.DataFrame(
    imputer.fit_transform(X_raw),
    columns=PROFILE_FEATURES,
    index=df.index,
)

print(f"Feature matrix shape: {X_profile.shape}")"""))

# ── 3  Task 1 - HMM state prediction ─────────────────────────────────────────
cells.append(md("""\
## 3. Task 1 - Predict HMM latest state from developer profile features

**Purpose:** If a small set of static profile features can reproduce the HMM state
assignments at high accuracy, it confirms the states encode real behavioral structure
rather than artifacts of the HMM algorithm.

8 classes: Idle, Low Recent Activity, Light At-Risk, Cooling, Active Exploration,
Build-Oriented, Prior Active, Irregular."""))

cells.append(code("""\
le_hmm = LabelEncoder()
y_hmm  = le_hmm.fit_transform(df["hmm_hidden_state"].astype(int))
n_hmm_classes = len(le_hmm.classes_)

X_tr, X_te, y_tr, y_te = train_test_split(
    X_profile, y_hmm, test_size=0.20,
    random_state=RANDOM_STATE, stratify=y_hmm,
)
X_tr2, X_val, y_tr2, y_val = train_test_split(
    X_tr, y_tr, test_size=0.15 / 0.80,
    random_state=RANDOM_STATE, stratify=y_tr,
)

model_hmm = make_lgbm_multiclass(n_hmm_classes)
model_hmm.fit(
    X_tr2, y_tr2,
    eval_set=[(X_val, y_val)],
    callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
)

pred_hmm = model_hmm.predict(X_te)
acc      = accuracy_score(y_te, pred_hmm)
bal_acc  = balanced_accuracy_score(y_te, pred_hmm)
macro_f1 = f1_score(y_te, pred_hmm, average="macro")

print("Task 1 - HMM state prediction from profile features")
print("=" * 55)
print(f"  Accuracy:          {acc:.4f}")
print(f"  Balanced accuracy: {bal_acc:.4f}")
print(f"  Macro F1:          {macro_f1:.4f}")
print(f"  Classes:           {list(le_hmm.classes_)}")
print()
print(classification_report(
    y_te, pred_hmm,
    target_names=[str(c) for c in le_hmm.classes_],
))"""))

cells.append(code("""\
# Confusion matrix
cm = confusion_matrix(y_te, pred_hmm)
state_labels = con.execute(f"SELECT hmm_hidden_state, hmm_state_label FROM {LABELS_TABLE} ORDER BY hmm_hidden_state").df()
tick_labels  = [f"S{s}" for s in le_hmm.classes_]

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(cm, cmap="Greens")
ax.set_xticks(range(n_hmm_classes)); ax.set_xticklabels(tick_labels, rotation=45, ha="right")
ax.set_yticks(range(n_hmm_classes)); ax.set_yticklabels(tick_labels)
ax.set_title("Task 1 - HMM State Confusion Matrix (test set)", fontsize=13, weight="bold")
ax.set_xlabel("Predicted"); ax.set_ylabel("True")
for i in range(n_hmm_classes):
    for j in range(n_hmm_classes):
        ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=8,
                color="white" if cm[i, j] > cm.max() * 0.5 else "black")
fig.colorbar(im, ax=ax)
plt.tight_layout()
plt.show()

print("\\nHMM state legend:")
for _, row in state_labels.iterrows():
    print(f"  S{int(row['hmm_hidden_state'])}: {row['hmm_state_label']}")"""))

# ── 4  Task 2 - Business signal flags ─────────────────────────────────────────
cells.append(md("""\
## 4. Task 2 - Predict business signal flags from developer profile features

Three binary targets derived from the HMM-HDBSCAN alignment:
- `early_warning_active_flag`: active-stratum developers showing a lapsing HMM state
- `recovery_candidate_flag`: at-risk/cooling developers showing build-oriented HMM state
- `dormant_reactivation_signal_flag`: dormant developers showing re-engagement HMM state

High AUC here confirms the flags are grounded in observable behavioral features, making
them actionable for targeting pipelines."""))

cells.append(code("""\
FLAGS = [
    "early_warning_active_flag",
    "recovery_candidate_flag",
    "dormant_reactivation_signal_flag",
]

FLAG_LABELS = {
    "early_warning_active_flag":      "Early Warning (active -> lapsing)",
    "recovery_candidate_flag":         "Recovery Candidate (at-risk/cooling -> build)",
    "dormant_reactivation_signal_flag":"Dormant Reactivation Signal",
}

flag_results = {}
flag_models  = {}

X_tr_f, X_te_f, idx_tr, idx_te = train_test_split(
    X_profile, df.index, test_size=0.20,
    random_state=RANDOM_STATE, stratify=df["hmm_hidden_state"],
)
X_tr_f2, X_val_f, idx_tr2, idx_val_f = train_test_split(
    X_tr_f, idx_tr, test_size=0.15 / 0.80,
    random_state=RANDOM_STATE,
)

print("Task 2 - Business signal flag prediction")
print("=" * 55)
for flag in FLAGS:
    y_f     = df.loc[df.index, flag].astype(int)
    y_tr_f2 = y_f.loc[idx_tr2]
    y_val_f = y_f.loc[idx_val_f]
    y_te_f  = y_f.loc[idx_te]

    pos = y_tr_f2.sum()
    neg = (y_tr_f2 == 0).sum()
    spw = neg / max(pos, 1)

    m = make_lgbm_binary(spw)
    m.fit(
        X_tr_f2, y_tr_f2,
        eval_set=[(X_val_f, y_val_f)],
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
    )
    flag_models[flag] = m

    prob  = m.predict_proba(X_te_f)[:, 1]
    auc   = roc_auc_score(y_te_f, prob)
    prauc = average_precision_score(y_te_f, prob)
    brier = brier_score_loss(y_te_f, prob)
    pos_rate = y_te_f.mean()

    flag_results[flag] = {"auc": auc, "prauc": prauc, "brier": brier,
                          "pos_rate": pos_rate, "prob": prob, "y_true": y_te_f}
    print(f"\\n  {FLAG_LABELS[flag]}")
    print(f"    Positive rate: {pos_rate:.3f}  |  AUC={auc:.4f}  PR-AUC={prauc:.4f}  Brier={brier:.4f}")"""))

cells.append(code("""\
# PR curves for all three flags
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
from sklearn.metrics import precision_recall_curve

for ax, flag in zip(axes, FLAGS):
    res   = flag_results[flag]
    prec, rec, _ = precision_recall_curve(res["y_true"], res["prob"])
    ax.plot(rec, prec, color=NVIDIA_GREEN, lw=1.8)
    ax.axhline(res["pos_rate"], color="gray", ls="--", alpha=0.6,
               label=f"Baseline {res['pos_rate']:.3f}")
    ax.set_title(FLAG_LABELS[flag].replace(" (", "\\n("), fontsize=9, weight="bold")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision" if ax == axes[0] else "")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.text(0.05, 0.05, f"PR-AUC={res['prauc']:.4f}", transform=ax.transAxes, fontsize=9)
    ax.legend(fontsize=8)

plt.suptitle("Task 2 - Precision-Recall Curves: Business Signal Flags", fontsize=13, weight="bold")
plt.tight_layout()
plt.show()"""))

# ── 5  Task 3 - Incremental HMM value ─────────────────────────────────────────
cells.append(md("""\
## 5. Task 3 - Incremental value of HMM state for stratum prediction

Two LightGBM models predict the HDBSCAN lifecycle stratum (active / cooling / at_risk / dormant):
- **Model A**: developer profile features only (static snapshot)
- **Model B**: profile features + `hmm_hidden_state` + `hmm_state_probability` (adds sequential HMM signal)

The F1 delta between Model A and Model B isolates how much information the HMM's temporal
state sequence adds over a static behavioral snapshot."""))

cells.append(code("""\
# Encode stratum
strata_in_data = df["stratum"].dropna().unique().tolist()
le_stratum = LabelEncoder()
y_stratum  = le_stratum.fit_transform(df["stratum"].fillna("unknown"))
n_strata   = len(le_stratum.classes_)

# Augmented feature matrix: profile + HMM state features
hmm_aug = pd.DataFrame({
    "hmm_hidden_state":    df["hmm_hidden_state"].fillna(-1).astype(float),
    "hmm_state_probability": df["hmm_state_probability"].fillna(0).astype(float),
}, index=df.index)
X_augmented = pd.concat([X_profile, hmm_aug], axis=1)

X_tr_s, X_te_s, y_tr_s, y_te_s = train_test_split(
    X_profile, y_stratum, test_size=0.20,
    random_state=RANDOM_STATE, stratify=y_stratum,
)
X_tr_aug, X_te_aug, _, _ = train_test_split(
    X_augmented, y_stratum, test_size=0.20,
    random_state=RANDOM_STATE, stratify=y_stratum,
)
X_val_s,  X_val_aug  = X_tr_s.iloc[:len(X_tr_s)//6], X_tr_aug.iloc[:len(X_tr_aug)//6]
y_val_s               = y_tr_s[:len(y_tr_s)//6]
X_tr_s2, X_tr_aug2   = X_tr_s.iloc[len(X_tr_s)//6:], X_tr_aug.iloc[len(X_tr_aug)//6:]
y_tr_s2               = y_tr_s[len(y_tr_s)//6:]

model_A = make_lgbm_multiclass(n_strata)
model_A.fit(
    X_tr_s2, y_tr_s2,
    eval_set=[(X_val_s, y_val_s)],
    callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
)

model_B = make_lgbm_multiclass(n_strata)
model_B.fit(
    X_tr_aug2, y_tr_s2,
    eval_set=[(X_val_aug, y_val_s)],
    callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
)

pred_A   = model_A.predict(X_te_s)
pred_B   = model_B.predict(X_te_aug)
acc_A    = accuracy_score(y_te_s, pred_A)
acc_B    = accuracy_score(y_te_s, pred_B)
f1_A     = f1_score(y_te_s, pred_A, average="macro")
f1_B     = f1_score(y_te_s, pred_B, average="macro")
bal_A    = balanced_accuracy_score(y_te_s, pred_A)
bal_B    = balanced_accuracy_score(y_te_s, pred_B)

print("Task 3 - Stratum prediction: profile only vs. profile + HMM")
print("=" * 58)
print(f"{'Metric':<22} {'Model A (profile)':<20} {'Model B (+HMM)':<18} {'Delta':>6}")
print("-" * 68)
print(f"{'Accuracy':<22} {acc_A:<20.4f} {acc_B:<18.4f} {acc_B - acc_A:+.4f}")
print(f"{'Balanced accuracy':<22} {bal_A:<20.4f} {bal_B:<18.4f} {bal_B - bal_A:+.4f}")
print(f"{'Macro F1':<22} {f1_A:<20.4f} {f1_B:<18.4f} {f1_B - f1_A:+.4f}")
print()
print("A positive delta confirms HMM state adds predictive signal beyond the static profile.")"""))

cells.append(code("""\
# Per-class F1 comparison
report_A = pd.DataFrame(
    classification_report(y_te_s, pred_A, target_names=le_stratum.classes_, output_dict=True)
).T
report_B = pd.DataFrame(
    classification_report(y_te_s, pred_B, target_names=le_stratum.classes_, output_dict=True)
).T

compare = report_A[["f1-score"]].rename(columns={"f1-score": "F1_profile_only"}).join(
    report_B[["f1-score"]].rename(columns={"f1-score": "F1_profile_plus_HMM"})
)
compare["delta"] = compare["F1_profile_plus_HMM"] - compare["F1_profile_only"]
compare = compare.loc[[c for c in le_stratum.classes_] + ["macro avg", "weighted avg"]]
display(compare.style.format("{:.4f}").bar(subset=["delta"], color=[NVIDIA_GREEN, "#DB4437"],
                                            align="zero"))"""))

# ── 6  Feature importance ──────────────────────────────────────────────────────
cells.append(md("""\
## 6. Feature importance

Gain-based importance for Task 1 (HMM state) and Task 2 (business flags).
Because Task 1 uses only pre-existing static profile features, high-importance
features represent the behavioral dimensions that most distinguish HMM states."""))

cells.append(code("""\
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# Task 1 importance
imp1 = pd.Series(model_hmm.feature_importances_,
                 index=PROFILE_FEATURES).sort_values(ascending=False).head(15)
axes[0].barh(imp1.index[::-1], imp1.values[::-1], color=NVIDIA_GREEN, edgecolor="white")
axes[0].set_title("Task 1 - HMM state prediction\\nTop 15 features (gain)", fontsize=11, weight="bold")
axes[0].set_xlabel("Feature importance (gain)")
axes[0].tick_params(axis="y", labelsize=9)

# Task 2 - average importance across all three flags
avg_imp2 = np.zeros(len(PROFILE_FEATURES))
for m in flag_models.values():
    avg_imp2 += m.feature_importances_
imp2 = pd.Series(avg_imp2 / len(flag_models),
                 index=PROFILE_FEATURES).sort_values(ascending=False).head(15)
axes[1].barh(imp2.index[::-1], imp2.values[::-1], color="#4285F4", edgecolor="white")
axes[1].set_title("Task 2 - Business flags (avg across 3 flags)\\nTop 15 features (gain)", fontsize=11, weight="bold")
axes[1].set_xlabel("Feature importance (gain)")
axes[1].tick_params(axis="y", labelsize=9)

plt.suptitle("LightGBM Feature Importance", fontsize=13, weight="bold")
plt.tight_layout()
plt.show()"""))

cells.append(code("""\
# Task 3: feature importance delta (which features gain most from adding HMM)
imp_A = pd.Series(model_A.feature_importances_, index=PROFILE_FEATURES)
imp_B_cols = list(X_augmented.columns)
imp_B = pd.Series(model_B.feature_importances_, index=imp_B_cols)
hmm_feat_imp = imp_B[["hmm_hidden_state", "hmm_state_probability"]]
print("Task 3 - HMM feature importance in Model B:")
display(hmm_feat_imp.sort_values(ascending=False).to_frame("importance"))

# Bar chart: top 20 features in Model B
top_B = imp_B.sort_values(ascending=False).head(20)
fig, ax = plt.subplots(figsize=(12, 7))
colors = [NVIDIA_GREEN if "hmm" in f else "#4285F4" for f in top_B.index]
ax.barh(top_B.index[::-1], top_B.values[::-1], color=colors[::-1], edgecolor="white")
ax.set_title("Task 3 - Model B (profile + HMM) Top 20 Features", fontsize=12, weight="bold")
ax.set_xlabel("Feature importance (gain)")
ax.tick_params(axis="y", labelsize=9)
lgnd = [mpatches.Patch(color=NVIDIA_GREEN, label="HMM features"),
        mpatches.Patch(color="#4285F4", label="Profile features")]
ax.legend(handles=lgnd, fontsize=9)
plt.tight_layout()
plt.show()"""))

# ── 7  SHAP ───────────────────────────────────────────────────────────────────
cells.append(md("""\
## 7. SHAP analysis

SHAP summary plots for Task 1 (HMM state prediction) and Task 2 (early warning flag).
These show *which feature values* push developers toward specific HMM states or signal flags."""))

cells.append(code("""\
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    print("shap not installed. Install with: pip install shap")

if HAS_SHAP:
    rng    = np.random.default_rng(RANDOM_STATE)
    shap_n = min(3000, len(X_te))
    s_idx  = rng.choice(len(X_te), shap_n, replace=False)
    X_shap = X_te.iloc[s_idx]

    print(f"Task 1 SHAP - HMM state prediction ({shap_n:,} test samples) ...")
    exp1 = shap.TreeExplainer(model_hmm)
    sv1  = exp1.shap_values(X_shap)
    # sv1 is list of arrays for multiclass; take mean absolute across classes
    mean_sv1 = np.mean(np.abs(np.array(sv1)), axis=0) if isinstance(sv1, list) else np.abs(sv1)
    shap.summary_plot(mean_sv1, X_shap, feature_names=PROFILE_FEATURES,
                      max_display=15, show=True, plot_size=(10, 6))"""))

cells.append(code("""\
if HAS_SHAP:
    flag = "early_warning_active_flag"
    X_te_flag = X_te_f.iloc[:shap_n] if len(X_te_f) >= shap_n else X_te_f
    print(f"Task 2 SHAP - {FLAG_LABELS[flag]} ...")
    exp2 = shap.TreeExplainer(flag_models[flag])
    sv2  = exp2.shap_values(X_te_flag)
    sv2_pos = sv2[1] if isinstance(sv2, list) else sv2
    shap.summary_plot(sv2_pos, X_te_flag, feature_names=PROFILE_FEATURES,
                      max_display=15, show=True, plot_size=(10, 6))"""))

# ── 8  Summary table ──────────────────────────────────────────────────────────
cells.append(md("## 8. Validation summary"))
cells.append(code("""\
rows = [
    {
        "Task": "1 - HMM state prediction",
        "Target": "hmm_hidden_state (8-class)",
        "Features": "Profile only",
        "Accuracy": acc,
        "Balanced Acc": bal_acc,
        "Macro F1": macro_f1,
        "Interpretation": "HMM states are feature-driven"
    },
]
for flag in FLAGS:
    rows.append({
        "Task": "2 - Business flags",
        "Target": FLAG_LABELS[flag],
        "Features": "Profile only",
        "AUC": flag_results[flag]["auc"],
        "PR-AUC": flag_results[flag]["prauc"],
        "Brier": flag_results[flag]["brier"],
        "Interpretation": "Flags detectable from static behavior"
    })
rows.append({
    "Task": "3A - Stratum (profile only)",
    "Target": "stratum (4-class)",
    "Features": "Profile only",
    "Accuracy": acc_A,
    "Balanced Acc": bal_A,
    "Macro F1": f1_A,
    "Interpretation": "Static profile baseline"
})
rows.append({
    "Task": "3B - Stratum (+ HMM)",
    "Target": "stratum (4-class)",
    "Features": "Profile + HMM state",
    "Accuracy": acc_B,
    "Balanced Acc": bal_B,
    "Macro F1": f1_B,
    "Interpretation": f"Delta F1 = {f1_B - f1_A:+.4f} (HMM incremental value)"
})

summary_df = pd.DataFrame(rows).fillna("")
display(summary_df)

con.close()
print("\\nValidation complete. Connection closed.")"""))

# ── Write notebook ─────────────────────────────────────────────────────────────
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.10.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = "HMM_LightGBM_Validation.ipynb"
with open(out, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"Written: {out}  ({len(cells)} cells)")
