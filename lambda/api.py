import boto3
import csv
import io
import json
import base64

s3 = boto3.client("s3")

def lambda_handler(event, context):
    bucket = "target-data-bucket-6i2caq"
    prefix = "training/"
    page_size = 500  # Número de filas por lote

    # Parsea body JSON del POST
    try:
        body = json.loads(event.get("body", "{}"))
    except Exception:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON body"}),
            "headers": {"Content-Type": "application/json"}
        }

    next_token = body.get("nextToken")

    # Decodifica token si existe
    if next_token:
        decoded = json.loads(base64.b64decode(next_token).decode("utf-8"))
        current_key_index = decoded["key_index"]
        row_offset = decoded["row_offset"]
    else:
        current_key_index = 0
        row_offset = 0

    # Lista objetos CSV
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    keys = [obj["Key"] for obj in response.get("Contents", []) if obj["Key"].endswith(".csv")]

    all_rows = []
    remaining = page_size

    while current_key_index < len(keys):
        key = keys[current_key_index]

        obj_response = s3.get_object(Bucket=bucket, Key=key)
        body = obj_response["Body"].read().decode("utf-8")
        reader = list(csv.DictReader(io.StringIO(body)))

        rows = reader[row_offset:]

        to_take = min(remaining, len(rows))
        all_rows.extend(rows[:to_take])
        remaining -= to_take

        if remaining == 0:
            next_token_payload = {
                "key_index": current_key_index if (row_offset + to_take) < len(reader) else current_key_index + 1,
                "row_offset": row_offset + to_take if (row_offset + to_take) < len(reader) else 0
            }
            next_token = base64.b64encode(json.dumps(next_token_payload).encode("utf-8")).decode("utf-8")
            break

        current_key_index += 1
        row_offset = 0

    return {
        "statusCode": 200,
        "body": json.dumps({
            "data": all_rows,
            "nextToken": next_token if remaining == 0 else None
        }),
        "headers": {
            "Content-Type": "application/json"
        }
    }
