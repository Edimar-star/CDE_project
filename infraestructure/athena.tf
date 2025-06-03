resource "aws_glue_catalog_database" "athena_db" {
  name = "forest_fire_data"
}

resource "aws_glue_catalog_table" "athena_table" {
  name          = "fires"
  database_name = aws_glue_catalog_database.athena_db.name
  table_type    = "EXTERNAL_TABLE"

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.target-data-bucket.bucket}/processed/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      name                  = "fires-serde"
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    # Columnas definidas correctamente aquí
    columns {
      name = "latitude"
      type = "double"
    }
    columns {
      name = "longitude"
      type = "double"
    }
    columns {
      name = "population_density"
      type = "double"
    }
    columns {
      name = "days"
      type = "int"
    }
    columns {
      name = "wind_speed"
      type = "double"
    }
    columns {
      name = "vapor_pressure_deficit"
      type = "double"
    }
    columns {
      name = "vapor_pressure"
      type = "double"
    }
    columns {
      name = "minimum_temperature"
      type = "double"
    }
    columns {
      name = "maximum_temperature"
      type = "double"
    }
    columns {
      name = "snow_water_equivalent"
      type = "double"
    }
    columns {
      name = "surface_shortwave_radiation"
      type = "double"
    }
    columns {
      name = "soil_moisture"
      type = "double"
    }
    columns {
      name = "runoff"
      type = "double"
    }
    columns {
      name = "precipitation_accumulation"
      type = "double"
    }
    columns {
      name = "Reference_evapotranspiration"
      type = "double"
    }
    columns {
      name = "climate_water_deficit"
      type = "double"
    }
    columns {
      name = "actual_Evapotranspiration"
      type = "double"
    }
    columns {
      name = "palmer_drought_severity_index"
      type = "double"
    }
    columns {
      name = "brightness_temperature"
      type = "double"
    }
    columns {
      name = "scan_fire_size"
      type = "double"
    }
    columns {
      name = "track_fire_size"
      type = "double"
    }
    columns {
      name = "confidence"
      type = "string"
    }
    columns {
      name = "fire_radiative_power"
      type = "double"
    }
    columns {
      name = "daynight"
      type = "string"
    }
    columns {
      name = "fire_type"
      type = "string"
    }
    columns {
      name = "n_pixels_ndvi"
      type = "double"
    }
    columns {
      name = "ndvi"
      type = "double"
    }
    columns {
      name = "ndvi_long_term_average"
      type = "double"
    }
    columns {
      name = "ndvi_anomaly_percent"
      type = "double"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_athena_workgroup" "main" {
  name = "primary"

  configuration {
    enforce_workgroup_configuration = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/results/"
    }
  }

  state = "ENABLED"
}
