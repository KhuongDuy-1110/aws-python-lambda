import json
import traceback
import pymysql
import os
import sys
import boto3

DB_HOST = os.environ['DB_HOST']
DB_USER = os.environ['DB_USER']
DB_PASS = os.environ['DB_PASS']
DB_NAME = os.environ['DB_NAME']

try:
    db_connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        connect_timeout=5,
        autocommit=True
    )
except pymysql.MySQLError as e:
    print(e)
    sys.exit(1)

print("Success: connect to mysql successfully")


def lambda_handler(event, context):
    try:
        # check db connection
        db_connection.ping(reconnect=True)

        # process new S3 event
        print("Received event:", json.dumps(event))
        s3_event = event['Records'][0]['s3']
        bucket_name = s3_event['bucket']['name']
        object_key = s3_event['object']['key']
        if 'apply-events/' in object_key:
            print(f'Processing APPLY event for {object_key}')
            process_apply(bucket_name, object_key)

        elif 'destroy-events/' in object_key:
            print(f'Processing DESTROY event for {object_key}')
            process_destroy(bucket_name, object_key)

    except pymysql.MySQLError as e:
        print("Lose connection")

    return {
        'statusCode': 200,
        'body': json.dumps('Modify database service successfully !')
    }

def process_apply(bucket_name, object_key):

    print(f"Fetching S3 object {object_key} from bucket {bucket_name}...")
    try:
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read().decode('utf-8')
        data = json.loads(content)
    except Exception as e:
        print(f"Error fetching S3 object {object_key} from bucket {bucket_name}: {e}")
        return

    services_data = []
    service_ids = []
    for key, value in data.items():
        try:
            record_data = value.get('value')
            if not record_data:
                print(f"Ignore {key}: no 'value' block.")
                continue

            service_id = record_data.get('service_id')
            if not service_id:
                print(f"Ignore {key}: no 'service_id' found.")
                continue

            services_data.append((
                key,
                record_data.get('public_ip'),
                record_data.get('private_ip'),
                record_data.get('service_id'),
                record_data.get('status'),
                record_data.get('additional_information'),
                record_data.get('created_at'),
                record_data.get('updated_at')
            ))
            service_ids.append(record_data.get('service_id'))
        except Exception as e:
            print(f"Error processing for {key}: {e}")

    if not services_data:
        print("No valid records to process.")
        return

    # bulk insert or update services
    print(f"Prepare to process {len(services_data)} records...")
    insertedSql = """
        INSERT INTO services
            (name, public_ip, private_ip, service_id, status, additional_information, created_at, updated_at)
        VALUES
            (%s, %s, %s, %s, %s, %s, COALESCE(%s, NOW() + INTERVAL 7 HOUR), COALESCE(%s, NOW() + INTERVAL 7 HOUR))
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            public_ip = VALUES(public_ip),
            private_ip = VALUES(private_ip),
            status = VALUES(status),
            additional_information = VALUES(additional_information),
            updated_at = NOW() + INTERVAL 7 HOUR;
    """
    try:
        with db_connection.cursor() as cursor:
            cursor.executemany(insertedSql, services_data)

        db_connection.commit()

        print(f"Success! Processed {len(services_data)} records.")

    except Exception as e:
        print("Error: SQL Transaction failed. Rolling back...")
        print(traceback.format_exc())
        try:
            db_connection.rollback()
        except Exception as rb_e:
            print(f"Error while rolling back: {rb_e}")

    # update other status services to 2 (deleted)
    placeholders = ','.join(['%s'] * len(service_ids))
    updatedSql = f"""
        UPDATE services
        SET status = 2, updated_at = NOW() + INTERVAL 7 HOUR
        WHERE service_id NOT IN ({placeholders})
    """
    try:
        with db_connection.cursor() as cursor:

            cursor.execute(updatedSql, service_ids)

            affected_rows = cursor.rowcount
            print(f"Successfully updated {affected_rows} rows.")
            db_connection.commit()

    except Exception as e:
        print(f"An error occurred: {e}")
        db_connection.rollback()

def process_destroy(bucket_name, object_key):
    print(f"Destroy processing for {object_key} in {bucket_name} is not implemented yet.")

    destroySql = f"""
        UPDATE services
        SET status = 2, updated_at = NOW() + INTERVAL 7 HOUR
        WHERE status = 1
    """
    try:
        with db_connection.cursor() as cursor:

            cursor.execute(destroySql)

            affected_rows = cursor.rowcount
            print(f"Successfully updated {affected_rows} rows.")
            db_connection.commit()

    except Exception as e:
        print(f"An error occurred: {e}")
        db_connection.rollback()
