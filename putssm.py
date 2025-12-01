import json
import boto3
from botocore.exceptions import ClientError

ssm_client = boto3.client('ssm')
ssm_allowed_path = '/betterversion/'

def lambda_handler(event, context):
    try:
        name = event.get('parameter_name')
        value = event.get('parameter_value')
        param_type = event.get('parameter_type', 'String') #String, StringList, SecureString
        overwrite = event.get('overwrite', False)

        if not name or value is None:
            return {
                'statusCode': 400,
                'body': json.dumps('Parameter name and value are required.')
            }

        print(f"Storing parameter: {name} with type: {param_type}")

        response = ssm_client.put_parameter(
            Name=ssm_allowed_path + name,
            Value=value,
            Type=param_type,
            Overwrite=overwrite
        )

        print(f"Parameter stored successfully: {response.get('Version')}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Parameter stored successfully',
                'version': response.get('Version')
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
                'body': json.dumps({'message': 'No permission for ssm:PutParameter.'})
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
            'body': json.dumps({'message': 'unidentifier error'})
        }
