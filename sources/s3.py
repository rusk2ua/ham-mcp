import os

import boto3


def _client():
    return boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))


def list_files(prefix: str) -> list[dict]:
    resp = _client().list_objects_v2(Bucket=os.getenv("S3_BUCKET"), Prefix=prefix)
    return [{"key": o["Key"], "size": o["Size"]} for o in resp.get("Contents", [])]


def fetch_file(key: str) -> bytes:
    obj = _client().get_object(Bucket=os.getenv("S3_BUCKET"), Key=key)
    return obj["Body"].read()
