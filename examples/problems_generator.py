# quick script to generate dummy problems
from models import ExamQuestionMeta, ProblemSet
from graders import GRADERS
import random


def generate_question(name: str, num_answers: int, points) -> dict:
    multiple = random.choice([True, False])
    correct_answers = 1
    if multiple:
        correct_answers = random.randint(2, num_answers - 1)
    return {
        'is_multiple_choice': multiple,
        'grader': random.choice(list(GRADERS.keys())),
        'points': random.randint(points[0], points[1]),
        'num_answers': num_answers,
        'num_correct_answers': correct_answers,
        'text': name
    }


def generate_answers(question: ExamQuestionMeta, num: int):
    correct_answers = question.num_correct_answers
    for index in range(0, num):
        is_correct = index < correct_answers
        text = f"{'Correct ' if is_correct else ''}Answer {index + 1}"
        question.insert_answer(is_correct=is_correct, text=text)


def generate(title, num_questions: int, num_answers: int, points=(1, 5)) -> ProblemSet:
    problems = ProblemSet(title=title)
    for index in range(0, num_questions):
        kwargs = generate_question(f"Question #{index}", num_answers, points)
        question = problems.insert_question(False, str(index), **kwargs)
        generate_answers(question, num_answers)
    return problems


generate("Test problem set", 12, 5).save('problems.yml')
