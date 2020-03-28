""" Utilities for writing integration tests around AWS Config service """
import time


MAX_ATTEMPTS = 50
WAIT_PERIOD = 20

def all_rule_results(configservice, rule_name):
    """ Return details for the given config rule, and deal with slurping all the results

    :param configservice: boto client for AWS Config
    :param rule_name: name of rule to get compliance details for
    :returns: slurped version of get_compliance_details_by_config_rule response """
    paginator = configservice.get_paginator('get_compliance_details_by_config_rule')
    page_iterator = paginator.paginate(
        ConfigRuleName=rule_name,
        ComplianceTypes=[
            'NON_COMPLIANT',
            'COMPLIANT',
            'NOT_APPLICABLE'
        ]
    )
    return [
        evaluation_result
        for page in page_iterator
        for evaluation_result in page['EvaluationResults']
    ]


def config_rule_wait_for_resource(configservice, resource_id, rule_name):
    """ wait for a resource_id to show up in config rule results.
    It's up to you to ensure that the rule and resource are relevant to each other... if not
    this thing will loop for a godawful long time.

    For example - eip-attached rule and eipalloc-xxxx go together.

    The point here is that the eval times for the rules ARE NOT RELIABLE for determining
    whether the rule has inspected a recent resource you created.  Therefore, this "wait" approach
    is to poll until the given resource shows up somewhere in the details - be it compliant or not.
    An irrelevant resource will never show so.... you'll be waiting... and finally get a None result

    :param configservice: boto client for interfacing with AWS Config service
    :param resource_id: resource id to wait for in the details of the call to get_compliance_details_by_config_rule
    :param rule_name: config rule to evaluate
    :return: None if resource never shows up, otherwise the EvaluationResult from call to
             get_compliance_details_by_config_rule
    """
    attempts = 0
    while True:
        compliance_result = [
            result
            for result in all_rule_results(configservice, rule_name)
            if result['EvaluationResultIdentifier']['EvaluationResultQualifier']['ResourceId'] == resource_id
        ]
        if compliance_result:
            return compliance_result[0]
        else:
            attempts += 1
            if attempts == MAX_ATTEMPTS:
                return None
            else:
                time.sleep(WAIT_PERIOD)


def evaluate_config_rule_and_wait_for_resource(configservice, resource_id,
                                               rule_name):
    """ Kick off the specified rule and wait for the resource_id to show up in the results.
    It's up to you to ensure that the rule and resource are relevant to each other... if not
    this thing will loop for a godawful long time.

    For example - eip-attached rule and eipalloc-xxxx go together.

    The point here is that the eval times for the rules ARE NOT RELIABLE for determining
    whether the rule has inspected a recent resource you created.  Therefore, this "wait" approach
    is to poll until the given resource shows up somewhere in the details - be it compliant or not.
    An irrelevant resource will never show so.... you'll be waiting... and finally get a None result

    :param configservice: boto client for interfacing with AWS Config service
    :param resource_id: resource id to wait for in the details of the call to get_compliance_details_by_config_rule
    :param rule_name: config rule to evaluate
    :return: None if resource never shows up, otherwise the EvaluationResult from call to
             get_compliance_details_by_config_rule
    """
    try:
        _ = configservice.start_config_rules_evaluation(
            ConfigRuleNames=[
                rule_name
            ]
        )
    except configservice.exceptions.LimitExceededException:
        # if throttled, just wait anyways
        pass

    return config_rule_wait_for_resource(configservice, resource_id, rule_name)
