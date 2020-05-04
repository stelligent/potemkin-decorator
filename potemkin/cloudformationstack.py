"""
CloudFromationStack decorator
"""
import time
import os
import boto3
from botocore.exceptions import WaiterError


class CloudFormationStack:
    """Decorator that spins up a CloudFormation stack for initial conditions, then tears it down after test """

    def __init__(self,
                 relative_path_to_initial_condition_cfn_template,
                 stack_name_stem=None,
                 parameters=None,
                 aws_profile=None,
                 teardown=True,
                 teardown_fail=True,
                 timeout=5):
        """ Constructor

        :param relative_path_to_initial_condition_cfn_template: The relative path/name to the CloudFormation template to create.
        :param stack_name_stem: CloudFormation stack name stem.  Combined with a timestamp to produce full stack name.
        :param parameters: Parameters to pass to CloudFormation.
        :param aws_profile: The aws profile to use. If None, uses current environment.
        :param teardown: Teardown resources after test completion. (default True)
        :param teardown_fail: Teardown resources after tests complete with one or more failure. If False, overrides teardown. (default True)
        :param timeout: Cloudformation and Config Waiter timeout in minutes (default 5)"""
        self._relative_path_to_initial_condition_cfn_template = relative_path_to_initial_condition_cfn_template
        self._stack_name = stack_name_stem
        self._aws_profile = aws_profile
        self._parameters = parameters
        if parameters is None:
            self._parameters = {}
        self._cloudformation_client = None
        self._teardown = teardown
        self._teardown_fail = teardown_fail
        self._timeout = timeout

    def __call__(self, user_defined_test_function):
        """ The heart of the matter to spin up the stack, invoke the pytest function and then teardown """
        def decorated_test_function():
            with open(self._resolve_template_path(), 'r') as initial_condition_cfn_template_file:
                initial_condition_cfn_template_content = initial_condition_cfn_template_file.read()

            qualified_stack_name = self._unique_stack_name(self._stack_name)

            stack_outputs = self._create_stack(
                stack_name=qualified_stack_name,
                parameters=self._parameters,
                template_body=initial_condition_cfn_template_content
            )


            try:
                user_defined_test_function(stack_outputs, qualified_stack_name)
            except Exception as error:
                print(error)
                if self._teardown and self._teardown_fail:
                    self._delete_stack(stack_name=qualified_stack_name)
                raise

            if self._teardown:
                self._delete_stack(
                    stack_name=qualified_stack_name
                )

        return decorated_test_function

    def _cloudformation(self):
        """ The boto client to interface with cloudformation service """
        if not self._cloudformation_client:
            if self._aws_profile:
                session = boto3.session.Session(profile_name=self._aws_profile)
                self._cloudformation_client = session.client('cloudformation')
            else:
                self._cloudformation_client = boto3.client('cloudformation')

        return self._cloudformation_client

    def _filter_stack_resources(self, stack_name, resource_status):
        """ filter stack resources for a given resource status

        :param resource_status: resource_status to show
        """
    
        response = ''
        cloudformation = self._cloudformation()
        stack_resources = cloudformation.describe_stack_resources(StackName=stack_name)
        for resource in stack_resources["StackResources"]:
            if resource["ResourceStatus"] == resource_status:
                response += f'  {resource["LogicalResourceId"]}: {resource.get("ResourceStatusReason", "")}\n'
        return response
            

    def _stack_outputs(self, stack_name):
        """ Transform results of DescribeStacks outputs into a dictionary

        :param stack_name: stack name
        """
        cloudformation = self._cloudformation()
        describe_stacks_response = cloudformation.describe_stacks(StackName=stack_name)
        stack_dict = describe_stacks_response['Stacks'][0]
        
        if stack_dict["StackStatus"] == "CREATE_IN_PROGRESS":
            events = self._filter_stack_resources(stack_name, 'CREATE_IN_PROGRESS')
            print('Stack timed out before creation was completed. Increase the timeout value on @potemkin.CloudFormationStack')
            print(f'Resources that are still in progress:\n{events}')
            raise Exception("StackTimeoutError")
        elif stack_dict["StackStatus"] != "CREATE_COMPLETE":
            events = self._filter_stack_resources(stack_name, 'CREATE_FAILED')
            print(f'Stack creation error: {stack_dict.get("StackStatusReason", "no reason given")}')
            print(f'Resource creation error details:\n{events}')
            raise Exception("StackCreationError")
        return {
            output['OutputKey']: output['OutputValue']
            for output in stack_dict['Outputs']
        }


    def _convert_parameters(self, parameters):
        """ Convert regular dictionary into array of Parameters for call to CreateStack
        :param parameters: regular dictionary of parameters """
        return [
            {
                'ParameterKey': k,
                'ParameterValue': v
            }
            for k, v in parameters.items()
        ]

    def _waiter_config(self):
        """ stock waiter config to use for all calls to CloudFormation service """
        return {
            'Delay': 20,
            'MaxAttempts': self._timeout * 3
        }

    def _delete_stack(self, stack_name):
        """ Call DeleteStack and wait for completion

        :param stack_name: name of stack to delete """
        cloudformation = self._cloudformation()
        _ = cloudformation.delete_stack(
            StackName=stack_name
        )

        waiter = cloudformation.get_waiter('stack_delete_complete')
        waiter.wait(
            StackName=stack_name,
            WaiterConfig=self._waiter_config()
        )

    def _create_stack(self, stack_name, parameters, template_body):
        """ Call CreateStack and wait for completion

        :param stack_name: name of stack to create from template
        :param parameters: dict of parameters for stack
        :param template_body: yml or json of cfn template
        :returns: dictionary of outputs """
        cloudformation = self._cloudformation()
        _ = cloudformation.create_stack(
            StackName=stack_name,
            TemplateBody=template_body,
            Parameters=self._convert_parameters(parameters),
            TimeoutInMinutes=self._timeout,
            Capabilities=[
                'CAPABILITY_NAMED_IAM',
                'CAPABILITY_AUTO_EXPAND'
            ],
            OnFailure='DO_NOTHING'
        )
        waiter = cloudformation.get_waiter('stack_create_complete')
        try:
            waiter.wait(
                StackName=stack_name,
                WaiterConfig=self._waiter_config()
            )
        except WaiterError:
            pass

        return self._stack_outputs(stack_name)
        
    def _resolve_template_path(self):
        """ Current wd + relative path """
        return os.path.join(
            os.getcwd(),
            self._relative_path_to_initial_condition_cfn_template
        )

    def _unique_stack_name(self, stack_name_stem):
        """ Generate unique stack name based upon stem and epoch time

        :param stack_name_stem: first part of stack name to generate """
        return f"{stack_name_stem}{self._now()}"

    def _now(self):
        """ Integer format of current time """
        return int(round(time.time()))
