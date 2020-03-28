import potemkin
import boto3
from potemkin.configservice import evaluate_config_rule_and_wait_for_resource, config_rule_wait_for_resource


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
