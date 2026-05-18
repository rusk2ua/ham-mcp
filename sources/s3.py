import os

import boto3


def _client():
    return boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))


def list_files(prefix: str) -> list[dict]:
    """List all files under a prefix, recursively, handling pagination.

    S3 has no real folders — keys containing '/' are already returned in a
    single flat list by list_objects_v2 (no Delimiter needed). Pagination
    handles buckets with more than 1,000 objects under the prefix.
    """
    bucket = os.getenv("S3_BUCKET")
    paginator = _client().get_paginator("list_objects_v2")
    results = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            results.append({
                "key": obj["Key"],
                "path": obj["Key"].removeprefix(prefix).lstrip("/"),
                "size": obj["Size"],
            })
    return results


def fetch_file(key: str) -> bytes:
    obj = _client().get_object(Bucket=os.getenv("S3_BUCKET"), Key=key)
    return obj["Body"].read()
