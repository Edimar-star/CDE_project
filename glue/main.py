import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql.functions import regexp_replace, col, year, to_date, abs, datediff, row_number, udf
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

asign_class_udf = udf(asign_class, StringType())
df_forest_fire = df.withColumn("confidence", asign_class_udf(df_forest_fire["confidence"]))

# ---------------------------------- NDVI ----------------------------------
dyf_ndvi = glueContext.create_dynamic_frame.from_catalog(
    database='org-report',
    table_name='ndvi'
)
df_ndvi = dyf_ndvi.toDF()

# ------------------------------- DIVIPOLAS --------------------------------
dyf_divipolas = glueContext.create_dynamic_frame.from_catalog(
    database='org-report',
    table_name='divipolas'
)
df_divipolas = dyf_divipolas.toDF()

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


# ------------------ UNION DATA FOREST_FIRE - GLOBAL_CLIMATE --------------------
kelvin = 273.15
df_global_climate       = df_global_climate.withColumn("tmin", col("tmin") + kelvin)
df_global_climate       = df_global_climate.withColumn("tmax", col("tmax") + kelvin)
df_final                = df_forest_fire.join(
    df_global_climate, 
    on=["latitude", "longitude", "date"], 
    how="inner"
)


# -------------- UNION DATA FOREST_FIRE - POPULATION_DENSITY --------------------
df_population_density   = df_population_density.withColumn("date", to_date("date", "yyyy-MM-dd"))
df_population_density   = df_population_density.withColumn("year", year("date"))

# join por latitude, longitude y year
df_final                = df_final.join(
    df_population_density, 
    on=["latitude", "longitude", "year"], 
    how="inner"
)
df_final = df_final.drop("year")


# ----------------------- UNION DATA NDVI - DIVIPOLAS ---------------------------
# join datasets
df_ndvi_clean           = df_ndvi.withColumn("ADM2_PCODE_clean", regexp_replace("ADM2_PCODE", "^CO", ""))
joined_df_ndvi          = df_ndvi_clean.join(df_divipolas, df_ndvi_clean["ADM2_PCODE_clean"] == df_divipolas["cod_mpio"], how="inner")

# select and rename columns
df_ndvi_result          = joined_df_ndvi.select("latitud", "longitud", "date", "n_pixels", "vim", "vim_avg", "viq")
df_ndvi_result          = df_ndvi_result.withColumnRenamed("latitud", "latitude")
df_ndvi_result          = df_ndvi_result.withColumnRenamed("longitud", "longitude")

# ---------------------- UNION DATA FOREST_FIRE - NDVI --------------------------
# Crear un cross join para comparar todas las combinaciones
joined                  = df_final.alias("a").crossJoin(df_ndvi_result.alias("b"))

# Calcular la distancia entre coordenadas (simple Euclideana 2D) y diferencia de días
joined                  = joined.withColumn(
    "spatial_distance", 
    ((col("a.latitude") - col("b.latitude"))**2 + (col("a.longitude") - col("b.longitude"))**2)
)

joined                  = joined.withColumn(
    "temporal_distance", 
    abs(datediff(col("a.date"), col("b.date")))
)

# Crear un ranking de menor distancia combinada (puedes ponderar si quieres)
joined                  = joined.withColumn(
    "rank", 
    row_number().over(
        Window.partitionBy("a.latitude", "a.longitude", "a.date")
        .orderBy(col("temporal_distance") + col("spatial_distance"))
    )
)

# Quedarse solo con el más cercano
closest = joined.filter(col("rank") == 1).drop("rank", "spatial_distance", "temporal_distance")

# Quitar prefijos
result = closest.select(
    [col(f"a.{c}").alias(c) for c in df1.columns] + 
    [col(f"b.{c}").alias(f"{c}_from_df2") for c in df2.columns if c not in df1.columns]
)

# Renombramiento de columnas
columns = {
    "latitude": "latitude", "longitude": "longitude", "population_density": "population_density", "General class": "land_cover_type",
    "class": "land_cover_subtype", "Sub-class": "vegetation_percent", "date": "date", "ws": "wind_speed", "vpd": "vapor_pressure_deficit",
    "vap": "vapor_pressure", "tmin": "minimum_temperature", "tmax": "maximum_temperature", "swe": "snow_water_equivalent",
    "srad": "surface_shortwave_radiation", "soil": "soil_moisture", "q": "runoff", "ppt": "precipitation_accumulation",
    "pet": "Reference_evapotranspiration", "def": "climate_water_deficit", "aet": "actual_Evapotranspiration",
    "PDSI": "palmer_drought_severity_index", "brightness": "brightness_temperature", "scan": "scan_fire_size", "track": "track_fire_size",
    "confidence": "confidence", "frp": "fire_radiative_power", "daynight": "daynight", "type": "fire_type", "n_pixels": "n_pixels_ndvi",
    "vim": "ndvi", "vim_avg": "ndvi_long_term_average", "viq": "ndvi_anomaly_percent", "year": "year"
}

for old_name, new_name in columns.items():
    result = result.withColumnRenamed(old_name, new_name)

# -------------------------------- FINISH JOB --------------------------------
result.write.mode('overwrite').parquet(f's3://target-data-bucket/forest_fire_COLOMBIA/')
job.commit()
