import logging
import boto3
from botocore.exceptions import ClientError
import os

s3 = boto3.resource('s3')

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return f'Successfully uploaded {file_name} to S3 bucket {bucket}/{object_name}'


def list_files(bucket,prefix=''):
    """ List files from an S3 bucket, optionally match a file prefix

    :param bucket: Bucket name to list files from
    :param prefix: File prefix filter (optional)
    :return: List of files
    """

    # create session
    session = boto3.Session()
    s3 = session.resource('s3')
    search_bucket = s3.Bucket(bucket)
    
    # create list of matching files
    files = []
    try:
        for i in search_bucket.objects.filter(Prefix=prefix):
            files.append(i.key)
    except ClientError as e:
        logging.error(e)
        return False
    return files