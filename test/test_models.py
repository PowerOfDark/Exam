from models import ProblemSet, ExamQuestionMeta, SchemeError


def test_insert_question():
    exam = ProblemSet()
    exam.insert_question(False, 'test')
    assert len(exam.questions) == 1
    try:
        exam.insert_question(False, 'test')
    except KeyError:
        # ok
        return
    raise Exception("Duplicate insertion")


def test_modify_question():
    exam = ProblemSet()
    exam.insert_question(False, 'test')
    exam.insert_question(True, 'test', num_answers=1)
    assert len(exam.questions) == 1


def get_question(**kwargs):
    return ExamQuestionMeta.from_defaults(kwargs)


def test_insert_answer():
    question = get_question(id='test')
    answer = question.insert_answer(text='1')
    assert answer.id == 1
    answer = question.insert_answer(1, text='2')
    assert len(question.answers) == 1


def test_prepare_answers():
    question = get_question(id='test')

    question.num_answers = 2
    question.num_correct_answers = 1

    question.insert_answer(1, is_correct=True)
    question.insert_answer(2, is_correct=False)
    question.insert_answer(3, is_correct=True)

    assert len(question.answers) == 3

    qa = question.prepare_answers()
    assert len(qa) == 2
    assert sum(1 for ans in qa if ans.is_correct) == 1

    # disable one of the answers
    question.insert_answer(2, likelihood=0)
    assert len(question.answers) == 3

    try:
        qa = question.prepare_answers()
    except (SchemeError, ValueError):
        # not enough answers to pick from
        return
    raise Exception("Picks disabled answers")
