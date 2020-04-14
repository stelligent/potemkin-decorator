""" Utilities not specific to an aws Service """
from random import randint
from time import sleep


def random_name(name, digits=10):
    """ Create a name with a random digits string at the end. Defaults to 10 digits """

    range_low = 10**(digits - 1)
    range_high = (10**digits) - 1
    return f'{name}{randint(range_low, range_high)}'


class WaitUntilTrueException(Exception):
    """ Custom exception for wait_until_true function"""

    def __init__(self, value):
        self.value = value
        self.name = 'wait_until_true_exception'

    def __str__(self):
        return f'{self.name}: {self.value}'


def wait_until_true(function, wait_period=20, attempts=15):
    """
    Decorator that sleeps and retries a function until the return value returns a truthy value or
    it times out and raises an exception.

    :param wait_period: time to wait between attempts (default 20 seconds)
    :param attempts: number of attempts before erroring
    :returns: functions response or raises error if all attempts do not result in a truthy value
    """

    def wrapper(*args, **kwargs):
        for _ in range(attempts):
            return_value = function(*args, **kwargs)
            if return_value:
                return return_value
            sleep(wait_period)
        raise WaitUntilTrueException('all retries used')

    return wrapper
