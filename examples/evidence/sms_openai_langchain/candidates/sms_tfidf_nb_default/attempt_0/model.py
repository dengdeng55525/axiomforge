from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import ComplementNB

def build_pipeline(task_spec):
    return Pipeline([
        ('text', TfidfVectorizer(ngram_range=(1, 2), max_features=30000, min_df=2)),
        ('model', ComplementNB(alpha=0.5)),
    ])
