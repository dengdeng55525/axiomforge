from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

def broken_pipeline(task_spec):
    text = TfidfVectorizer(ngram_range=(1, 2), max_features=30000, min_df=2)
    model = LogisticRegression(max_iter=1000, random_state=task_spec['seed'])
    return Pipeline([('text', text), ('model', model)])
