from kivy.uix.textinput import TextInput
from kivy.properties import NumericProperty
"""
    Desc: Extends the kivy TextInput by allowing us to limit charaters in textfields

    BUGS: Currently doesn't work on android due to predictive text. Need to fix.
""" 
class BoundedInput(TextInput):

    max_chars = NumericProperty(7)

    def insert_text(self, substring, from_undo=False):
        if not from_undo and len(self.text)+len(substring) > self.max_chars and self.max_chars != -1:
            return
        super(BoundedInput, self).insert_text(substring, from_undo)
