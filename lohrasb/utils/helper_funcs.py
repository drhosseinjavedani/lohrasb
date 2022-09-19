import catboost
import lightgbm
import numpy as np
import optuna
import xgboost
from imblearn.ensemble import BalancedRandomForestClassifier
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    explained_variance_score,
    f1_score,
    make_scorer,
    max_error,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    median_absolute_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split
from sklearn.svm import SVC

maping_mesurements = {
    "accuracy_score": accuracy_score,
    "explained_variance_score": explained_variance_score,
    "f1": f1_score,
    "f1_score": f1_score,
    "mean_absolute_error": mean_absolute_error,
    "mae": mean_absolute_error,
    "mean_absolute_percentage_error": mean_absolute_percentage_error,
    "mape": mean_absolute_percentage_error,
    "mean_squared_error": mean_squared_error,
    "mse": mean_squared_error,
    "median_absolute_error": median_absolute_error,
    "precision_score": precision_score,
    "precision": precision_score,
    "r2": r2_score,
    "r2_score": r2_score,
    "recall_score": recall_score,
    "recall": recall_score,
    "roc_auc_score": roc_auc_score,
    "roc": roc_auc_score,
    "roc_auc": roc_auc_score,
}


def _trail_param_retrive(trial, dict, keyword):
    """An internal function. Return a trial suggest using dict params of estimator and
    one keyword of it. Based on the keyword, it will return an
    Optuna.trial.suggest. The return will be trial.suggest_int(keyword, min(dict[keyword]), max(dict[keyword]))

    Example : _trail_param_retrive(trial, {
            "max_depth": [2, 3],
            "min_child_weight": [0.1, 0.9],
            "gamma": [1, 9],
             }, "gamma") --> will be trail.suggest_int for gamma using [1,9]

    Parameters
    ----------
    trial: Optuna trial
        A trial is a process of evaluating an objective function.
        For more info, visit
        https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html
    dict: dict
        A dictionary of estimator params.
        e.g., {
            "max_depth": [2, 3],
            "min_child_weight": [0.1, 0.9],
            "gamma": [1, 9],
             }
    Keyword: str
        A keyword of estimator key params. e.g., "gamma"
    """
    if isinstance(dict[keyword][0] , str)  or dict[keyword][0] is None:
        return trial.suggest_categorical(keyword, dict[keyword])
    if isinstance(dict[keyword][0] , int):
        if len(dict[keyword]) >=2:
            if isinstance(dict[keyword][1] , int):
                return trial.suggest_int(keyword, min(dict[keyword]), max(dict[keyword]))
        else :
            return trial.suggest_float(keyword, min(dict[keyword]), max(dict[keyword]))
    if isinstance(dict[keyword][0] , float):
        return trial.suggest_float(keyword, min(dict[keyword]), max(dict[keyword]))


def _trail_params_retrive(trial, dict):
    """An internal function. Return a trial suggests using dict params of estimator.
    
    Example : _trail_param_retrive(trial, {
            "eval_metric": ["auc"],
            "max_depth": [2, 3],
            "min_child_weight": [0.1, 0.9],
            "gamma": [1, 9],
            "booster": ["gbtree", "gblinear", "dart"],
             }, "gamma") --> will return params where 
             
             parmas = {
                "eval_metric": trial.suggest_categorical("eval_metric", ["auc"]),
                "max_depth": trial.suggest_int("max_depth", 2,3),
                "min_child_weight": trial.suggest_float("min_child_weight", 0.1, 0.9),
                "booster": trial.suggest_categorical("booster", ["gbtree", "gblinear", "dart"]),
             }
    Parameters
    ----------
    trial: Optuna trial
        A trial is a process of evaluating an objective function.
        For more info, visit
        https://optuna.readthedocs.io/en/stable/reference/generated/optuna.trial.Trial.html
    dict: dict
        A dictionary of estimator params.
        e.g., {
            "eval_metric": ["auc"],
            "max_depth": [2, 3],
            "min_child_weight": [0.1, 0.9],
            "gamma": [1, 9],
            "booster": ["gbtree", "gblinear", "dart"],
             }
    """
    params = {}
    for keyword in dict.keys():
        if keyword not in params.keys():
            if isinstance(dict[keyword][0] , str)  or dict[keyword][0] is None:
                params[keyword] = trial.suggest_categorical(keyword, dict[keyword])
            if isinstance(dict[keyword][0] , int):
                if len(dict[keyword]) >=2:
                    if isinstance(dict[keyword][1] , int):
                        params[keyword] = trial.suggest_int(keyword, min(dict[keyword]), max(dict[keyword]))
                else :
                    params[keyword] = trial.suggest_float(keyword, min(dict[keyword]), max(dict[keyword]))
            if isinstance(dict[keyword][0] , float):
                params[keyword] = trial.suggest_float(keyword, min(dict[keyword]), max(dict[keyword]))
    return params

def calc_metric_for_multi_outputs_classification(
    multi_label, valid_y, preds, SCORE_TYPE
):
    """Internal function for calculating the performance of a multi-output
    classification estimator.

    Parameters
    ----------
    multi_label : Pandas DataFrame
        A multioutput Class label. This is a Pandas multioutput label data frame.
    valid_y : Pandas DataFrame or Pandas Series
        True labels
    preds : Pandas DataFrame Pandas Series
        predicted labels.
    SCORE_TYPE : str
        A string refers to the type of error measurement function.
        Supported values "f1_score", "accuracy_score", "precision_score",
        "recall_score", "roc_auc_score","tp","tn"
    """
    sum_errors = 0

    for i, l in enumerate(multi_label):
        f1 = f1_score(valid_y[l], preds[:, i])
        acc = accuracy_score(valid_y[l], preds[:, i])
        pr = precision_score(valid_y[l], preds[:, i])
        recall = recall_score(valid_y[l], preds[:, i])
        roc = roc_auc_score(valid_y[l], preds[:, i])
        tn, fp, fn, tp = confusion_matrix(
            valid_y[l], preds[:, i], labels=[0, 1]
        ).ravel()

        if SCORE_TYPE == "f1" or SCORE_TYPE == "f1_score":
            sum_errors = sum_errors + f1
        if (
            SCORE_TYPE == "acc"
            or SCORE_TYPE == "accuracy_score"
            or SCORE_TYPE == "accuracy"
        ):
            sum_errors = sum_errors + acc
        if (
            SCORE_TYPE == "pr"
            or SCORE_TYPE == "precision_score"
            or SCORE_TYPE == "precision"
        ):
            sum_errors = sum_errors + pr
        if (
            SCORE_TYPE == "recall"
            or SCORE_TYPE == "recall_score"
            or SCORE_TYPE == "recall"
        ):
            sum_errors = sum_errors + recall
        if (
            SCORE_TYPE == "roc"
            or SCORE_TYPE == "roc_auc_score"
            or SCORE_TYPE == "roc_auc"
        ):
            sum_errors = sum_errors + roc

        # other metrics - not often use

        if SCORE_TYPE == "tp" or SCORE_TYPE == "true possitive":
            sum_errors = sum_errors + tp
        if SCORE_TYPE == "tn" or SCORE_TYPE == "true negative":
            sum_errors = sum_errors + tn

    return sum_errors


def _calc_metric_for_single_output_classification(valid_y, pred_labels, SCORE_TYPE):
    """Internal function for calculating the performance of a
    classification estimator.

    Parameters
    ----------
    valid_y : Pandas DataFrame or Pandas Series
        True labels
    preds : Pandas DataFrame Pandas Series
        predicted labels.
    SCORE_TYPE : str
        A string refers to the type of error measurement function.
        Supported values "f1_score", "accuracy_score", "precision_score",
        "recall_score", "roc_auc_score","tp","tn"

    """

    sum_errors = 0
    f1 = f1_score(valid_y, pred_labels)
    acc = accuracy_score(valid_y, pred_labels)
    pr = precision_score(valid_y, pred_labels)
    recall = recall_score(valid_y, pred_labels)
    roc = roc_auc_score(valid_y, pred_labels)

    tn, _, _, tp = confusion_matrix(valid_y, pred_labels, labels=[0, 1]).ravel()
    if SCORE_TYPE == "f1" or SCORE_TYPE == "f1_score":
        sum_errors = sum_errors + f1
    if (
        SCORE_TYPE == "acc"
        or SCORE_TYPE == "accuracy_score"
        or SCORE_TYPE == "accuracy"
    ):
        sum_errors = sum_errors + acc
    if (
        SCORE_TYPE == "pr"
        or SCORE_TYPE == "precision_score"
        or SCORE_TYPE == "precision"
    ):
        sum_errors = sum_errors + pr
    if SCORE_TYPE == "recall" or SCORE_TYPE == "recall_score" or SCORE_TYPE == "recall":
        sum_errors = sum_errors + recall
    if SCORE_TYPE == "roc" or SCORE_TYPE == "roc_auc_score" or SCORE_TYPE == "roc_auc":
        sum_errors = sum_errors + roc

    # other metrics - not often use

    if SCORE_TYPE == "tp" or SCORE_TYPE == "true possitive":
        sum_errors = sum_errors + tp
    if SCORE_TYPE == "tn" or SCORE_TYPE == "true negative":
        sum_errors = sum_errors + tn

    return sum_errors


def _calc_metric_for_single_output_regression(valid_y, pred_labels, SCORE_TYPE):
    """Internal function for calculating the performance of a
    regression estimator.

    Parameters
    ----------
    valid_y : Pandas DataFrame or Pandas Series
        True values
    preds : Pandas DataFrame Pandas Series
        predicted values.
    SCORE_TYPE : str
        A string refers to the type of error measurement function.
        Supported values "r2_score", "explained_variance_score", "max_error",
        "mean_absolute_error", "mean_squared_error","median_absolute_error",
        "mean_absolute_percentage_error"

    """

    r2 = r2_score(valid_y, pred_labels)
    explained_variance_score_sr = explained_variance_score(valid_y, pred_labels)

    max_error_err = max_error(valid_y, pred_labels)
    mean_absolute_error_err = mean_absolute_error(valid_y, pred_labels)
    mean_squared_error_err = mean_squared_error(valid_y, pred_labels)
    median_absolute_error_err = median_absolute_error(valid_y, pred_labels)
    mean_absolute_percentage_error_err = mean_absolute_percentage_error(
        valid_y, pred_labels
    )

    if SCORE_TYPE == "r2" or SCORE_TYPE == "r2_score":
        return r2
    if SCORE_TYPE == "explained_variance_score":
        return explained_variance_score_sr

    if SCORE_TYPE == "max_error":
        return max_error_err
    if SCORE_TYPE == "mean_absolute_error":
        return mean_absolute_error_err
    if SCORE_TYPE == "mean_squared_error":
        return mean_squared_error_err
    if SCORE_TYPE == "median_absolute_error":
        return median_absolute_error_err
    if SCORE_TYPE == "mean_absolute_percentage_error":
        return mean_absolute_percentage_error_err


def _calc_best_estimator_optuna_univariate(
    X,
    y,
    estimator,
    measure_of_accuracy,
    estimator_params,
    verbose,
    test_size,
    random_state,
    eval_metric,
    number_of_trials,
    sampler,
    pruner,
    with_stratified,
):
    """Internal function for returning best estimator using
    assigned parameters by Optuna.

    Parameters
    ----------
    X : Pandas DataFrame
        Training data. Must fulfill input requirements of the feature selection
        step of the pipeline.
    y : Pandas DataFrame or Pandas series
        Training targets. Must fulfill label requirements of the feature selection
        step of the pipeline.
    estimator: object
        An unfitted estimator. For now, only tree-based estimators. Supported
        methods are, "XGBRegressor",
        ``XGBClassifier``, ``RandomForestClassifier``,``RandomForestRegressor``,
        ``CatBoostClassifier``,``CatBoostRegressor``,
        ``BalancedRandomForestClassifier``,
        ``LGBMClassifier``, and ``LGBMRegressor``.
    estimator_params: dict
        Parameters passed to find the best estimator using optimization
        method. 
    measure_of_accuracy : str
        Measurement of performance for classification and
        regression estimator during hyperparameter optimization while
        estimating best estimator. Classification-supported measurments are
        f1, f1_score, acc, accuracy_score, pr, precision_score,
        recall, recall_score, roc, roc_auc_score, roc_auc,
        tp, true positive, tn, true negative. Regression supported
        measurements are r2, r2_score, explained_variance_score,
        max_error, mean_absolute_error, mean_squared_error,
        median_absolute_error, and mean_absolute_percentage_error.    ----------
    verbose : int
        Controls the verbosity across all objects: the higher, the more messages.
    test_size : float or int
        If float, it should be between 0.0 and 1.0 and represent the proportion
        of the dataset to include in the train split during estimating the best estimator
        by optimization method. If int represents the
        absolute number of train samples. If None, the value is automatically
        set to the complement of the test size.
    random_state : int
        Random number seed.
    eval_metric : str
        An evaluation metric name for pruning. For xgboost.XGBClassifier it is
        ``auc``, for catboost.CatBoostClassifier it is ``AUC`` for catboost.CatBoostRegressor
        it is ``RMSE``.
    number_of_trials : int
        The number of trials. If this argument is set to None,
        there is no limitation on the number of trials.
    sampler : object
        optuna.samplers. For more information, see:
        ``https://optuna.readthedocs.io/en/stable/reference/samplers.html#module-optuna.samplers``.
    pruner : object
        optuna.pruners. For more information, see:
        ``https://optuna.readthedocs.io/en/stable/reference/pruners.html``.
    with_stratified : bool
        Set True if you want data split in a stratified fashion. (default ``True``).
    """


    if estimator.__class__.__name__ == "LogisticRegression" and with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, stratify=y[y.columns.to_list()[0]], test_size=test_size
        )
        print(train_x)

    if estimator.__class__.__name__ == "LogisticRegression" and not with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

    if estimator.__class__.__name__ == "SVC" and with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, stratify=y[y.columns.to_list()[0]], test_size=test_size
        )
        print(train_x)

    if estimator.__class__.__name__ == "SVC" and not with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

    if estimator.__class__.__name__ == "XGBClassifier" and with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, stratify=y[y.columns.to_list()[0]], test_size=test_size
        )
        print(train_x)

    if estimator.__class__.__name__ == "XGBClassifier" and not with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        print(train_x)
    if estimator.__class__.__name__ == "XGBRegressor":
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
    if estimator.__class__.__name__ == "LinearRegression":
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

    if estimator.__class__.__name__ == "CatBoostClassifier" and with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, stratify=y[y.columns.to_list()[0]], test_size=test_size
        )
    if estimator.__class__.__name__ == "CatBoostClassifier" and not with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(X, y, test_size=test_size)
    if estimator.__class__.__name__ == "CatBoostRegressor":
        train_x, valid_x, train_y, valid_y = train_test_split(X, y, test_size=test_size)
    if estimator.__class__.__name__ == "LinearRegression":
        train_x, valid_x, train_y, valid_y = train_test_split(X, y, test_size=test_size)

    if estimator.__class__.__name__ == "RandomForestClassifier" and with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, stratify=y[y.columns.to_list()[0]], test_size=test_size
        )
    if estimator.__class__.__name__ == "RandomForestClassifier" and not with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(X, y, test_size=test_size)
    if estimator.__class__.__name__ == "RandomForestRegressor":
        train_x, valid_x, train_y, valid_y = train_test_split(X, y, test_size=test_size)

    if (
        estimator.__class__.__name__ == "BalancedRandomForestClassifier"
        and with_stratified
    ):
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, stratify=y[y.columns.to_list()[0]], test_size=test_size
        )
    if (
        estimator.__class__.__name__ == "BalancedRandomForestClassifier"
        and not with_stratified
    ):
        train_x, valid_x, train_y, valid_y = train_test_split(X, y, test_size=test_size)

    if estimator.__class__.__name__ == "LGBMClassifier" and with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(
            X, y, stratify=y[y.columns.to_list()[0]], test_size=test_size
        )
    if estimator.__class__.__name__ == "LGBMClassifier" and not with_stratified:
        train_x, valid_x, train_y, valid_y = train_test_split(X, y, test_size=test_size)
    if estimator.__class__.__name__ == "LGBMRegressor":
        train_x, valid_x, train_y, valid_y = train_test_split(X, y, test_size=test_size)

    def objective(trial):
        nonlocal train_x
        nonlocal train_x
        nonlocal train_y
        nonlocal valid_y

        if (
            estimator.__class__.__name__ == "XGBClassifier"
            or estimator.__class__.__name__ == "XGBRegressor"
        ):
            dtrain = xgboost.DMatrix(train_x, label=train_y)
            dvalid = xgboost.DMatrix(valid_x, label=valid_y)
            param = {}
            param["verbosity"] = verbose
            param["eval_metric"] = eval_metric

            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )

            if estimator.__class__.__name__ == "XGBRegressor":
                est = xgboost.train(
                    param,
                    dtrain,
                    evals=[(dvalid, "validation")],
                    callbacks=None,
                )
            if estimator.__class__.__name__ == "XGBClassifier":
                est = xgboost.train(
                    param,
                    dtrain,
                    evals=[(dvalid, "validation")],
                )
            preds = est.predict(dvalid)
            pred_labels = np.rint(preds)

        if estimator.__class__.__name__ == "LogisticRegression":

            param = {}
            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )
            param["verbose"] = verbose
            lgc = LogisticRegression(**param)
            lgc.fit(train_x, train_y)
            preds = lgc.predict(valid_x)
            pred_labels = np.rint(preds)

        if estimator.__class__.__name__ == "SVC":

            param = {}
            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )
            svc = SVC(**param)
            svc.fit(train_x, train_y)
            preds = svc.predict(valid_x)
            pred_labels = np.rint(preds)

        if estimator.__class__.__name__ == "CatBoostClassifier":

            param = {}
            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )
            param["verbose"] = verbose
            param["eval_metric"] = eval_metric

            catest = catboost.CatBoostClassifier(**param)
            catest.fit(train_x, train_y, eval_set=[(valid_x, valid_y)], verbose=verbose)
            preds = catest.predict(valid_x)
            pred_labels = np.rint(preds)

        if estimator.__class__.__name__ == "LGBMClassifier":

            param = {}
            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )
            param["verbose"] = verbose
            param["eval_metric"] = eval_metric
            lgbest = lightgbm.LGBMClassifier(**param)
            lgbest.fit(train_x, train_y, eval_set=[(valid_x, valid_y)], verbose=verbose)
            preds = lgbest.predict(valid_x)
            pred_labels = np.rint(preds)

        if estimator.__class__.__name__ == "CatBoostRegressor":
            param = {}
            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )

            param["verbose"] = verbose
            param["eval_metric"] = eval_metric
            catest = catboost.CatBoostRegressor(**param)
            catest.fit(train_x, train_y, eval_set=[(valid_x, valid_y)], verbose=verbose)
            preds = catest.predict(valid_x)

        if estimator.__class__.__name__ == "LGBMRegressor":
            param = {}
            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )

            param["verbose"] = verbose
            param["eval_metric"] = eval_metric
            lgbest = lightgbm.LGBMRegressor(**param)
            lgbest.fit(train_x, train_y, eval_set=[(valid_x, valid_y)], verbose=verbose)
            preds = lgbest.predict(valid_x)

        if estimator.__class__.__name__ == "RandomForestClassifier":

            param = {}
            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )
            param["verbose"] = verbose
            rfest = RandomForestClassifier(**param)
            rfest.fit(train_x, train_y.values.ravel())
            preds = rfest.predict(valid_x)
            pred_labels = preds

        if estimator.__class__.__name__ == "BalancedRandomForestClassifier":

            param = {}
            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )
            param["verbose"] = verbose
            brfest = BalancedRandomForestClassifier(**param)
            brfest.fit(train_x, train_y.values.ravel())
            preds = brfest.predict(valid_x)
            pred_labels = preds

        if estimator.__class__.__name__ == "RandomForestRegressor":
            param = {}
            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )

            param["verbose"] = verbose
            rfest = RandomForestRegressor(**param)
            rfest.fit(train_x, train_y)
            preds = rfest.predict(valid_x)

        if estimator.__class__.__name__ == "LinearRegression":
            param = {}
            for param_key in estimator_params.keys():
                param[param_key] = _trail_param_retrive(
                    trial, estimator_params, param_key
                )

            param["verbose"] = verbose
            lr = LinearRegression(**param)
            lr.fit(train_x, train_y)
            preds = lr.predict(valid_x)

        if (
            "classifier" in estimator.__class__.__name__.lower()
            or "svc" in estimator.__class__.__name__.lower()
            or "logisticregression" in estimator.__class__.__name__.lower()
        ):
            accr = _calc_metric_for_single_output_classification(
                valid_y, pred_labels, measure_of_accuracy
            )
        if "regressor" in estimator.__class__.__name__.lower():
            accr = _calc_metric_for_single_output_regression(
                valid_y, preds, measure_of_accuracy
            )

        return accr

    study = optuna.create_study(direction="maximize", sampler=sampler, pruner=pruner)
    study.optimize(objective, n_trials=number_of_trials, timeout=600)
    trial = study.best_trial

    if (
        estimator.__class__.__name__ == "XGBRegressor"
        or estimator.__class__.__name__ == "XGBClassifier"
    ):
        dtrain = xgboost.DMatrix(train_x, label=train_y)
        dvalid = xgboost.DMatrix(valid_x, label=valid_y)
        print(trial.params)
        best_estimator = xgboost.train(
            trial.params,
            dtrain,
            evals=[(dvalid, "validation")],
        )
    if estimator.__class__.__name__ == "LogisticRegression":
        print(trial.params)
        clf = LogisticRegression(**trial.params)
        best_estimator = clf.fit(train_x, train_y)
    if estimator.__class__.__name__ == "LinearRegression":
        print(trial.params)
        regressor = LinearRegression(**trial.params)
        best_estimator = regressor.fit(train_x, train_y)
    if estimator.__class__.__name__ == "SVC":
        print(trial.params)
        clf = SVC(**trial.params)
        best_estimator = clf.fit(train_x, train_y)
    if estimator.__class__.__name__ == "CatBoostClassifier":
        print(trial.params)
        clf = catboost.CatBoostClassifier(**trial.params)
        best_estimator = clf.fit(train_x, train_y)
    if estimator.__class__.__name__ == "CatBoostRegressor":
        print(trial.params)
        regressor = catboost.CatBoostRegressor(**trial.params)
        best_estimator = regressor.fit(train_x, train_y)
    if estimator.__class__.__name__ == "RandomForestClassifier":
        print(trial.params)
        clf = RandomForestClassifier(**trial.params)
        best_estimator = clf.fit(train_x, train_y.values.ravel())
    if estimator.__class__.__name__ == "RandomForestRegressor":
        print(trial.params)
        regressor = RandomForestRegressor(**trial.params)
        best_estimator = regressor.fit(train_x, train_y)
    if estimator.__class__.__name__ == "BalancedRandomForestClassifier":
        print(trial.params)
        clf = BalancedRandomForestClassifier(**trial.params)
        best_estimator = clf.fit(train_x, train_y.values.ravel())
    if estimator.__class__.__name__ == "LGBMClassifier":
        print(trial.params)
        clf = lightgbm.LGBMClassifier(**trial.params)
        best_estimator = clf.fit(train_x, train_y.values.ravel())
    if estimator.__class__.__name__ == "LGBMRegressor":
        print(trial.params)
        regressor = lightgbm.LGBMRegressor(**trial.params)
        best_estimator = regressor.fit(train_x, train_y)

    return best_estimator, study, trial
