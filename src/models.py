from typing import List, Optional, Dict, Callable
import related
from datetime import datetime
import random
from config import ConfigProvider
from graders import get_grader
from utils import combine_dictionaries, weighted_random


class ConfigError(Exception):
    pass


class SchemeError(Exception):
    pass


CFG = ConfigProvider.get_question_defaults()
if CFG is None:
    raise ConfigError("Missing internal 'question_defaults' config")


@related.mutable
class ExamQuestionAnswerMeta:
    """
    Represents metadata of a question answer's object
    """
    text = related.StringField('')
    is_correct = related.BooleanField(False, required=False)
    likelihood = related.IntegerField(1, required=False)
    id = related.IntegerField(0)

    def __str__(self):
        return f"{self.id}: [{'+' if self.is_correct else '-'}] {self.text}"


@related.mutable
class ExamQuestionAnswer:
    id = related.IntegerField(0)
    text = related.StringField('')
    is_selected = related.BooleanField(False, required=False)

    @staticmethod
    def from_meta(meta: ExamQuestionAnswerMeta):
        return ExamQuestionAnswer(id=meta.id, text=meta.text)


@related.mutable
class ExamQuestionMeta:
    """
    Represents question metadata along with all possible answers
    """

    @staticmethod
    def from_defaults(*args: Dict[str, object]):
        defaults = combine_dictionaries(CFG, *args)
        return ExamQuestionMeta(**defaults)

    id = related.StringField('')
    text = related.StringField('')
    num_answers = related.IntegerField(CFG['num_answers'], required=False)
    num_correct_answers = related.IntegerField(CFG['num_correct_answers'], required=False)
    is_multiple_choice = related.BooleanField(CFG['is_multiple_choice'], required=False)
    likelihood = related.IntegerField(CFG['likelihood'], required=False)
    points = related.IntegerField(CFG['points'], required=False)
    answers = related.SequenceField(ExamQuestionAnswerMeta, required=False)
    grader = related.StringField('binary', required=False)

    def prepare_answers(self) -> List[ExamQuestionAnswerMeta]:
        """
        Returns a list with randomly selected answers
        """
        correct_answers = list(filter(lambda ans: ans.is_correct, self.answers))
        wrong_answers = list(filter(lambda ans: not ans.is_correct, self.answers))
        wrong_answers_count = self.num_answers - self.num_correct_answers

        def validate(items, count, prompt):
            nonlocal self
            item_count = len(items)
            if count > item_count:
                raise SchemeError(
                    f"Question `{self.text}`, {prompt}: got {item_count}, expected {count}")

        validate(correct_answers, self.num_correct_answers, 'correct answers')
        validate(wrong_answers, wrong_answers_count, 'wrong answers')

        def get_likelihood(ans):
            return ans.likelihood

        correct_answers = weighted_random(correct_answers, get_likelihood, self.num_correct_answers)
        wrong_answers = weighted_random(wrong_answers, get_likelihood, wrong_answers_count)

        answers = correct_answers + wrong_answers
        random.shuffle(answers)
        return answers

    def _get_next_answer_id(self) -> int:
        """
        Returns an unused answer id
        """
        last_id = 0 if len(self.answers) == 0 else max(ans.id for ans in self.answers)
        return last_id + 1

    def find_answer(self, id: int) -> ExamQuestionAnswerMeta:
        """
        Returns the answer with specified `id` if it exists; otherwise None
        """
        return next((ans for ans in self.answers if ans.id == id), None)

    def insert_answer(self, id: Optional[int] = None, **kwargs) -> ExamQuestionAnswerMeta:
        """
        Inserts an answer with specified `id` (or replaces if exists)
        """
        next_id = self._get_next_answer_id()
        found_answer = self.find_answer(id)
        if found_answer:
            sum_dict = combine_dictionaries(found_answer.__dict__, kwargs)
            new_answer = ExamQuestionAnswerMeta(**sum_dict)
            self.answers.remove(found_answer)
        else:
            new_answer = ExamQuestionAnswerMeta(id=(id or next_id), **kwargs)
        self.answers.append(new_answer)

        return new_answer

    def validate(self):
        """Validates object state"""
        for answer in self.answers:
            if answer.id == 0:
                answer.id = self._get_next_answer_id()
        if self.num_correct_answers != 1:
            self.is_multiple_choice = True
        self.points = max(0, self.points)


@related.mutable
class ExamQuestion:
    id = related.StringField(None)
    text = related.StringField('')
    is_multiple_choice = related.BooleanField(False)
    answers = related.SequenceField(ExamQuestionAnswer, None)
    points = related.IntegerField(0)

    @staticmethod
    def from_meta(id: str, meta: ExamQuestionMeta):
        meta.validate()
        multiple_choice = meta.is_multiple_choice
        answers_meta = meta.prepare_answers()
        answers = [ExamQuestionAnswer.from_meta(ans) for ans in answers_meta]
        return ExamQuestion(id=id, text=meta.text, is_multiple_choice=multiple_choice,
                            answers=answers,
                            points=meta.points)

    def grade(self, meta: ExamQuestionMeta) -> int:
        """
        Returns the score for this ExamQuestion instance
        """
        grader = get_grader(meta.grader)
        if grader:
            return grader(meta, self)
        return 0


@related.mutable
class Exam:
    """Represents a writable exam"""
    meta_uuid = related.UUIDField()
    generated_at = related.DateTimeField(default=datetime.now(), required=False)
    questions = related.SequenceField(ExamQuestion, required=False)
    title = related.StringField('')
    description = related.StringField(required=False)
    was_user_completed = related.BooleanField(False, required=False)
    user_name = related.StringField(required=False)
    completed_at = related.DateTimeField(required=False)

    def save(self, path: str):
        with open(path, "w") as file:
            related.to_yaml(self, file)

    def clear(self):
        """
        Clears this Exam instance from any user-input
        """
        self.was_user_completed = False
        self.user_name = None
        self.completed_at = None
        for question in self.questions:
            for ans in question.answers:
                ans.is_selected = False

    @property
    def max_score(self):
        return sum(q.points for q in self.questions)

    def get_score(self, meta, question_callback: Callable = None) -> int:
        """
        Calculates this Exam's total score.

        Args
            question_callback: called for each graded question with its score
        """
        if meta is None:
            return 0

        score = 0

        for question in self.questions:
            question_meta = meta.find_question(question.id)
            points = question.grade(question_meta)
            if question_callback:
                question_callback(question, points)
            score += points

        return score


@related.mutable
class ProblemSet:
    """Stores all question metadata and defaults"""
    uuid = related.UUIDField(required=False)
    title = related.StringField('')
    questions = related.MappingField(ExamQuestionMeta, 'id', required=False)
    question_defaults = related.ChildField(ExamQuestionMeta, ExamQuestionMeta.from_defaults(),
                                           required=False)

    def create_question(self, **kwargs) -> ExamQuestionMeta:
        """Creates a new Question from defaults"""
        return ExamQuestionMeta.from_defaults(self.question_defaults.__dict__, kwargs)

    def insert_question(self, allow_edit: bool, id: str, **kwargs) -> ExamQuestionMeta:
        found_question = self.find_question(id)
        if found_question:
            if not allow_edit:
                raise KeyError("Question with specified `id` already exists")
            sum_dict = combine_dictionaries(found_question.__dict__, kwargs)
            new_question = self.create_question(**sum_dict)
        else:
            new_question = self.create_question(**kwargs)
        self.questions[id] = new_question
        return new_question

    def find_question(self, id: str) -> ExamQuestionMeta:
        """
        Returns the question with specified `id` if it exists; otherwise None
        """
        return self.questions.get(id, None)

    def generate_exam(self, num_questions: int, description: str, title: str = None) -> Exam:
        """
        Creates an Exam instance from randomly selected questions and answers
        Args:
            num_questions: the number of questions to include
            description: exam description shown to user
            title: short exam title
        """
        questions_meta = weighted_random(self.questions.items(), lambda q: q[1].likelihood,
                                         num_questions)
        questions = [ExamQuestion.from_meta(id, meta) for id, meta in questions_meta]
        now = datetime.now()
        return Exam(meta_uuid=self.uuid, generated_at=now, title=title or self.title,
                    questions=questions,
                    description=description)

    def ensure_exam_compatibility(self, exam: Exam) -> None:
        """
        Checks whether the `exam` was created from this problem set.

        Raises
            SchemeError: if the `exam` isn't compatible
        """

        def fail(reason):
            raise SchemeError(
                f"Problem set `{self.title}` does not match the exam `{self.title}` ({reason})")

        if self.uuid != exam.meta_uuid:
            fail('UUID')

        # check for missing questions
        for question in exam.questions:
            if self.find_question(question.id) is None:
                fail(f"missing question: {question.id}")

    def save(self, path: str) -> None:
        """
        Saves this object instance as YAML to the specified path
        """
        self.validate()
        with open(path, "w") as file:
            related.to_yaml(self, file, suppress_empty_values=True, suppress_map_key_values=True)

    def validate(self):
        """Validates object state"""
        for key, question in self.questions.items():
            question.validate()

    @staticmethod
    def from_file(path: str):
        with open(path, "r") as file:
            obj = related.from_yaml(file, ProblemSet)
            obj.validate()
            return obj
