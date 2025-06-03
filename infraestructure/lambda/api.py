import boto3
import csv
import io
import uuid
from datetime import datetime, timedelta

s3 = boto3.client("s3")

def lambda_handler(event, context):
    bucket = "target-data-bucket-6i2caq"
    prefix = "training/"
    output_key = f"temp/joined_{uuid.uuid4()}.csv"

    # Inicializa CSV en memoria
    output_csv = io.StringIO()
    writer = None

    paginator = s3.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

    for page in page_iterator:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".csv"):
                obj_response = s3.get_object(Bucket=bucket, Key=key)
                body = obj_response["Body"].read().decode("utf-8")
                reader = csv.DictReader(io.StringIO(body))

                if writer is None:
                    writer = csv.DictWriter(output_csv, fieldnames=reader.fieldnames)
                    writer.writeheader()

                for row in reader:
                    writer.writerow(row)

    # Subir CSV combinado al bucket
    s3.put_object(
        Bucket=bucket,
        Key=output_key,
        Body=output_csv.getvalue(),
        ContentType="text/csv"
    )

    # Generar pre-signed URL (válida por 15 minutos)
    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": output_key},
        ExpiresIn=900  # 15 minutos
    )

    return {
        "statusCode": 200,
        "body": url
    }
