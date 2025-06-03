import streamlit as st
import pandas as pd
import joblib
import json

# Carga el modelo entrenado
model = joblib.load("./model/model.joblib")
with open("./model/model_columns.json", "r") as f:
    expected_cols = json.load(f)

# Categorías que usaste en el entrenamiento
daynight_categories = ["D", "N"]
fire_type_categories = ["presumed vegetation fire", "active volcano", "other static land source", "offshore"]

def main():
    st.title("Predicción de incendios")

    # Inputs del usuario
    data = {}
    data["latitude"] = st.number_input("Latitude", format="%.6f")
    data["longitude"] = st.number_input("Longitude", format="%.6f")
    data["population_density"] = st.number_input("Population Density", min_value=0.0)
    data["days"] = st.number_input("Days", min_value=0, step=1)
    data["wind_speed"] = st.number_input("Wind Speed", min_value=0.0)
    data["vapor_pressure_deficit"] = st.number_input("Vapor Pressure Deficit", min_value=0.0)
    data["vapor_pressure"] = st.number_input("Vapor Pressure", min_value=0.0)
    data["minimum_temperature"] = st.number_input("Minimum Temperature")
    data["maximum_temperature"] = st.number_input("Maximum Temperature")
    data["snow_water_equivalent"] = st.number_input("Snow Water Equivalent", min_value=0.0)
    data["surface_shortwave_radiation"] = st.number_input("Surface Shortwave Radiation", min_value=0.0)
    data["soil_moisture"] = st.number_input("Soil Moisture", min_value=0.0)
    data["runoff"] = st.number_input("Runoff", min_value=0.0)
    data["precipitation_accumulation"] = st.number_input("Precipitation Accumulation", min_value=0.0)
    data["Reference_evapotranspiration"] = st.number_input("Reference Evapotranspiration", min_value=0.0)
    data["climate_water_deficit"] = st.number_input("Climate Water Deficit", min_value=0.0)
    data["actual_Evapotranspiration"] = st.number_input("Actual Evapotranspiration", min_value=0.0)
    data["palmer_drought_severity_index"] = st.number_input("Palmer Drought Severity Index")
    data["brightness_temperature"] = st.number_input("Brightness Temperature", min_value=0.0)
    data["scan_fire_size"] = st.number_input("Scan Fire Size", min_value=0.0)
    data["track_fire_size"] = st.number_input("Track Fire Size", min_value=0.0)
    data["fire_radiative_power"] = st.number_input("Fire Radiative Power", min_value=0.0)
    data["n_pixels_ndvi"] = st.number_input("N Pixels NDVI", min_value=0.0)
    data["ndvi"] = st.number_input("NDVI", min_value=0.0)
    data["ndvi_long_term_average"] = st.number_input("NDVI Long Term Average", min_value=0.0)
    data["ndvi_anomaly_percent"] = st.number_input("NDVI Anomaly Percent", min_value=0.0)

    data["daynight"] = st.selectbox("Day/Night", options=daynight_categories)
    data["fire_type"] = st.selectbox("Fire Type", options=fire_type_categories)

    if st.button("Predict"):
        df = pd.DataFrame([data])

        # One-hot encoding manual para las categorías (para que coincida con entrenamiento)
        for cat in daynight_categories:
            df[f"daynight_{cat}"] = (df["daynight"] == cat).astype(int)
        for cat in fire_type_categories:
            df[f"fire_type_{cat}"] = (df["fire_type"] == cat).astype(int)

        # Elimina las columnas categóricas originales
        df = df.drop(columns=["daynight", "fire_type"])

        # Agrega las columnas faltantes con 0 para evitar errores
        for col in expected_cols:
            if col not in df.columns:
                df[col] = 0

        df = df[expected_cols]

        pred = model.predict(df.values)[0]
        messages = {
            "l": "Low probability of fire, between 0% to 30% of probability.",
            "n": "Medium probability of fire, between 30% to 80% of probability.",
            "h": "High probability of fire, between 80% to 100% of probability."
        }
        st.write(f"Prediction: {messages[pred]}")

if __name__ == "__main__":
    main()
