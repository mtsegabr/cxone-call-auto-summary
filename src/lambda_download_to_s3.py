import json
import os
import urllib.request
import hashlib
import boto3

S3_BUCKET = os.environ["S3_BUCKET"]
DDB_TABLE = os.environ["DDB_TABLE"]

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DDB_TABLE)

def lambda_handler(event, context):
    contact_id = event["contactId"]
    file_url = event["fileUrl"]

    key = f"cxone/{contact_id}.wav"

    try:
        with urllib.request.urlopen(file_url, timeout=120) as resp:
            audio_bytes = resp.read()
    except Exception as e:
        return {"status": "error", "error": str(e)}

    etag = hashlib.md5(audio_bytes).hexdigest()

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=audio_bytes,
        ContentType="audio/wav",
        Metadata={"contactId": contact_id, "md5": etag}
    )

    table.put_item(Item={
        "contactId": contact_id,
        "s3Key": key,
        "status": "stored"
    })

    return {"status": "uploaded", "s3Key": key}