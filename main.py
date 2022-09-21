# impelemnt various examples for testing purposes

import pandas as pd
import numpy as np
from optuna.pruners import HyperbandPruner
from optuna.samplers._tpe.sampler import TPESampler
from sklearn.model_selection import KFold, train_test_split
from lohrasb.best_estimator import BaseModel
import optuna
from sklearn.metrics import f1_score, mean_absolute_error
from lohrasb.project_conf import ROOT_PROJECT
from sklearn.linear_model import *
from sklearn.svm import *
from xgboost import *
from sklearn.linear_model import *
from catboost import *
from lightgbm import *
from sklearn.neural_network import *
from imblearn.ensemble import *
from sklearn.ensemble import *

# prepare data for tests
try:
    print(ROOT_PROJECT / "lohrasb" / "data" / "data.csv")
    data = pd.read_csv(ROOT_PROJECT / "lohrasb" / "data" / "data.csv")
except Exception as e:
    print(ROOT_PROJECT / "lohrasb" / "data" / "data.csv")
    print(e)

print(data.columns.to_list())
X = data.loc[:, data.columns != "default payment next month"]
y = data.loc[:, data.columns == "default payment next month"]

X = X.select_dtypes(include=np.number)

print(data.columns.to_list())

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.33, random_state=0
)

# functions for classifications
def run_classifiers(obj, X_train, y_train, X_test, y_test):
    obj.fit(X_train, y_train)
    y_preds = obj.predict(X_test)
    pred_labels = np.rint(y_preds)
    print("model output : ")
    print(pred_labels)
    print("f1 score for classification :")
    print(f1_score(y_test, pred_labels))


# functions for regressions
def run_regressors(obj, X_train, y_train, X_test, y_test):
    obj.fit(X_train, y_train)
    y_preds = obj.predict(X_test)
    print("model output : ")
    print(y_preds)
    print("mean absolute error score for regression :")
    print(mean_absolute_error(y_test, y_preds))


models_classifiers = {
    "XGBClassifier": {
        "eval_metric": ["auc"],
        "max_depth": [4, 5],
    },
    "LGBMClassifier": {"max_depth": [1, 12]},
    "CatBoostClassifier": {
        "depth": [5, 6],
        "boosting_type": ["Ordered"],
        "bootstrap_type": ["Bayesian"],
        "logging_level": ["Silent"],
    },
    "SVC": {
        "C": [0.5, 1],
        "kernel": ["poly"],
    },
    "MLPClassifier": {
        "activation": ["identity"],
        "alpha": [0.0001, 0.001],
    },
    "BalancedRandomForestClassifier": {
        "n_estimators": [100, 200],
        "min_impurity_decrease": [0.0, 0.1],
    },
}


models_regressors = {
    "XGBRegressor": {
        "max_depth": [4, 5],
        "min_child_weight": [0.1, 0.9],
        "gamma": [1, 9],
    },
    "LogisticRegression": {
        "C": [0.5, 1],
        "fit_intercept": [True, False],
    },
    "RandomForestRegressor": {
        "max_depth": [4, 5],
    },
    "MLPRegressor": {
        "activation": ["logistic"],
        "solver": ["lbfgs", "sgd", "adam"],
        "alpha": [0.0001],
    },
}

# check grid search on selected classification models
def run_gird_classifiers(pause_iteration=True):
    for model in models_classifiers:
        obj = BaseModel.bestmodel_factory.using_gridsearch(
            estimator=eval(model + "()"),
            estimator_params=models_classifiers[model],
            measure_of_accuracy="f1",
            verbose=3,
            n_jobs=-1,
            random_state=42,
            cv=KFold(2),
        )
        # run classifiers
        run_classifiers(obj, X_train, y_train, X_test, y_test)
        if pause_iteration:
            val = input(f"Enter confirmation of results for the model {model} Y/N: ")
            if val == "N":
                break


# check grid search on selected regression models
def run_gird_regressoros(pause_iteration=True):
    for model in models_regressors:
        obj = BaseModel.bestmodel_factory.using_gridsearch(
            estimator=eval(model + "()"),
            estimator_params=models_regressors[model],
            measure_of_accuracy="mean_absolute_error",
            verbose=3,
            n_jobs=-1,
            random_state=42,
            cv=KFold(2),
        )
        # run classifiers
        run_regressors(obj, X_train, y_train, X_test, y_test)
        if pause_iteration:
            val = input(f"Enter confirmation of results for the model {model} Y/N: ")
            if val == "N":
                break


# check randomized search on selected classification models
def run_random_classifiers(pause_iteration=True):
    for model in models_classifiers:
        obj = BaseModel.bestmodel_factory.using_randomsearch(
            estimator=eval(model + "()"),
            estimator_params=models_classifiers[model],
            measure_of_accuracy="f1",
            verbose=3,
            n_jobs=-1,
            random_state=42,
            cv=KFold(2),
            n_iter=50,
        )
        # run classifiers
        run_classifiers(obj, X_train, y_train, X_test, y_test)
        if pause_iteration:
            val = input(f"Enter confirmation of results for the model {model} Y/N: ")
            if val == "N":
                break


# check randomized search on selected regression models
def run_random_regressoros(pause_iteration=True):
    for model in models_regressors:
        obj = BaseModel.bestmodel_factory.using_randomsearch(
            estimator=eval(model + "()"),
            estimator_params=models_regressors[model],
            measure_of_accuracy="mean_absolute_error",
            verbose=3,
            n_jobs=-1,
            random_state=42,
            cv=KFold(2),
            n_iter=50,
        )
        # run classifiers
        run_regressors(obj, X_train, y_train, X_test, y_test)
        if pause_iteration:
            val = input(f"Enter confirmation of results for the model {model} Y/N: ")
            if val == "N":
                break


# check optuna search on selected classification models
def run_optuna_classifiers(pause_iteration=True):
    for model in models_classifiers:
        obj = BaseModel.bestmodel_factory.using_optuna(
            estimator=eval(model + "()"),
            estimator_params=models_classifiers[model],
            measure_of_accuracy="f1",
            verbose=3,
            n_jobs=-1,
            random_state=42,
            # optuna params
            # optuna study init params
            study=optuna.create_study(
                storage=None,
                sampler=TPESampler(),
                pruner=HyperbandPruner(),
                study_name=None,
                direction="maximize",
                load_if_exists=False,
                directions=None,
            ),
            # optuna optimization params
            study_optimize_objective=None,
            study_optimize_objective_n_trials=10,
            study_optimize_objective_timeout=600,
            study_optimize_n_jobs=-1,
            study_optimize_catch=(),
            study_optimize_callbacks=None,
            study_optimize_gc_after_trial=False,
            study_optimize_show_progress_bar=False,
        )
        # run classifiers
        run_classifiers(obj, X_train, y_train, X_test, y_test)
        if pause_iteration:
            val = input(f"Enter confirmation of results for the model {model} Y/N: ")
            if val == "N":
                break


# check optuna search on selected regression models
def run_optuna_regressors(pause_iteration=True):
    for model in models_regressors:
        obj = BaseModel.bestmodel_factory.using_optuna(
            estimator=eval(model + "()"),
            estimator_params=models_regressors[model],
            measure_of_accuracy="mean_absolute_error",
            verbose=3,
            n_jobs=-1,
            random_state=42,
            # optuna params
            # optuna study init params
            study=optuna.create_study(
                storage=None,
                sampler=TPESampler(),
                pruner=HyperbandPruner(),
                study_name=None,
                direction="minimize",
                load_if_exists=False,
                directions=None,
            ),
            # optuna optimization params
            study_optimize_objective=None,
            study_optimize_objective_n_trials=10,
            study_optimize_objective_timeout=600,
            study_optimize_n_jobs=-1,
            study_optimize_catch=(),
            study_optimize_callbacks=None,
            study_optimize_gc_after_trial=False,
            study_optimize_show_progress_bar=False,
        )
        # run classifiers
        run_regressors(obj, X_train, y_train, X_test, y_test)
        if pause_iteration:
            val = input(f"Enter confirmation of results for the model {model} Y/N: ")
            if val == "N":
                break


if __name__ == "__main__":
    # run_gird_classifiers(pause_iteration=True) # OK
    # run_gird_regressoros(pause_iteration=True) # OK
    # run_random_classifiers(pause_iteration=True) # OK
    # run_random_regressoros(pause_iteration=True) # OK
    # run_optuna_classifiers(pause_iteration=True) # OK
    run_optuna_regressors(pause_iteration=True)  # OK
