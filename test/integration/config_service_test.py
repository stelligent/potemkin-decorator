import pytest
import potemkin
import boto3
from potemkin.configservice import evaluate_config_rule_and_wait_for_resource, config_rule_wait_for_resource, config_rule_wait_for_absent_resources, config_rule_wait_for_compliance_results


@potemkin.CloudFormationStack('test/integration/test_templates/eip.yml',
                              stack_name_stem='EipTestStack')
def test_wait_for_compliance_results_success(stack_outputs, stack_name):
    global expected_results_success
    configservice = boto3.Session().client('config')

    expected_results_success = {
        stack_outputs['EIPOutput']: "NON_COMPLIANT",
        stack_outputs['EIP2Output']: "NON_COMPLIANT"
    }

    assert config_rule_wait_for_compliance_results(
        configservice,
        rule_name='eip-attached',
        expected_results=expected_results_success)


@pytest.mark.xfail(reason="deliberate fail")
@potemkin.CloudFormationStack('test/integration/test_templates/eip.yml',
                              stack_name_stem='EipTestStack')
def test_wait_for_compliance_results_fail(stack_outputs, stack_name):
    global expected_results_fail
    configservice = boto3.Session().client('config')

    expected_results_fail = {
        stack_outputs['EIPOutput']: "NON_COMPLIANT",
        stack_outputs['EIP2Output']: "COMPLIANT"
    }

    assert config_rule_wait_for_compliance_results(
        configservice,
        rule_name='eip-attached',
        expected_results=expected_results_fail)


def test_wait_for_compliance_results_success_results_removed():
    configservice = boto3.Session().client('config')
    resource_ids = list(expected_results_success.keys())

    assert [] == config_rule_wait_for_absent_resources(
        configservice, rule_name='eip-attached', resource_ids=resource_ids)


def test_wait_for_compliance_results_fail_results_removed():
    configservice = boto3.Session().client('config')
    resource_ids = list(expected_results_fail.keys())

    assert [] == config_rule_wait_for_absent_resources(
        configservice, rule_name='eip-attached', resource_ids=resource_ids)


@potemkin.CloudFormationStack(
    'test/integration/test_templates/eip.yml',
    stack_name_stem='EipTestStack'
)
def test_config_rule_with_evaluate(stack_outputs, stack_name):
    eipalloc = stack_outputs['EIPOutput']
    configservice = boto3.Session().client('config')

    actual_result = evaluate_config_rule_and_wait_for_resource(
        configservice,
        resource_id=eipalloc,
        rule_name='eip-attached'
        )

    expected_compliance_type = 'NON_COMPLIANT'
    assert actual_result['ComplianceType'] == expected_compliance_type

@potemkin.CloudFormationStack(
    'test/integration/test_templates/eip.yml',
    stack_name_stem='EipTestStack'
)
def test_config_rules_no_evaluate(stack_outputs, stack_name):
    eipalloc = stack_outputs['EIPOutput']
    configservice = boto3.Session().client('config')

    actual_result = config_rule_wait_for_resource(
        configservice,
        resource_id=eipalloc,
        rule_name='eip-attached'
    )

    expected_compliance_type = 'NON_COMPLIANT'
    assert actual_result['ComplianceType'] == expected_compliance_type
