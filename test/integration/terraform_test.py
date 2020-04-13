import pytest
import boto3

import potemkin
from potemkin.configservice import config_rule_wait_for_compliance_results


@potemkin.TerraformResources('test/integration/test_templates/terraform')
def test_wait_for_compliance_results(tf_outputs):
    global expected_results_success
    configservice = boto3.Session().client('config')

    expected_results = {
        tf_outputs['EIPOutput']: "NON_COMPLIANT",
        tf_outputs['EIP2Output']: "NON_COMPLIANT"
    }

    assert config_rule_wait_for_compliance_results(
        configservice,
        rule_name=tf_outputs['ConfigRuleName'],
        expected_results=expected_results)
