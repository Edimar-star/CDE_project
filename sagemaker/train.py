from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from io import StringIO
import pandas as pd
import numpy as np
import tarfile
import joblib
import boto3
import glob

# 1. Concatenar todos los archivos en un solo DataFrame
data_dir = '/opt/ml/input/data/train'
all_files = glob.glob(os.path.join(data_dir, 'part-*.csv'))
df = pd.concat((pd.read_csv(f) for f in all_files))

# 2. Separar features y target
target = "confidence"
X = df.drop(target, axis=1).values
y = df[target].values

# 3. Configurar splits
num_arboles, N_SPLITS = range(1, 101), 10
splits = [train_test_split(X, y, test_size=0.25, random_state=42+i) for i in range(N_SPLITS)]

# 4. Métricas
metrics = {
    "accuracy_train": {n: [] for n in num_arboles},
    "precision_train": {n: [] for n in num_arboles},
    "recall_train": {n: [] for n in num_arboles},
    "accuracy_test": {n: [] for n in num_arboles},
    "precision_test": {n: [] for n in num_arboles},
    "recall_test": {n: [] for n in num_arboles},
}

# 5. Entrenar con todos los n_estimators
for n in num_arboles:
    for X_train, X_test, y_train, y_test in splits:
        model = RandomForestClassifier(n_estimators=n, max_depth=5, class_weight="balanced", random_state=42)
        model.fit(X_train, y_train)

        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)

        # Guardar métricas
        metrics["accuracy_train"][n].append(accuracy_score(y_train, y_train_pred))
        metrics["precision_train"][n].append(precision_score(y_train, y_train_pred, average='macro', zero_division=1))
        metrics["recall_train"][n].append(recall_score(y_train, y_train_pred, average='macro', zero_division=1))

        metrics["accuracy_test"][n].append(accuracy_score(y_test, y_test_pred))
        metrics["precision_test"][n].append(precision_score(y_test, y_test_pred, average='macro', zero_division=1))
        metrics["recall_test"][n].append(recall_score(y_test, y_test_pred, average='macro', zero_division=1))

# 6. Promediar
for k in metrics:
    for n in num_arboles:
        metrics[k][n] = np.mean(metrics[k][n])

# 7. Seleccionar mejor `n`
best_n = max(metrics["accuracy_test"], key=metrics["accuracy_test"].get)

# 8. Entrenar modelo final con el mejor `n`
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
final_model = RandomForestClassifier(n_estimators=best_n, max_depth=5, class_weight="balanced", random_state=42)
final_model.fit(X_train, y_train)
score = model.score(X_test, y_test)

# 9. Guardar modelo como .joblib
joblib.dump(final_model, "model.joblib")

# 10. Subir modelo a S3 como .tar.gz
with tarfile.open("model.tar.gz", "w:gz") as tar:
    tar.add("model.joblib")

s3.upload_file("model.tar.gz", bucket_name, "model/model.tar.gz")
print(f"Modelo entrenado con n={best_n} y score={score} subido a S3.")