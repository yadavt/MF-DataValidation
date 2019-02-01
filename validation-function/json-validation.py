from __future__ import print_function
import base64
import json
import boto3
import time
from botocore.vendored import requests
from jsonschema import Draft3Validator

def lambda_handler(event, context):
    for record in event['Records']:
       #Kinesis data is base64 encoded so decode here
        payload=base64.b64decode(record["kinesis"]["data"])
        print("Decoded payload: " + str(payload))
        payload=json.loads(payload)

    #Read from dynamo db that contains schemas
    dynamodb=boto3.resource("dynamodb")
    table=dynamodb.Table("JSON_Schemas")

    if not payload["name"]:
        responsedb= table.get_item(
            Key={
                "Property" :"Default"
            }
        )
    else:
        responsedb= table.get_item(
            Key={
                "Property" :payload["name"]
            }
        )
    item= responsedb["Item"]
    schema=item["Schema"]
    schema=json.loads(schema)

    v=Draft3Validator(schema)
    errors = sorted(v.iter_errors(payload), key=lambda e: e.path)

    if errors:
        #Construct error string
        errorStr=""
        for error in errors:
            errorStr=errorStr+("Value incorrect at key " + error.path[0] + ". " +error.message +"\n")

        # Write the payload to s3
        encoded_string=(errorStr+str(payload)).encode("utf-8")
        print(encoded_string)
        s3_path=time.strftime("%Y%m%d-"+payload["messageId"])
        s3 = boto3.resource("s3")
        s3.Bucket("mf-json-validation-errors").put_object(Key=s3_path, Body=encoded_string)

        #Reconstruct message for slack
        errorStr="Error in Message ID "+ payload["messageId"] +"\n"+ errorStr +"\n"+"You can find the details here: https://s3-us-west-2.amazonaws.com/mf-json-validation-errors/"+ s3_path

        # Set the webhook_url to the one provided by Slack
        webhook_url = 'https://hooks.slack.com/services/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'
        slack_data = {'text': str(errorStr)}

        response = requests.post(
            webhook_url, data=json.dumps(slack_data),
            headers={'Content-Type': 'application/json'}
            )

        if response.status_code != 200:
            raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s'
            % (response.status_code, response.text)
                )
