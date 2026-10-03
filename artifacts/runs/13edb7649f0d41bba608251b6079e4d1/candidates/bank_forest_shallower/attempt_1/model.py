from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier

def build_pipeline(task_spec):
    numeric = Pipeline([
        ('impute', SimpleImputer(strategy='median')),
        ('scale', StandardScaler()),
    ])
    prepare = ColumnTransformer([
        ('numeric', numeric, task_spec['numeric_features']),
        ('categorical', OneHotEncoder(handle_unknown='ignore', random_state=task_spec['seed']), task_spec['categorical_features']),
    ])
    model = RandomForestClassifier(n_estimators=150, max_depth=10, min_samples_leaf=5, n_jobs=1, random_state=task_spec['seed'])
    return Pipeline([('prepare', prepare), ('model', model)])
