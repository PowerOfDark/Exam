import kivy
import os
from datetime import datetime
from ui.stubs import TextLabel, VerticalGrid, SaveDialog
from kivy.app import App, Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.layout import Layout
from kivy.lang.builder import Builder
from kivy.properties import ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from utils import percentage
from kivy.config import Config

kivy.require('1.11.1')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')


def wrap_action(handler):
    """
    Wraps a callable with no arguments into a kivy event handler
    """

    def action(obj, param):
        handler()

    return action


def get_container(root: Widget):
    """
    Returns the top-most Layout child
    """
    return next((child for child in root.children if isinstance(child, Layout)), None)


def get_app():
    return App.get_running_app()


NO_SCORE = -1e9
"""int: Constant that represents invalid question/exam score"""


class ExamAnswer(VerticalGrid):
    answer = ObjectProperty()
    answer_meta = ObjectProperty(None)
    grouping = StringProperty(None)
    is_selected = BooleanProperty()
    is_correct = BooleanProperty()

    def __init__(self, answer_meta, answer, grouping, **kwargs):
        super(ExamAnswer, self).__init__(**kwargs)
        self.bind(is_selected=wrap_action(self.save_changes))
        self.answer_meta = answer_meta
        self.answer = answer
        self.grouping = grouping

        self.build()

    @property
    def exam_question(self):
        # (ExamQuestion) <-> (Container) <-> (self)
        parent = self.parent
        if parent and parent.parent:
            return parent.parent
        return None

    def on_checked(self, value: bool):
        self.is_selected = value

    def save_changes(self):
        if self.answer:
            self.answer.is_selected = self.is_selected
        if self.exam_question:
            get_app().dispatch('on_answer_changed', self.exam_question.question)

    def build(self):
        if self.answer:
            self.is_selected = self.answer.is_selected
        meta = self.answer_meta or False
        self.is_correct = meta and meta.is_correct


class ExamQuestion(VerticalGrid):
    num = NumericProperty(0)
    points_graded = NumericProperty(NO_SCORE)
    points_str = StringProperty('')
    question = ObjectProperty()
    question_meta = ObjectProperty(None)
    text = StringProperty('')

    def __init__(self, question_meta, question, num, **kwargs):
        super(ExamQuestion, self).__init__(**kwargs)

        update = wrap_action(self.update)
        get_app().bind(should_grade=update, on_answer_changed=update)

        self.container = get_container(self)

        self.num = num
        self.answers = set()
        self.question_meta = question_meta
        self.question = question

        self.build()

    def clear(self):
        for widget in self.answers:
            self.container.remove_widget(widget)
        self.answers = set()

    def build(self):
        self.clear()
        if self.question:
            for ans in self.question.answers:
                self.build_answer(ans)
        self.update()

    def build_answer(self, answer):
        meta = self.question_meta
        ans_meta = meta.find_answer(answer.id) if meta else None
        # add checkbox grouping if there's only one answer
        grouping = None if self.question.is_multiple_choice else str(self.question.id)
        widget = ExamAnswer(ans_meta, answer, grouping)

        self.container.add_widget(widget)
        self.answers.add(widget)

    def update(self):
        meta = self.question_meta
        if self.question:
            self.text = self.question.text

            should_grade = get_app().should_grade
            self.points_graded = self.question.grade(meta) if should_grade else NO_SCORE

            # update points display
            if self.points_graded != NO_SCORE:
                self.points_str = f"{self.points_graded}/{self.question.points}p"
            else:
                self.points_str = f"{self.question.points}p"


class ExamQuestions(VerticalGrid):
    def __init__(self, **kwargs):
        super(ExamQuestions, self).__init__(**kwargs)
        app = get_app()
        app.bind(exam_meta=wrap_action(self.build), exam=wrap_action(self.build))

        self.container = get_container(self)

        self.questions = set()
        self.exam_meta = app.exam_meta
        self.exam = app.exam

        self.build()

    def clear(self):
        for widget in self.questions:
            self.container.remove_widget(widget)
        self.questions = set()

    def build(self):
        self.clear()
        if self.exam:
            for question in self.exam.questions:
                self.build_question(question)

    def build_question(self, question):
        meta = self.exam_meta
        q_meta = meta.find_question(question.id) if meta else None
        # numerate the question
        id = len(self.questions) + 1

        widget = ExamQuestion(q_meta, question, id)

        self.container.add_widget(widget)
        self.questions.add(widget)


class ExamView(VerticalGrid):
    def __init__(self, **kwargs):
        super(ExamView, self).__init__(**kwargs)

        container = self.ids.container
        container.add_widget(ExamQuestions())


class ExamApp(App):
    should_grade = BooleanProperty(False)
    score = NumericProperty(NO_SCORE)
    score_str = StringProperty(None)
    save_location = StringProperty(None)
    exam = ObjectProperty(None)
    exam_meta = ObjectProperty(None)

    def __init__(self, exam_meta, exam, save_location, **kwargs):
        self.register_event_type('on_answer_changed')

        grade = wrap_action(self.grade)
        update_title = wrap_action(self.update_title)
        self.bind(should_grade=grade, save_location=update_title)

        self.exam_meta = exam_meta
        self.exam = exam
        self.save_location = save_location
        super(ExamApp, self).__init__(**kwargs)

        self.should_grade = exam.was_user_completed and exam_meta is not None
        self.grade()

    def alert(self, text: str, size=(200, 100), **kwargs):
        """Shows an alert box"""
        content = TextLabel(text=text, color=(1, 1, 1, 1))
        self._popup = Popup(content=content, size_hint=(None, None), size=size, **kwargs)
        self._popup.open()

    def dismiss_popup(self):
        self._popup.dismiss()

    def update_title(self):
        self.title = f"[{self.save_location}] Exam '{self.exam and self.exam.title}'"

    def build(self):
        # load main UI styles
        Builder.load_file(os.path.join(os.path.dirname(__file__), 'ui.kv'))

        # scrollview covering the entire window
        root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        Window.bind(height=root.setter('height'))

        view = ExamView()
        root.add_widget(view)

        return root

    def clear_exam(self):
        """Clears the exam and notifies observers"""
        self.exam.clear()
        # notify observers
        self.property('exam').dispatch(self)
        self.should_grade = False

        self.alert("The exam has been cleared", title="Notice", size=(300, 100))

    def save_prompt(self):
        """Opens save prompt"""
        content = SaveDialog(save=self.save_prompt_callback, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save exam", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def save_prompt_callback(self, path, filename):
        self.dismiss_popup()
        path = os.path.join(path, filename)
        self.save_location = path
        self.save_exam()

    def save_exam(self):
        """Saves the exam at `save_location`"""
        if self.exam.user_name:
            self.exam.completed_at = datetime.now()
            self.exam.was_user_completed = True
            self.should_grade = self.exam_meta is not None
        else:
            self.alert("Exam was saved without user name", title="Notice", size=(300, 100))

        try:
            self.exam.save(self.save_location)
        except Exception:
            self.alert(f"Could not save the exam", title="Error")

    def grade(self):
        """Attempts to grade the exam"""
        meta = self.exam_meta
        max_score = self.exam.max_score
        if self.should_grade:
            self.score = self.exam.get_score(meta)
            percent = percentage(self.score, max_score)
            self.score_str = f"{self.score} / {max_score} ({percent:.1f}%)"
        else:
            self.score = NO_SCORE
            self.score_str = f"? / {max_score}"

    def on_answer_changed(self, question):
        self.grade()
