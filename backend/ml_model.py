
from functools import lru_cache

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


@lru_cache(maxsize=1)
def train_model():
    rng = np.random.default_rng(42)

    fill = rng.uniform(5, 95, 1200)
    growth = rng.uniform(2, 20, 1200)

    X = np.column_stack((fill, growth))
    y = (100 - fill) / growth

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=30,
        max_depth=12,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)
    predicted = model.predict(X_test)

    metrics = {
        "model": "Random Forest Regressor",
        "training_samples": len(X_train),
        "testing_samples": len(X_test),
        "mae_days": round(
            float(mean_absolute_error(y_test, predicted)), 3
        ),
        "r2_score": round(
            float(r2_score(y_test, predicted)), 4
        ),
        "data_source": "Synthetic simulation data",
        "evaluation_type": "Held-out synthetic test set"
    }

    comparison = [
        {
            "sample": i + 1,
            "actual": round(float(y_test[i]), 2),
            "predicted": round(float(predicted[i]), 2)
        }
        for i in range(min(30, len(y_test)))
    ]

    return model, metrics, comparison


def predict_time_to_full(fill_percent, daily_growth):
    fill = float(fill_percent)
    growth = float(daily_growth)

    if fill >= 100:
        return 0.0

    if growth <= 0:
        return None

    model, _, _ = train_model()

    result = model.predict(
        np.array([[fill, growth]])
    )[0]

    return round(max(0, float(result)), 2)


def get_priority(fill_percent, weight_percent, days_left):
    if fill_percent >= 90 or weight_percent >= 90:
        return "Critical"

    if fill_percent >= 75 or weight_percent >= 75:
        return "High"

    if days_left is not None and days_left <= 2:
        return "High"

    if fill_percent >= 50 or weight_percent >= 50:
        return "Medium"

    return "Low"


def get_model_evaluation():
    _, metrics, comparison = train_model()

    return {
        "metrics": metrics,
        "comparison": comparison
    }
