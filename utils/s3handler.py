import boto3

def read_file_from_s3(bucket_name, file_key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=file_key)
    content = obj['Body'].read().decode('utf-8')
    
    return content