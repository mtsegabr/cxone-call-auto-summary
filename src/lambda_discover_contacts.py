import json
import boto3
import datetime as dt
import os
from cxone_client import CxoneClient

DDB_TABLE = os.environ["DDB_TABLE"]
CXONE_SECRET_ID = os.environ["CXONE_SECRET_ID"]
WINDOW_MINUTES = int(os.environ["WINDOW_MINUTES"])
CXONE_BASE_URL = os.environ["CXONE_BASE_URL"]
CXONE_AUTH_URL = os.environ["CXONE_AUTH_URL"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DDB_TABLE)
secrets = boto3.client("secretsmanager")

def _get_secrets():
    raw = secrets.get_secret_value(SecretId=CXONE_SECRET_ID)["SecretString"]
    data = json.loads(raw)
    return data["accessKeyId"], data["accessKeySecret"]

def _already_processed(contact_id):
    return "Item" in table.get_item(Key={"contactId": contact_id})

def lambda_handler(event, context):
    access_id, access_secret = _get_secrets()
    client = CxoneClient(access_id, access_secret, CXONE_BASE_URL, CXONE_AUTH_URL)

    now = dt.datetime.utcnow()
    start = now - dt.timedelta(minutes=WINDOW_MINUTES)

    start_iso = start.replace(microsecond=0).isoformat() + "Z"
    end_iso   = now.replace(microsecond=0).isoformat() + "Z"

    page = 1
    found = []

    while True:
        resp = client.list_completed_contacts(start_iso, end_iso, page=page)
        contacts = resp.get("items", [])

        for c in contacts:
            if c.get("state") == "COMPLETED":
                acd_id = c.get("acdCallId") or c.get("masterContactId")
                if acd_id and not _already_processed(acd_id):
                    found.append(acd_id)

        if not resp.get("nextPage"):
            break
        page += 1

    return {"contactIds": found}