The potemkin decorator allows standing up AWS resources in the form of a Cloudformation template.
For "integration testing" boto code with AWS, this allows for a convenient way to setup initial conditions
instead of having to develop boto code that is likely as complex as the "code under test".

Here is an example invocation from pytest:
```
import potemkin
import boto3


@potemkin.CloudFormationStack(
  'test/integration/test_templates/aes256_bucket.yml',
  stack_name_stem='TestStack',
  parameters={'BucketName': 'unclefreddie33388'},
  aws_profile='myprofile',
  teardown=False
)
def test_bucket_has_aes256_encryption(stack_outputs):
  full_bucket_name = stack_outputs['BucketNameOut']

  s3 = boto3.Session(profile_name='myprofile').client('s3')
  get_bucket_encryption_response = s3.get_bucket_encryption(
    Bucket=full_bucket_name
  )

  assert get_bucket_encryption_response['ServerSideEncryptionConfiguration']['Rules'][0]['ApplyServerSideEncryptionByDefault']['SSEAlgorithm'] == 'AES256'
``` 

The CloudFormationStack creates the stack and binds the outputs to stack_outputs.  The pytest method
could invoke more boto code to manipulate the resources created by the decorator.  In this case,
the test just asserts that the initial condition is what is expected.

This is basically a python/pytest port of "aws-int-test-rspec-helper" that worked with Ruby/RSpec:
* https://github.com/stelligent/aws-int-test-rspec-helper/
