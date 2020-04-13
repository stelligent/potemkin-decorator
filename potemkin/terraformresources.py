"""
TerraformResources decorator
"""
import time
import os
import subprocess
import json
import boto3


class TerraformResources:
    """Decorator that creates infrastructure via terraform apply for initial conditions, then tears it down after test """

    def __init__(self,
                 relative_path_to_terraform_root,
                 parameters=None,
                 aws_profile=None,
                 teardown=True,
                 teardown_fail=True):
        """ Constructor

        :param relative_path_to_terraform_root: directory containing terraform code.
        :param parameters: Parameters to pass to terraform (requires variable block in terraform).
        :param aws_profile: The aws profile to use. If None, uses current environment.
        :param teardown: Teardown resources after test completion. (default True)
        :param teardown_fail: Teardown resources after tests complete with one or more failure. If False, overrides teardown (default True)"""

        self._relative_path_to_terraform_root = relative_path_to_terraform_root
        self._aws_profile = aws_profile
        self._parameters = parameters if parameters else {}
        self._teardown = teardown
        self._teardown_fail = teardown_fail

    def __call__(self, user_defined_test_function):
        """ The heart of the matter to create the resources, invoke the pytest function and then destroy """

        def decorated_test_function():
            os.chdir(self._relative_path_to_terraform_root)
            self._terraform('init')
            self._terraform_apply()

            try:
                user_defined_test_function(
                    tf_outputs=self._terraform_outputs())
            except Exception as error:
                print(error)
                self._teardown = self._teardown_fail if not self._teardown_fail else self._teardown
                if self._teardown:
                    self._terraform('destroy -auto-approve')
                raise

            if self._teardown:
                self._terraform('destroy -auto-approve')

        return decorated_test_function

    def _terraform_apply(self):
        """ Create terraform apply command with parameters """
        vars = ''
        for param in self._parameters:
            vars += f' -var {param}={self._parameters[param]}'
        command = f'apply -auto-approve{vars}'
        self._terraform(command)

    def _terraform_outputs(self):
        """ Get terraform outputs and convert to dict """
        response = self._terraform('output -json')
        output_dict = json.loads(response)
        return {var: output_dict[var]["value"] for var in output_dict}

    def _terraform(self, command):
        """ Run terraform command, adding AWS_PROFILE to environment if aws_profile is specified """

        tf_env = os.environ.copy()
        if self._aws_profile:
            tf_env["AWS_PROFILE"] = self._aws_profile

        full_command = f'terraform {command}'
        response = subprocess.run(full_command.split(" "),
                                  stdout=subprocess.PIPE,
                                  env=tf_env)
        stdout = response.stdout.decode("utf-8") if response.stdout else ''
        stderr = response.stderr.decode("utf-8") if response.stderr else ''
        if response.returncode == 0:
            print(f'terraform command: {full_command}')
            print(stdout)
            return stdout
        else:
            raise f'ERROR:\nstdout: {stdout}\n\nstderr: {stderr}'

    def _now(self):
        """ Integer format of current time """
        return int(round(time.time()))
