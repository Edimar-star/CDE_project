import os
import joblib
import numpy as np
import pandas as pd
import requests

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score

def load_data_from_lambda(endpoint_url):
    """Hace una solicitud al endpoint REST de Lambda y carga los datos como DataFrame"""
    response = requests.get(endpoint_url)
    response.raise_for_status()  # lanza excepción si falla

    json_data = response.json()

    if not isinstance(json_data, list):
        raise ValueError("La respuesta del endpoint no es una lista de registros")

    return pd.DataFrame(json_data)

def evaluate_model(X, y, n_values, n_splits=10):
    metrics = {k: {n: [] for n in n_values} for k in [
        "accuracy_train", "precision_train", "recall_train",
        "accuracy_test", "precision_test", "recall_test"
    ]}
    splits = [train_test_split(X, y, test_size=0.25, random_state=42+i) for i in range(n_splits)]

    for n in n_values:
        for X_train, X_test, y_train, y_test in splits:
            model = RandomForestClassifier(n_estimators=n, max_depth=5, class_weight="balanced", random_state=42)
            model.fit(X_train, y_train)

            y_train_pred = model.predict(X_train)
            y_test_pred = model.predict(X_test)

            metrics["accuracy_train"][n].append(accuracy_score(y_train, y_train_pred))
            metrics["precision_train"][n].append(precision_score(y_train, y_train_pred, average='macro', zero_division=1))
            metrics["recall_train"][n].append(recall_score(y_train, y_train_pred, average='macro', zero_division=1))

            metrics["accuracy_test"][n].append(accuracy_score(y_test, y_test_pred))
            metrics["precision_test"][n].append(precision_score(y_test, y_test_pred, average='macro', zero_division=1))
            metrics["recall_test"][n].append(recall_score(y_test, y_test_pred, average='macro', zero_division=1))

    for k in metrics:
        for n in n_values:
            metrics[k][n] = np.mean(metrics[k][n])
    return metrics

def main():
    model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
    
    # ← CAMBIA ESTA URL por tu endpoint real de Lambda REST
    lambda_endpoint = "https://nayoh5iwzl.execute-api.eu-central-1.amazonaws.com/data"
    
    df = load_data_from_lambda(lambda_endpoint)

    target = "confidence"
    X = df.drop(columns=[target]).values
    y = df[target].values

    n_values = range(1, 101)
    metrics = evaluate_model(X, y, n_values)

    best_n = max(metrics["accuracy_test"], key=metrics["accuracy_test"].get)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = RandomForestClassifier(n_estimators=best_n, max_depth=5, class_weight="balanced", random_state=42)
    model.fit(X_train, y_train)

    joblib.dump(model, os.path.join(model_dir, "model.joblib"))
    print(f"Modelo entrenado con n={best_n}. Guardado en {model_dir}/model.joblib")

if __name__ == "__main__":
    main()
