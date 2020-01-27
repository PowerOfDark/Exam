from utils import weighted_random, combine_dictionaries, percentage, get_params


def test_random():
    objs = list(range(0, 20))
    output = weighted_random(objs, lambda x: x, 2)
    assert len(output) == 2


def test_random_negative():
    objs = list(range(-5, 20))
    try:
        weighted_random(objs, lambda x: x, 1)
    except ValueError:
        # ok
        return
    raise Exception("Accepts negative weights")


def test_random_zero():
    objs = list(range(0, 20))
    try:
        weighted_random(objs, lambda x: x, 20)
    except ValueError:
        # ok
        return
    raise Exception("Doesn't ignore zero-weights")


def test_combine_dicts():
    first = {'One': 1, 'Two': 2, 'Three': 3}
    second = {'foo.yml': 'bar', 'Two': 4}
    third = {'foo.yml': 4, 'Three': None}

    result = combine_dictionaries(first, second, third)
    assert len(result) == 4
    assert result['foo.yml'] == result['Two']


def test_percentage():
    assert percentage(0, 0) == 100
    assert percentage(1, 2) == 50


def test_get_params():
    kwargs = {'key': None, 'foo.yml': 'bar'}
    result = get_params(**kwargs)
    assert len(result) == 1
    assert 'foo.yml' in result
