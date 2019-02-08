import boto3
import datetime
import os
from datetime import timedelta


def lambda_handler(event, context):

    # Create connection to redshift data base and get the cursor
    con = psycopg2.connect(
        dbname=os.environ['DB_NAME'],
        host=os.environ['HOST'],
        port=5439,
        user=os.environ['USER'],
        password=os.environ['PASS'])

    cur = con.cursor()

    # Get the S3 files
    s3 = boto3.resource("s3")
    myBucket = s3.Bucket("mf-json-validation-errors")

    # Set the date so that previous day files are extracted
    dayBefore = datetime.date.today() - timedelta(days=1)

    # Select only the previous day files
    s3Files = myBucket.objects.filter(Prefix=dayBefore.strftime("%Y%m%d"))

    # open the file and extract the errors and message
    for object in s3Files:
        file_content = object.get()['Body'].read().decode('utf-8')
        errorMsg, jsonBody = file_content[:file_content.find(
            "{")], file_content[file_content.find("{"):]
        dateVal, messageId = object.key[:object.key.find(
            "-")], object.key[object.key.find("-"):]
        errorArr = errorMsg.split("\n")
        # Insert for every error in the file
        for error in errorArr:
            cur.execute("INSERT INTO errors (datecreated, messageID,errormessage,payload) VALUES (%s,%s,%s,%s)",
                        (dateVal, messageId, error, jsonBody))

    # commit and close database connection
    con.commit()
    cur.close()
    con.close()
