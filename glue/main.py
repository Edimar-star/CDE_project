import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import StringType
from pyspark.sql.window import Window

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# ------------------------------ FOREST FIRE -------------------------------
dyf_forest_fire = glueContext.create_dynamic_frame.from_catalog(
    database='org-report',
    table_name='forest_fire'
)
df_forest_fire = dyf_forest_fire.toDF()

def asign_class(value):
    if value in ["l", "n", "h"]:
        return value

    x = int(value)
    if 0 <= x < 30:
        return "l"
    elif 30 <= x < 80:
        return "n"

    return "h"

asign_class_udf = F.udf(asign_class, StringType())
df_forest_fire = df_forest_fire.withColumn("confidence", asign_class_udf(df_forest_fire["confidence"]))

# ---------------------------------- NDVI ----------------------------------
dyf_ndvi = glueContext.create_dynamic_frame.from_catalog(
    database='org-report',
    table_name='ndvi'
)
df_ndvi = dyf_ndvi.toDF()

# --------------------------- POPULATION DENSITY ---------------------------
dyf_population_density = glueContext.create_dynamic_frame.from_catalog(
    database='org-report',
    table_name='population_density'
)
df_population_density = dyf_population_density.toDF()

# ----------------------------- GLOBAL CLIMATE -----------------------------
dyf_global_climate = glueContext.create_dynamic_frame.from_catalog(
    database='org-report',
    table_name='global_climate'
)
df_global_climate = dyf_global_climate.toDF()

# ---------------------- UNION DATA FOREST_FIRE - NDVI --------------------------
df_final                = df_forest_fire.join(
    df_ndvi, 
    on=["latitude", "longitude", "date"], 
    how="left"
)

# ------------------ UNION DATA FOREST_FIRE - GLOBAL_CLIMATE --------------------
kelvin = 273.15
df_global_climate       = df_global_climate.withColumn("tmin", F.col("tmin") + kelvin)
df_global_climate       = df_global_climate.withColumn("tmax", F.col("tmax") + kelvin)
df_final                = df_final.join(
    df_global_climate, 
    on=["latitude", "longitude", "date"], 
    how="left"
)


# -------------- UNION DATA FOREST_FIRE - POPULATION_DENSITY --------------------
df_final   = df_final.withColumn("date", F.to_date("date", "yyyy-MM-dd"))
df_final   = df_final.withColumn("year", F.year("date"))

# join por latitude, longitude y year
df_final                = df_final.join(
    df_population_density, 
    on=["latitude", "longitude", "year"], 
    how="left"
)
df_final = df_final.drop("year")

# Renombramiento de columnas
columns = {
    "latitude": "latitude", "longitude": "longitude", "population_density": "population_density", 
    "date": "date", "ws": "wind_speed", "vpd": "vapor_pressure_deficit", "vap": "vapor_pressure", 
    "tmin": "minimum_temperature", "tmax": "maximum_temperature", "swe": "snow_water_equivalent",
    "srad": "surface_shortwave_radiation", "soil": "soil_moisture", "q": "runoff", "ppt": "precipitation_accumulation", 
    "pet": "Reference_evapotranspiration", "def": "climate_water_deficit", "aet": "actual_Evapotranspiration",
    "PDSI": "palmer_drought_severity_index", "brightness": "brightness_temperature", "scan": "scan_fire_size", 
    "track": "track_fire_size", "confidence": "confidence", "frp": "fire_radiative_power", "daynight": "daynight", 
    "type": "fire_type", "n_pixels": "n_pixels_ndvi", "vim": "ndvi", "vim_avg": "ndvi_long_term_average", "viq": "ndvi_anomaly_percent"
}

for old_name, new_name in columns.items():
    df_final = df_final.withColumnRenamed(old_name, new_name)

# Seleccion de columnas
df_final = df_final.select(*columns.values())

# ----------------------------- SAVING DATA --------------------------------
df_final.write.mode('overwrite').parquet(f's3://target-data-bucket-6i2caq/processed/')
df_final.write.mode('overwrite').option("header", True).csv(f's3://target-data-bucket-6i2caq/training/')

# -------------------------------- FINISH JOB --------------------------------
job.commit()
