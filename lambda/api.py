import boto3
import csv
import io

s3 = boto3.client("s3")

def lambda_handler(event, context):
    bucket = "target-data-bucket-6i2caq"
    prefix = "training/"

    # Lista los objetos en el prefijo
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    all_data = []

    for obj in response.get("Contents", []):
        key = obj["Key"]
        if key.endswith(".csv"):
            # Descarga el archivo
            obj_response = s3.get_object(Bucket=bucket, Key=key)
            body = obj_response["Body"].read().decode("utf-8")

            # Parsea el CSV
            reader = csv.DictReader(io.StringIO(body))
            for row in reader:
                all_data.append(row)

    return {
        "statusCode": 200,
        "body": all_data
    }
