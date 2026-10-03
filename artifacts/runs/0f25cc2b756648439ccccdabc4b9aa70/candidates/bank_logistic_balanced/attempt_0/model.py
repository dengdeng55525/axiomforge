from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression

def build_pipeline(task_spec):
    numeric = Pipeline([
        ('impute', SimpleImputer(strategy='median')),
        ('scale', StandardScaler()),
    ])
    categorical = OneHotEncoder(handle_unknown='ignore')
    prepare = ColumnTransformer([
        ('numeric', numeric, task_spec['numeric_features']),
        ('categorical', categorical, task_spec['categorical_features']),
    ])
    model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=task_spec['seed'])
    return Pipeline([('prepare', prepare), ('model', model)])
