#! /usr/bin/env bash

iamRole=""
functionName=""
s3Bucket=""
webhookURL=""
streamName=""

# Enter IAM role
while [[ -z "$iamRole" ]]
do
  read -p "Enter IAM role that let's the function access kinesis streams: " iamRole
done

# Enter function name
while [[ -z "$functionName" ]]
do
  read -p "Enter function name: " functionName
done

# Enter function name
while [[ -z "$s3Bucket" ]]
do
  read -p "Enter S3 bucket name: " s3Bucket
done

# Enter webhook url
while [[ -z "$webhookURL" ]]
do
  read -p "Enter Slack webhook url: " webhookURL
done

# Enter Kinesis stream name
while [[ -z "$streamName" ]]
do
  read -p "Enter kinesis stream name to connect to Lambda: " streamName
done

#Get AWS account ID
accountID=$(aws sts get-caller-identity --output text --query 'Account')

#Create deployment package
zip -r9 json-validation-prod.zip ../package/
zip -g json-validation-prod.zip json-validation-prod.py

#Create the lambda fucntion
aws lambda create-function --function-name $functionName \
--zip-file fileb://json-validation-prod.zip --handler json-validation-prod.lambda_handler --runtime python3.7 \
--role arn:aws:iam::$accountID:role/$iamRole --environment Variables="{S3_BUCKET=$s3Bucket,WEBHOOK_URL=$webhookURL}"

#Connect to kinesis stream
aws lambda create-event-source-mapping --function-name $functionName \
--event-source  arn:aws:kinesis:$AWS_DEFAULT_REGION:$accountID:stream/$streamName \
--batch-size 100 --starting-position LATEST
