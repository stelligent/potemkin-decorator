import potemkin
import boto3


@potemkin.CloudFormationStack(
  'test/integration/test_templates/aes256_bucket.yml',
  stack_name_stem='TestStack',
  parameters={'BucketName': 'unclefreddie33388'},
  teardown=False
)
def test_bucket_has_aes256_encryption(stack_outputs, stack_name):
  full_bucket_name = stack_outputs['BucketNameOut']

  s3 = boto3.Session().client('s3')
  get_bucket_encryption_response = s3.get_bucket_encryption(
    Bucket=full_bucket_name
  )

  assert get_bucket_encryption_response['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm'] == 'AES256'
