from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from io import StringIO
import pandas as pd
import numpy as np
import tarfile
import joblib
import glob

def main()
    # Concatenar todos los archivos en un solo DataFrame
    data_dir = '/opt/ml/input/data/train'
    all_files = glob.glob(os.path.join(data_dir, 'part-*.csv'))
    df = pd.concat((pd.read_csv(f) for f in all_files))

    # Separar features y target
    target = "confidence"
    X = df.drop(target, axis=1).values
    y = df[target].values

    # Entrenar modelo
    n_estimators = 40
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    final_model = RandomForestClassifier(n_estimators=n_estimators, max_depth=5, class_weight="balanced", random_state=42)
    final_model.fit(X_train, y_train)
    score = final_model.score(X_test, y_test)

    # Guardar modelo como .joblib
    output_path = os.environ["SM_MODEL_DIR"]
    joblib.dump(final_model, os.path.join(output_path, "model.joblib"))

    print(f"Modelo entrenado con n={n_estimators} y score={score} guardado en {output_path}")


if __name__ == "__main__":
    main()