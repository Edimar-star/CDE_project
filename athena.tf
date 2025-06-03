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
