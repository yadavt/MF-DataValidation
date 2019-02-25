#! /usr/bin/env bash

iamRole=""
functionName=""
s3Bucket=""
dbName=""
userName=""
password=""
host=""

# Enter IAM role
while [[ -z "$iamRole" ]]
do
  read -p "Enter IAM role that let's the function access redshift cluster: " iamRole
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

# Enter database name
while [[ -z "$dbName" ]]
do
  read -p "Enter redshift database name: " dbName
done

# Enter database user name
while [[ -z "$userName" ]]
do
  read -p "Enter username for the database: " userName
done

# Enter database password
while [[ -z "$password" ]]
do
  read -p "Enter password for the database: " password
done

# Enter database host name
while [[ -z "$host" ]]
do
  read -p "Enter redshift host name: " host
done

#Get AWS account ID
accountID=$(aws sts get-caller-identity --output text --query 'Account')

#Create deployment package
zip -r9 errorLoad.zip ./package/
zip -g errorLoad.zip errorLoad.py

#Create the lambda fucntion
aws lambda create-function --function-name $functionName \
--zip-file fileb://errorLoad.zip --handler errorLoad.lambda_handler --runtime python3.7 \
--role arn:aws:iam::$accountID:role/$iamRole --timeout 180 \
--environment Variables="{S3_BUCKET=$s3Bucket,DB_NAME=$dbName,HOST=$host,USER=$userName,PASS=$password}"

# Set up the cron rule
aws events put-rule \
--name $functionName \
--schedule-expression 'cron(0 16 1/1 * ? *)'

aws events put-targets --rule $functionName \
--targets "Id"="1","Arn"="arn:aws:lambda:$AWS_DEFAULT_REGION:$accountID:function:$functionName"
