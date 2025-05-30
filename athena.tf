resource "aws_glue_catalog_database" "athena_db" {
  name = "forest_fire_data"
}

resource "aws_glue_catalog_table" "athena_table" {
  name          = "fires"
  database_name = aws_glue_catalog_database.athena_db.name
  table_type    = "EXTERNAL_TABLE"

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.target-data-bucket.bucket}/processed/fires/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "fires-serde"
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
      parameters = {
        "field.delim" = ","
      }
    }
  }

  parameters = {
    "classification" = "csv"
    "typeOfData"     = "file"
  }
}
