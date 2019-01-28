from __future__ import print_function
import base64
import random
import json
import boto3
import time
from botocore.vendored import requests

def lambda_handler(event, context):
    for record in event['Records']:
       #Kinesis data is base64 encoded so decode here
        payload=base64.b64decode(record["kinesis"]["data"])
        print("Decoded payload: " + str(payload))


    # Set the webhook_url to the one provided by Slack
    webhook_url = 'https://hooks.slack.com/services/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'
    slack_data = {'text': str(payload)}

    response = requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
        )

    if response.status_code != 200:
        raise ValueError(
        'Request to slack returned an error %s, the response is:\n%s'
        % (response.status_code, response.text)
            )

    # Write the payload to s3
    encoded_string=str(payload).encode("utf-8")
    s3_path=time.strftime("%Y%m%d-%H%M%S")

    s3 = boto3.resource("s3")
    s3.Bucket("mf-json-validation-errors").put_object(Key=s3_path, Body=encoded_string)
