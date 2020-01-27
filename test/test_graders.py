from models import ExamQuestionMeta, ExamQuestion
from graders import binary_grader, linear_grader
import related

sample_meta = related.from_yaml("""
id: 'test'
num_answers: 4
num_correct_answers: 2
answers:
        - text: 1
          is_correct: yes
        - text: 2
          is_correct: yes
        - text: 3
        - text: 4
""", ExamQuestionMeta)

sample_meta.validate()

sample_question = related.from_yaml("""
id: 'test'
points: 4
answers:
        - id: 1
        - id: 2
          is_selected: yes
        - id: 3
        - id: 4
""", ExamQuestion)


def test_binary_grader():
    score = binary_grader(sample_meta, sample_question)
    assert score == 0


def test_linear_grader():
    score = linear_grader(sample_meta, sample_question)
    assert score == 2
