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
print("Leyendo forest_fire...")
dyf_forest_fire = glueContext.create_dynamic_frame.from_catalog(
    database='org-report',
    table_name='forest_fire'
)
df_forest_fire = dyf_forest_fire.toDF().cache()

def asign_class(value):
    try:
        if value in ["l", "n", "h"]:
            return value
        if value is None:
            return "l"
        x = int(value)
        if 0 <= x < 30:
            return "l"
        elif 30 <= x < 80:
            return "n"
        return "h"
    except:
        return "l"

asign_class_udf = F.udf(asign_class, StringType())
df_forest_fire = df_forest_fire.withColumn("confidence", asign_class_udf(df_forest_fire["confidence"]))

# ---------------------------------- NDVI ----------------------------------
print("Leyendo ndvi...")
dyf_ndvi = glueContext.create_dynamic_frame.from_catalog(
    database='org-report',
    table_name='ndvi'
)
df_ndvi = dyf_ndvi.toDF().cache()

# --------------------------- POPULATION DENSITY ---------------------------
print("Leyendo population_density...")
dyf_population_density = glueContext.create_dynamic_frame.from_catalog(
    database='org-report',
    table_name='population_density'
)
df_population_density = dyf_population_density.toDF().cache()

# ----------------------------- GLOBAL CLIMATE -----------------------------
print("Leyendo global_climate...")
dyf_global_climate = glueContext.create_dynamic_frame.from_catalog(
    database='org-report',
    table_name='global_climate'
)
df_global_climate = dyf_global_climate.toDF().cache()

# ---------------------- UNIÓN FOREST_FIRE - NDVI --------------------------
print("Uniendo forest_fire con ndvi...")
df_final = df_forest_fire \
    .withColumn("date", F.to_date("date")) \
    .join(
        df_ndvi.withColumn("date", F.to_date("date")),
        on=["latitude", "longitude", "date"],
        how="left"
    )

# ------------------ UNIÓN FOREST_FIRE - GLOBAL_CLIMATE --------------------
print("Uniendo con global_climate...")
kelvin = 273.15
df_global_climate = df_global_climate \
    .withColumn("date", F.to_date("date")) \
    .withColumn("tmin", F.col("tmin") + kelvin) \
    .withColumn("tmax", F.col("tmax") + kelvin)

df_final = df_final.join(
    df_global_climate,
    on=["latitude", "longitude", "date"],
    how="left"
)

# -------------- UNIÓN FOREST_FIRE - POPULATION_DENSITY --------------------
print("Uniendo con population_density...")
df_final = df_final.withColumn("year", F.year("date"))
df_population_density = df_population_density.withColumn("year", F.col("year").cast("int"))

df_final = df_final.join(
    df_population_density,
    on=["latitude", "longitude", "year"],
    how="left"
).drop("year")

# -------------------------- Renombrar columnas -----------------------------
print("Renombrando columnas...")
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
    if old_name != new_name:
        df_final = df_final.withColumnRenamed(old_name, new_name)

df_final = df_final.select(*columns.values()).cache()

# ----------------------------- GUARDAR DATOS -------------------------------
print("Guardando en Parquet y CSV...")
df_final.write.mode('overwrite').parquet("s3://target-data-bucket-6i2caq/processed/")
df_final.write.mode('overwrite').option("header", True).csv("s3://target-data-bucket-6i2caq/training/")

# -------------------------------- FINISH JOB ------------------------------
print("Job completado con éxito.")
job.commit()
