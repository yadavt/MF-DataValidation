# Sentinel

## Project Idea
An automated quality control service that will help data science and engineering can work together more closely, reducing time spent fixing bugs and manually QAing new data features.  This will be used with Segment (event data service).  It could be used for other data sources as well.

## Overview of the solution
Sentinel solves the following two problems:

### Problem 1:
With every new feature development/UI modification a new page schema is generated and is pushed in the backend to be consumed by the downstream processes. Front end engineers need to make sure that the values being passed are valid and match the specified format and schema type. Sentinel helps the front end developers validate page event schemas, by providing real time feedback on slack, on errors pertaining to properties associated with these newly added features.

### Problem 2:
Sentinel also provides detailed errors in analytical database for production version of the website. These errors can be analyzed by backend engineers and front end developers to make right and corrective actions in pages and/or baseline schemas.

## Setup
Begin by cloning the repository. To setup an instance of Sentinel on your environment, the following needs to be configured:

1. A system that has the ability to capture page events through embedded javascript code and send to downstream process. Here we have used __[Segment](https://segment.com/docs/spec/)__ to stream page events to backend amazon kinesis stream.
  - Configure your javascript source through segment by following the steps as described [here](https://segment.com/docs/sources/website/analytics.js/)

2. __Amazon Kinesis__ is the backbone of the entire system that acts as a messaging buffer to feed the downstream processes(lambda function in our case). The data stream can be connected directly to stream consumers as well. Run the `/setup-scripts/setup-stream.sh` to create a stream. Setup the IAM policy and IAM role as described in the steps [here](https://segment.com/docs/destinations/amazon-kinesis/)

_** If you want to learn more about setting up kinesis streams, this [documentation](https://docs.aws.amazon.com/streams/latest/dev/learning-kinesis-module-one-create-stream.html) gives a good overview._  

3. __Slack__ is configured with lambda to send notifications. To configure a webhook for slack, follow the steps [here](https://api.slack.com/incoming-webhooks#posting_with_webhooks). Capture the webhook url.

4. __S3__ is used to store detailed schema error payloads for further analysis. The production version of errors are stored in S3 and parsed into a redshift table for ad-hoc querying or creating dashboards. Create an s3 bucket that will be used to store all schema errors.  

5. __Dynamo DB__ stores the baseline schemas. `Property` value is the key for unique schema types. Currently the system supports `name`, `event` and `identity` type events. For adding new types modify the code in `json-validation.py`:
```
typeEvent = payload["type"]
    <!-- print(typeEvent) -->
    schema = {}
    if typeEvent == "page":
        schema = getSchema(payload["name"])
    elif typeEvent == "track":
        schema = getSchema(payload["event"])
    elif typeEvent == "identity":
        schema = getSchema("identity")
```
To setup the baseline schemas in dynamo DB, run `setup-dynamoDB.sh `. Verify the table is created via CLI or console. Start adding new schemas per the attributed described above.

6. __Redshift__ stores the parsed error payloads. The redshift cluster should contain `datecreated`, `messageID`, `errormessage` and `payload`. Create a new redshift cluster or use exiting cluster and create a table with schema defined above. Take a note of the VPC, subnet and security group configuration.

7. __Lambda__ functions are the processing engine for sentinel. Before you start setting up the lambda, create two IAM roles:
  - Role to let lambda connect and access kinesis streams, push data to s3 and access dynamo DB. The three policies attached to the role should be:  
  `AmazonS3FullAccess`  
  `AmazonDynamoDBFullAccess`  
  `AWSLambdaKinesisExecutionRole`
  - Role to let lambda access s3 files and push data to redshift. The two policies attached should be:  
  `AmazonS3ReadOnlyAccess`  
  `AWSLambdaVPCAccessExecutionRole`

There are three Lambda functions is to accomplish the following tasks:
 - `json-validation.py` does the validation of input schema against baseline schema stored in DynamoDB, in _test environment_ and pushes the messages to S3 and slack respectively. To setup the corresponding function go to the `src/validation-function` directory. Then run `. ../setup-scripts/setup-testenv-lambda.sh `. Go to the console and validate the function created and test it with this sample payload:
 ```
 {
  "Records": [
    {
      "kinesis": {
        "kinesisSchemaVersion": "1.0",
        "partitionKey": "1",
        "sequenceNumber": "49590338271490256608559692538361571095921575989136588898",
        "data": "eyAiX21ldGFkYXRhIjogeyAiYnVuZGxlZCI6IFsgIkFtcGxpdHVkZSIsICJTZWdtZW50LmlvIiwgIlZpc3VhbCBXZWJzaXRlIE9wdGltaXplciIgXSwgInVuYnVuZGxlZCI6IFtdIH0sICJhbm9ueW1vdXNJZCI6ICJjM2FlZmVjOS0yZGZmLTRmZTAtODg3OC05MTkzNzRjMzU2ZWEiLCAiY2F0ZWdvcnkiOiBudWxsLCAiY2hhbm5lbCI6ICJjbGllbnQiLCAiY29udGV4dCI6IHsgImFtcCI6IHsgImlkIjogImFtcC00bmJfaWNDbFZZc29Oc2R2TnBodHZ3IiB9LCAiaXAiOiAiMTU3LjEzMC4yMTIuNiIsICJsaWJyYXJ5IjogeyAibmFtZSI6ICJhbmFseXRpY3MuanMiLCAidmVyc2lvbiI6ICIzLjcuMiIgfSwgInBhZ2UiOiB7ICJwYXRoIjogIi9sc2FwcC9wb2xpY3ktdHlwZSIsICJyZWZlcnJlciI6ICJodHRwOi8vbG9jYWxob3N0OjQyMDAvbHNhcHAvcG9saWN5LXR5cGUiLCAic2VhcmNoIjogIiIsICJ0aXRsZSI6ICJNYXNvbiBGaW5hbmNlIC0gTGlmZSBTZXR0bGVtZW50IEVzdGltYXRlIiwgInVybCI6ICJodHRwOi8vbG9jYWxob3N0OjQyMDAvbHNhcHAvcG9saWN5LXR5cGUiIH0sICJ1c2VyQWdlbnQiOiAiTW96aWxsYS81LjAgKE1hY2ludG9zaDsgSW50ZWwgTWFjIE9TIFggMTBfMTFfNikgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzcxLjAuMzU3OC45OCBTYWZhcmkvNTM3LjM2IiB9LCAiaW50ZWdyYXRpb25zIjoge30sICJtZXNzYWdlSWQiOiAiYWpzLTUxM2I3NThkODljYTAzZGFjNDYyYzYzMzU2YmRlYzIyIiwgIm5hbWUiOiAiUG9saWN5IFR5cGUiLCAib3JpZ2luYWxUaW1lc3RhbXAiOiAiMjAxOS0wMS0yNVQxOTo1Mjo0My40MzZaIiwgInByb2plY3RJZCI6ICJDWTlBeWExOWQyIiwgInByb3BlcnRpZXMiOiB7ICJhZGRpdGlvbmFsX2hlYWx0aF9zdGF0dXMiOiBbXSwgImFnZSI6ICI4MCIsICJlbWFpbCI6ICIiLCAiZnVubmVsIjogImxzYXBwIiwgImdlbmRlciI6ICJ0YXJ1biIsICJoZWFsdGhfc3RhdHVzIjogIiIsICJsYW5kaW5nUGFnZSI6IGZhbHNlLCAibWFzb25VVUlEIjogIjA3MGVlZGQ2LTQxN2EtNGEyMC1iYTczLTNlZTAgYWY0ZTU0NmIiLCAibmFtZSI6ICJQb2xpY3kgVHlwZSIsICJwYXRoIjogIi9sc2FwcC9wb2xpY3ktdHlwZSIsICJwb2xpY3lfZmFjZV92YWx1ZSI6ICI5MDAwMDAwMCIsICJwb2xpY3lfdHlwZSI6ICIiLCAicHJldmlvdXNQYWdlIjogIi9sc2FwcC9wb2xpY3ktc2l6ZSIsICJyZWZlcnJlciI6ICJodHRwOi8vbG9jYWxob3N0OjQyMDAvbHNhcHAvcG9saWN5LXR5cGUiLCAic2VhcmNoIjogIiIsICJzdGF0ZSI6ICIiLCAidGVybV9jb252ZXJ0cyI6ICIiLCAidGl0bGUiOiAiTWFzb24gRmluYW5jZSAtIExpZmUgU2V0dGxlbWVudCBFc3RpbWF0ZSIsICJ1cmwiOiAiaHR0cDovL2xvY2FsaG9zdDo0MjAwL2xzYXBwL3BvbGljeS10eXBlIiwgIndpZGdldF90cmFmZmljIjogZmFsc2UgfSwgInJlY2VpdmVkQXQiOiAiMjAxOS0wMS0yNVQxOTo1Mjo0My41NDJaIiwgInNlbnRBdCI6ICIyMDE5LTAxLTI1VDE5OjUyOjQzLjQ2MFoiLCAidGltZXN0YW1wIjogIjIwMTktMDEtMjVUMTk6NTI6NDMuNTE4WiIsICJ0eXBlIjoicGFnZSIsICJ1c2VySWQiOiIxMzcwIiwgInZlcnNpb24iOiIyIiB9",
        "approximateArrivalTimestamp": 1545084650.987
      },
      "eventSource": "aws:kinesis",
      "eventVersion": "1.0",
      "eventID": "shardId-000000000006:49590338271490256608559692538361571095921575989136588898",
      "eventName": "aws:kinesis:record",
      "invokeIdentityArn": "arn:aws:iam::123456789012:role/lambda-kinesis-role",
      "awsRegion": "us-west-2",
      "eventSourceARN": "arn:aws:kinesis:us-east-2:123456789012:stream/lambda-stream"
    }
  ]
}
```
 - `json-validation-prod.py` does the validation of input schema against baseline schema stored in DynamoDB, in _prod environment_ and pushes the messages to S3. To setup the corresponding function go to the `src/validation-function-prod` directory. Then run `. ../setup-scripts/setup-prodenv-lambda.sh `. Verify and test similar to the test environment lambda.
 - `errorLoad.py` does the parsing of errors pushed in S3 and pushes the data into redshift cluster. To setup the corresponding function go to the `src/errorLoad` directory. Then run `. ../setup-scripts/setup-dailyjob-lambda`. Modify the lambda function to have the same vpc, subnet and security configuration as the redshift cluster. Verify and test the function.

## Architecture
![Architecture](Arch.png)

## Demo
![Alt Text](/images/demo.gif)
