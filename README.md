# AWS Lambda by Python

### GETSSM function

1. Usage: Use this func to get parameter stored in AWS SSM Parameters
2. Trigger mechanism: API gateway
    - ssm_allowed_path: set in service role
    - Params:
        - parameterName
        - withDecryption
    - Response:
        - statusCode
        - body {'message','parameter'}
3. Service roles
    - {"ssm:PutParameter","kms:Decrypt","kms:Encrypt","kms:GenerateDataKey""ssm:GetParametersByPath","ssm:GetParameters""ssm:GetParameter"}

### PUTSSM function

1. Usage: Use this func to put new parameter to AWS SSM Parameters
2. Trigger mechanism: API gateway
    - ssm_allowed_path: set in service role
    - Body:
        - parameter_name (String)
        - parameter_value (String)
        - parameter_type (String | StringList | SecureString)
        - overwrite (True | False)
    - Response:
        - statusCode
        - body {'message','version'}
3. Service roles
    - {"ssm:PutParameter",
                "kms:Decrypt",
                "kms:Encrypt",
                "kms:GenerateDataKey",
                "ssm:GetParametersByPath",
                "ssm:GetParameters",
                "ssm:GetParameter"}

### Store Terraform asset function

1. Usage: This func is desgined for automatically analysis and store terraform resources in selected database
2. Trigger mechanism: S3 push event
    - Set Lambda env variables:
        - DB_HOST
        - DB_NAME
        - DB_PASS
        - DB_USER
    - Response:
        - statusCode
        - body {'message'}
3. Service roles
    - {"s3:Get*",
                "s3:List*",
                "s3:Describe*",
                "s3-object-lambda:Get*",
                "s3-object-lambda:List*"}
    - {"logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DescribeSubnets",
                "ec2:DeleteNetworkInterface",
                "ec2:AssignPrivateIpAddresses",
                "ec2:UnassignPrivateIpAddresses"}
