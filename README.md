The potemkin decorator allows standing up AWS resources in the form of a Cloudformation template.
For "integration testing" boto code with AWS, this allows for a convenient way to setup initial conditions
instead of having to develop boto code that is likely as complex as the "code under test".

## Basic Usage

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
def test_bucket_has_aes256_encryption(stack_outputs, stack_name):
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

## Service Specific Usage

The potemkin decorator has additional functions for interacting with specific AWS services 

### AWS Config ###
AWS Config initiates evaluations when a resource is created, but the evaluations are completed
asynchronously. They can take several minutes to complete. The AWS config functions wait until 
the config rule has an evaluation for the resource, then returns the evaluation.

#### config_rule_wait_for_resource ####
This function polls aws config until there is an evaluation for the resource, then returns it. Use this 
function for config rules with a configuration change trigger.

```
import potemkin
import boto3


@potemkin.CloudFormationStack(
  'test/integration/test_templates/aes256_bucket.yml',
  stack_name_stem='TestStack',
  parameters={'BucketName': 'unclefreddie33388'}
)
def test_bucket_encryption_rule(stack_outputs, stack_name):
  configservice = boto3.Session().client('config')

  results = config_rule_wait_for_resource(configservice, 
                                          resource_id='unclefreddie33388', 
                                          rule_name='config-rule-s3-encryption')
  
  assert results['ComplianceType'] == 'NON_COMPLIANT'
``` 


#### evaluate_config_rule_and_wait_for_resource ####
This is similar to config_rule_wait_for_resource but it first initiates a config evaluation. Use this 
for config rules with a periodic trigger.

```
import potemkin
import boto3


@potemkin.CloudFormationStack(
  'test/integration/test_templates/aes256_bucket.yml',
  stack_name_stem='TestStack',
  parameters={'BucketName': 'unclefreddie33388'}
)
def test_bucket_encryption_rule(stack_outputs, stack_name):
  configservice = boto3.Session().client('config')

  results = evaluate_config_rule_and_wait_for_resource(configservice, 
                                                      resource_id='unclefreddie33388', 
                                                      rule_name='config-rule-s3-encryption')
  
  assert results['ComplianceType'] == 'NON_COMPLIANT'
``` 