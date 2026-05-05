import boto3
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def upload_raw_files():
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    bucket = os.getenv('AWS_BUCKET_NAME')
    raw_path = Path('data/raw')

    files = list(raw_path.glob('*.csv'))
    print(f'Found {len(files)} CSV files to upload\n')

    for file in sorted(files):
        print(f'Uploading {file.name}...')
        s3.upload_file(str(file), bucket, f'raw/{file.name}')
        print(f'  Uploaded to s3://{bucket}/raw/{file.name}')

    print(f'\nAll {len(files)} files uploaded successfully.')

if __name__ == '__main__':
    upload_raw_files()