import json
import boto3
from botocore.exceptions import ClientError
import datetime

ssm_client = boto3.client('ssm')
ssm_allowed_path = '/betterversion/'

def lambda_handler(event, context):
    try:
        query_params = event.get('queryStringParameters', {})
        name = query_params.get('parameterName')
        with_decryption = query_params.get('withDecryption', False)

        if not name:
            return {
                'statusCode': 400,
                'body': json.dumps('Parameter name is required.')
            }

        print(f"Getting parameter: {name}")

        response = (ssm_client.get_parameter(
            Name=ssm_allowed_path + name,
            WithDecryption=with_decryption
        )).get('Parameter')

        if isinstance(response.get('LastModifiedDate'), datetime.datetime):
            response['LastModifiedDate'] = response['LastModifiedDate'].isoformat()

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Parameter retrieved successfully',
                'parameter': response
            })
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ParameterAlreadyExists':
            print(f"Error: Parameter '{name}' existed and overwrite=false.")
            return {
                'statusCode': 409,
                'body': json.dumps({'message': f"Parameter '{name}' existed. Set overwrite=true for overide."})
            }
        elif error_code == 'AccessDeniedException':
             print(f"Error: Access denied. Check IAM Role")
             return {
                'statusCode': 403,
                'body': json.dumps({'message': 'No permission for ssm:GetParameter.'})
            }
        else:
            print(f"Unidentifier from ClientError: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': f"Error from AWS: {error_code}"})
            }

    except Exception as e:
        print(f"Unidentifier error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': "unidentifier error {e}"})
        }
