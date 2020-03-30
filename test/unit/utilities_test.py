from potemkin import utilities


def test_utilities_default():
    """ test not specifying digits returns name with 10 digits appended """
    name = 'testname'
    full_name = utilities.random_name(name)

    assert len(full_name) == len(name) + 10
    assert isinstance((int(full_name[len(name):])), int)


def test_utilities_digits():
    """ test specifying digits returns name with correct number of digits """
    name = 'testname'
    digits = 3

    full_name = utilities.random_name(name, digits=digits)

    assert len(full_name) == len(name) + digits
    assert isinstance((int(full_name[len(name):])), int)