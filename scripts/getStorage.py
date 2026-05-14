#!/usr/bin/env python3

from google.cloud import storage

storage_client = storage.Client()
blobs = storage_client.list_blobs(bucket_or_name="fc-b11e4c02-3d65-4372-ae65-cbfb3709a3b9/submissions")

for blob in blobs:
    print(blob)
    print(blob.size)