import streamlit as st
import numpy as np
import requests
import json

st.title("🔥 Predicción de Incendios Forestales")

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

# Campos string
categorical = ["daynight", "fire_type"]

# Formulario
input_data = {}
with st.form("prediction_form"):
    for col in columns:
        if col in categorical:
            input_data[col] = st.selectbox(col, ["D", "N"] if col == "daynight" else ["presumed vegetation fire", "active volcano", "other static land source", "offshore"])
        else:
            input_data[col] = st.number_input(col, step=0.1)

    submitted = st.form_submit_button("Predecir")

if submitted:
    try:
        X = np.array([[input_data[col] for col in columns]])
        prediction = model.predict(X)[0]
        st.success(f"🔥 Predicción: {prediction}")
    except Exception as e:
        st.error(f"Error en la predicción: {e}")
