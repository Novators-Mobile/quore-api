import boto3, io
from os import environ

s3_client = boto3.client(endpoint_url="http://s3:8000",
                            aws_access_key_id='quoreapi',
                            aws_secret_access_key=environ["S3_SECRET"],
                            service_name='s3')
host = "novatorsmobile.ru/s3"

def upload_avatar(file: bytes, id: str | int):
    s3_client.create_bucket(Bucket="avatars")
    s3_client.upload_fileobj(io.BytesIO(file), "avatars", str(id) + '.png')

def get_avatar(id: str | int):
    return s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': 'avatars',
                                                            'Key': str(id) + '.png'},
                                                    ExpiresIn=60).replace('s3:8000', host)

def delete_avatar(id: str | int):
    s3_client.delete_object(Bucket="avatars", Key=str(id) + '.png')

def upload_image(file: bytes, id: str | int, count = int):
    s3_client.create_bucket(Bucket="gallery")
    s3_client.upload_fileobj(io.BytesIO(file), "gallery", str(id) + '_' + str(count) + '.png')    

def get_images(filenames: list):
    return list(map(lambda name: s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': 'gallery',
                                                            'Key': name},
                                                    ExpiresIn=60).replace('s3:8000', host), filenames))

def delete_image(filename: str):
    s3_client.delete_object(Bucket="gallery", Key=filename)

def delete_all_images(filenames: list):
    map(lambda name: s3_client.delete_object(Bucket="gallery", Key=name), filenames)