"""Deterministic trusted baselines and offline mock-generated examples."""


def reference_code(task_type: str, algorithm: str = "logistic", variant: str = "default") -> str:
    if variant not in {"default", "balanced", "regularized", "shallower"}:
        raise ValueError(f"Unknown reference variant: {variant}")
    algorithm = {"random_forest": "forest", "naive_bayes": "nb"}.get(algorithm, algorithm)
    if algorithm == "logistic":
        model_import = "from sklearn.linear_model import LogisticRegression"
        model = "LogisticRegression(max_iter=1000, random_state=task_spec['seed']"
        if variant == "balanced":
            model += ", class_weight='balanced')"
        elif variant == "regularized":
            model += ", C=0.25)"
        elif variant == "shallower":
            raise ValueError("shallower variant requires a tree estimator")
        else:
            model += ")"
    elif algorithm == "forest":
        model_import = "from sklearn.ensemble import RandomForestClassifier"
        model = (
            "RandomForestClassifier(n_estimators=100, max_depth=12, "
            "min_samples_leaf=5, n_jobs=2, random_state=task_spec['seed'])"
        )
    elif algorithm == "extra_trees":
        model_import = "from sklearn.ensemble import ExtraTreesClassifier"
        model = (
            "ExtraTreesClassifier(n_estimators=100, max_depth=12, "
            "min_samples_leaf=5, n_jobs=2, random_state=task_spec['seed'])"
        )
    elif algorithm == "nb":
        model_import = "from sklearn.naive_bayes import ComplementNB"
        model = "ComplementNB(alpha=0.5)"
    elif algorithm == "dummy":
        model_import = "from sklearn.dummy import DummyClassifier"
        model = "DummyClassifier(strategy='prior')"
    else:
        raise ValueError(f"Unknown reference algorithm: {algorithm}")
    if algorithm in {"forest", "extra_trees"}:
        if variant == "shallower":
            model = model.replace("max_depth=12", "max_depth=6")
        elif variant == "balanced":
            model = model[:-1] + ", class_weight='balanced')"
        elif variant == "regularized":
            model = model.replace("min_samples_leaf=5", "min_samples_leaf=12")
    elif algorithm == "nb" and variant == "regularized":
        model = "ComplementNB(alpha=2.0)"
    elif algorithm in {"nb", "dummy"} and variant != "default":
        raise ValueError(f"Variant {variant} does not apply to {algorithm}")
    if task_type in {"text_binary_classification", "text_classification", "sms"}:
        return f"""from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
{model_import}

def build_pipeline(task_spec):
    return Pipeline([
        ('text', TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=30000)),
        ('model', {model}),
    ])
"""
    if algorithm == "nb":
        raise ValueError("ComplementNB is only supplied as a text reference baseline")
    return f"""from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
{model_import}

def build_pipeline(task_spec):
    numeric = Pipeline([
        ('impute', SimpleImputer(strategy='median')),
        ('scale', StandardScaler()),
    ])
    prepare = ColumnTransformer([
        ('numeric', numeric, task_spec['numeric_features']),
        ('categorical', OneHotEncoder(handle_unknown='ignore'), task_spec['categorical_features']),
    ])
    return Pipeline([('prepare', prepare), ('model', {model})])
"""
