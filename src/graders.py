from typing import Callable
from utils import percentage
import math


def binary_grader(question_meta, question) -> int:
    """
    Basic question grader that grants all the points
    only if all answers are correct
    """
    if question_meta.id != question.id:
        return 0

    for answer in question.answers:
        meta = question_meta.find_answer(answer.id)
        if not meta or answer.is_selected != meta.is_correct:
            return 0

    return question.points


def linear_grader(question_meta, question) -> int:
    """
    Question grader that grants points proportionally
    to the number of correct answers.
    The score is set to zero if a wrong answer was selected
    """
    if question_meta.id != question.id:
        return 0
    correct_answers = 0
    all_correct_answers = 0
    for answer in question.answers:
        meta = question_meta.find_answer(answer.id)
        if not meta or (answer.is_selected and not meta.is_correct):
            return 0
        if meta.is_correct:
            all_correct_answers += 1
            if answer.is_selected:
                correct_answers += 1

    ratio = percentage(correct_answers, all_correct_answers) / 100.0

    return math.floor(question.points * ratio)


GRADERS = {
    'binary': binary_grader,
    'linear': linear_grader
}


def get_grader(name: str) -> Callable:
    if name in GRADERS:
        return GRADERS[name]
    raise NotImplementedError("The specified grader was not found")
