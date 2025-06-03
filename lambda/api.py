import boto3
import tarfile
import joblib
import json
import os
import tempfile
import numpy as np

s3 = boto3.client('s3')

# Ejecuta solo una vez (fuera del handler) para evitar recarga innecesaria
def load_model_from_s3():
    bucket = "target-data-bucket-6i2caq"
    key = "model/model.joblib"

    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, "model.joblib")
        s3.download_file(bucket, key, model_path)
        model = joblib.load(model_path)
    
    return model

model = load_model_from_s3()

def lambda_handler(event, context):
    try:
        input_data = json.loads(event["body"])

        columns = [
            "latitude", "longitude", "population_density", "days", "wind_speed", 
            "vapor_pressure_deficit", "vapor_pressure", "minimum_temperature", 
            "maximum_temperature", "snow_water_equivalent", "surface_shortwave_radiation", 
            "soil_moisture", "runoff", "precipitation_accumulation", "Reference_evapotranspiration", 
            "climate_water_deficit", "actual_Evapotranspiration", "palmer_drought_severity_index", 
            "brightness_temperature", "scan_fire_size", "track_fire_size", "confidence", 
            "fire_radiative_power", "daynight", "fire_type", "n_pixels_ndvi", "ndvi", 
            "ndvi_long_term_average", "ndvi_anomaly_percent"
        ]

        X = np.array([[input_data[col] for col in columns]])
        prediction = model.predict(X)[0]

        return {
            "statusCode": 200,
            "body": json.dumps({"prediction": int(prediction)})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
