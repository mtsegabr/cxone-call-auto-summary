import json
import os
import boto3
from cxone_client import CxoneClient

CXONE_SECRET_ID = os.environ["CXONE_SECRET_ID"]
CXONE_BASE_URL  = os.environ["CXONE_BASE_URL"]
CXONE_AUTH_URL  = os.environ["CXONE_AUTH_URL"]

secrets = boto3.client("secretsmanager")

def _get_secrets():
    raw = secrets.get_secret_value(SecretId=CXONE_SECRET_ID)["SecretString"]
    data = json.loads(raw)
    return data["accessKeyId"], data["accessKeySecret"]

def lambda_handler(event, context):
    contact_id = event["contactId"]

    access_id, access_secret = _get_secrets()
    client = CxoneClient(access_id, access_secret, CXONE_BASE_URL, CXONE_AUTH_URL)

    meta = client.get_playback_metadata(contact_id)
    file_url = meta.get("fileToPlayUrl")

    if not file_url:
        details = client.get_contact_details(contact_id)
        file_url = (details.get("media") or {}).get("fileToPlayUrl")

    if not file_url:
        return {"ready": False, "contactId": contact_id}

    return {"ready": True, "contactId": contact_id, "fileUrl": file_url}