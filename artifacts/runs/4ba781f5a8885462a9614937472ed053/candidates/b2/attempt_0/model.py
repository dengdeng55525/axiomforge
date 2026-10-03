from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

def build_pipeline(task_spec):
    return Pipeline([
        ('text', TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=30000)),
        ('model', LogisticRegression(max_iter=1000, random_state=task_spec['seed'], class_weight='balanced')),
    ])
