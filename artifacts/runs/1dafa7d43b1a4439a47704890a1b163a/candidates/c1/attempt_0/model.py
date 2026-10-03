from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

def broken_pipeline(task_spec):
    numeric = Pipeline([
        ('impute', SimpleImputer(strategy='median')),
        ('scale', StandardScaler()),
    ])
    prepare = ColumnTransformer([
        ('numeric', numeric, task_spec['numeric_features']),
        ('categorical', OneHotEncoder(handle_unknown='ignore'), task_spec['categorical_features']),
    ])
    return Pipeline([('prepare', prepare), ('model', LogisticRegression(max_iter=1000, random_state=task_spec['seed']))])
