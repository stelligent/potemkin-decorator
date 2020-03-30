""" Utilities not specific to an aws Service """
from random import randint


def random_name(name, digits=10):
    """ Create a name with a random digits string at the end. Defaults to 10 digits """

    range_low = 10**(digits - 1)
    range_high = (10**digits) - 1
    return f'{name}{randint(range_low, range_high)}'
