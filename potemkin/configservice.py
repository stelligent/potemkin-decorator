""" Utilities for writing integration tests around AWS Config service """
import time
import json


MAX_ATTEMPTS = 45
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


def _remove_missing_resource_ids(config_records, resource_ids):
    """
    Remove resource_ids found in config_results and return any remaining resource_ids
    
    :param config_records: config compliance records
    :param resource_ids: list of resource ids
    :returns: list of resource IDs found in compliance records
    """
    resources_in_config = []

    for config_record in config_records:
        config_record_id = config_record['EvaluationResultIdentifier'][
            'EvaluationResultQualifier']['ResourceId']

        if config_record_id in resource_ids:
            resources_in_config.append(config_record_id)
    return resources_in_config


def config_rule_wait_for_absent_resources(configservice, rule_name, resource_ids,
                                          wait_period=WAIT_PERIOD, max_attempts=MAX_ATTEMPTS):
    """
    Wait for resource_ids to be removed from AWS Config results.
    Default timeout is 15 minutes

    :param configservice: boto client for interfacing with AWS Config service
    :param rule_name: config rule to evaluate
    :param wait_period: period to wait between checks
    :return: empty list if all resource_ids are absent. If timeout, return list of remaining ids.

    :param wait_period: length of wait period (optional)
    :param max_attempts: number of attempts before timeout (optional)
    """
    for _ in range(max_attempts):
        config_records = all_rule_results(configservice, rule_name)
        remaining_ids = _remove_missing_resource_ids(config_records, resource_ids)
        if not remaining_ids:
            return []
        time.sleep(wait_period)
    print(f'TIMEOUT waiting for these resources to disappear: {remaining_ids}')
    return remaining_ids


def _present_config_results(config_records, resource_ids):
    """ 
    If resource_id is in config_results add to dictionary and return dictionary
    
    :param config_records: config compliance records
    :param resource_ids: list of resource ids
    :returns: dictionary of resource_id: compliance_type
    """
    found_ids = {}
    for config_records in config_records:
        config_record_id = config_records['EvaluationResultIdentifier'][
            'EvaluationResultQualifier']['ResourceId']

        if config_record_id in resource_ids:
            found_ids[config_record_id] = config_records["ComplianceType"]
    return found_ids


def config_rule_wait_for_compliance_results(configservice, rule_name, expected_results,
                                            wait_period=WAIT_PERIOD, max_attempts=MAX_ATTEMPTS,
                                            evaluate=False):
    """ 
    Wait for all resource_ids to show up in config_results, then compare config_results
    to to expected_results. Default timeout is 15 minutes

    :param configservice: boto client for interfacing with AWS Config service
    :param rule_name: config rule to evaluate
    :param expected_results: dictionary of expected results in format resource_id: COMPLIANT|NON_COMPLIANT
    :return: test results compared to actual results. If timeout results are partial.

    :param wait_period: length of wait period (optional)
    :param max_attempts: number of attempts before timeout (optional)
    :param evaluate: If True, initiate a config rule evaluation. Use for periodic rules. (optional)
    """

    if evaluate:
        _start_evaluations(configservice, rule_name)

    resource_ids = list(expected_results.keys())
    resource_id_count = len(resource_ids)
    for _ in range(max_attempts):
        config_records = all_rule_results(configservice, rule_name)

        actual_results = _present_config_results(config_records, resource_ids)
        if len(actual_results) == resource_id_count:
            break
        time.sleep(wait_period)

    print(f'actual_results = {json.dumps(actual_results, indent=4)}')
    print(f'expected_results = {json.dumps(expected_results, indent=4)}')
    return actual_results == expected_results


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

def _start_evaluations(configservice, rule_name):
    """ Start configuration rule evaluations """
    try:
        _ = configservice.start_config_rules_evaluation(
            ConfigRuleNames=[
                rule_name
            ]
        )
    except configservice.exceptions.LimitExceededException:
        # if throttled, just wait anyways
        pass

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

    _start_evaluations(configservice, rule_name)
    return config_rule_wait_for_resource(configservice, resource_id, rule_name)
