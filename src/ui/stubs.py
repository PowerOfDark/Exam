# this file contains widget-stubs further used in the ui.kv layout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.properties import ObjectProperty


class TextLabel(Label):
    pass


class HorizontalTextLabel(Label):
    pass


class ExamHeader(BoxLayout):
    pass


class ExamInfo(BoxLayout):
    pass


class VerticalGrid(BoxLayout):
    pass


class HorizontalGrid(BoxLayout):
    pass


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    cancel = ObjectProperty(None)
    text_input = ObjectProperty(None)
