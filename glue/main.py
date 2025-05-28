import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext

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

# ----------------------- UNION DATA NDVI - DIVIPOLAS ---------------------------

# ---------------------- UNION DATA FOREST_FIRE - NDVI --------------------------

# ------------------ UNION DATA FOREST_FIRE - GLOBAL_CLIMATE --------------------

# -------------- UNION DATA FOREST_FIRE - POPULATION_DENSITY --------------------

#df.write.mode('overwrite').parquet(f's3://target-data-bucket/forest_fire_COLOMBIA/')

job.commit()
