# Create Glue Data Catalog Database
resource "aws_glue_catalog_database" "org_report_database" {
  name         = "org-report"
  location_uri = "s3://${aws_s3_bucket.source-data-bucket.id}/"
}

# Create Glue Crawler
resource "aws_glue_crawler" "org_report_crawler" {
  name          = "org-report-crawler"
  database_name = aws_glue_catalog_database.org_report_database.name
  role          = aws_iam_role.glue_service_role.name
  
  s3_target {
    path = "s3://${aws_s3_bucket.source-data-bucket.bucket}/raw/forest_fire/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.source-data-bucket.bucket}/raw/ndvi/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.source-data-bucket.bucket}/raw/global_climate/"
  }

  s3_target {
    path = "s3://${aws_s3_bucket.source-data-bucket.bucket}/raw/population_density/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
  }
  configuration = <<EOF
{
  "Version":1.0,
  "Grouping": {
    "TableGroupingPolicy": "CombineCompatibleSchemas"
  }
}
EOF
}
resource "aws_glue_trigger" "org_report_trigger" {
  name = "org-report-trigger"
  type = "ON_DEMAND"
  actions {
    crawler_name = aws_glue_crawler.org_report_crawler.name
  }
}