# general-purpose utilities
from typing import Dict, Callable, List
import random


def combine_dictionaries(*args: Dict[str, object]) -> Dict[str, object]:
    """
    Flattens given dictionaries into a single one
    with respect to the arguments' order.
    """
    sum_dict = dict()
    for config in args:
        for key, value in config.items():
            sum_dict[key] = value
    return sum_dict


def get_weight_list(items, weight_predicate: Callable) -> List:
    """
    Creates a list of tuples representing an item, along with its weight,
    by applying the `weight_predicate`

    Notes
        `weight_predicate` must return non-negative integers
    """
    output_list = []
    for item in items:
        weight = weight_predicate(item)
        if weight < 0:
            raise ValueError("Predicate returned a negative integer")
        if weight > 0:
            output_list.append((item, weight))

    return output_list


def weighted_random(items, weight_predicate: Callable, count: int) -> List:
    """
    Randomly chooses `count` items given a weighing callable.

    Notes
        `weight_predicate` must return non-negative integers
    """
    if count < 0:
        raise ValueError("`count` should be a positive integer")

    input_list = get_weight_list(items, weight_predicate)
    if len(input_list) < count:
        raise ValueError("Not enough available items")

    total_weight = sum(pair[1] for pair in input_list)
    output_list = []

    while len(output_list) < count and total_weight > 0:
        rand = random.randint(1, total_weight)
        # keep subtracting until the prefix sum is greater than `rand`
        for index, pair in enumerate(input_list):
            item, weight = pair
            rand -= weight
            if rand > 0:
                continue
            # include `item`
            output_list.append(item)
            total_weight -= weight
            # remove `item` from list
            input_list[index] = (None, 0)
            break

    return output_list


def get_params(**kwargs) -> dict:
    """
    Dumps non-empty kwargs
    """
    args = dict()
    for key, value in kwargs.items():
        if value:
            args[key] = value
    return args


def percentage(sum: float, all: float) -> float:
    """Calculates percentage [0..100]"""
    return sum / all * 100 if all != 0 else 100


def short_str(value: str, count: int) -> str:
    """
    Returns first `count` characters from `value`,
    adding an ellipsis if necessary
    """
    if len(value) < count:
        return value
    return value[0:count] + '...'
