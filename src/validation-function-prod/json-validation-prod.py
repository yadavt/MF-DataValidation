import json
from jsonschema import Draft7Validator
import boto3
import time
from botocore.vendored import requests
import base64


def lambda_handler(event, context):

    # get data from Kinesis Stream
    for record in event['Records']:

       # Kinesis data is base64 encoded so decode here
        payload = base64.b64decode(record["kinesis"]["data"])
        print("Decoded payload: " + str(payload))
        payload = json.loads(payload)

    try:
        typeEvent = payload["type"]
        print(typeEvent)
        schema = {}
        if typeEvent == "page":
            schema = getSchema(payload["name"])
        elif typeEvent == "track":
            schema = getSchema(payload["event"])
        elif typeEvent == "identity":
            schema = getSchema("identity")

        errors = validate(schema, payload)
        if errors:
            errorStr = ""
            for error in errors:
                errorStr = errorStr + \
                    ("Value incorrect at key " +
                     error.path[0] + ". " + error.message + "\n")
            print(errorStr)

            # publish error data to s3
            s3_path = publishS3(errorStr, payload)

            # post error data to slack
            postSlack(errorStr, payload, s3_path)

    except(KeyError):
        print("Cannot find the schema since property is missing. " + str(KeyError))


def getSchema(keyValue):
    # Assign default if empty
    if keyValue == "" or keyValue == None:
        keyValue = "Default"

    # Read from dynamo db that contains schemas
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("JSON_Schemas")

    responsedb = table.get_item(
        Key={"Property": keyValue}
    )
    item = responsedb["Item"]
    schema = json.loads(item["Schema"])
    return schema


def validate(schema, payload):
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    return errors


def postSlack(errorStr, payload, s3_path):

    # Reconstruct message to include the s3 location
    errorStr = "Error in Message ID " + payload["messageId"] + "\n" + errorStr + "\n" + \
        "You can find the details here: https://s3-us-west-2.amazonaws.com/mf-json-validation-errors/" + s3_path

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


def publishS3(errorStr, payload):

    # Write the payload to s3
    encoded_string = (errorStr + str(payload)).encode("utf-8")
    print(encoded_string)
    s3_path = time.strftime("%Y%m%d-" + payload["messageId"])
    s3 = boto3.resource("s3")
    s3.Bucket("mf-json-validation-errors").put_object(Key=s3_path,
                                                      Body=encoded_string)
    return s3_path
