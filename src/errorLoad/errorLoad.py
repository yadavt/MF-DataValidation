import psycopg2

def lambda_handler(event, context):
    # TODO implement
    con = psycopg2.connect(
    dbname="schemaerrors",
    host="10.0.0.17",
    port= 5439,
    user="admin",
    password="MasonFinance22")

    cur = con.cursor()
