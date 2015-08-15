from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import ListProperty
from kivy.metrics import *
from kivy.graphics import *
from turingtape_deque import TuringTape as TuringTape_Deque

class TuringTape(BoxLayout):

    def __init__(self, **kwargs):
        super(TuringTape, self).__init__(**kwargs)

        self.element_size = cm(.25)
        self.tape_elements = []

        self.blank_char = '_'
        self.tape = TuringTape_Deque('', self.blank_char, True)
        self.curr_index = 0

        self.turing_simulator = None

    def resize(self, size):
        self.total_elements = int(size[0]/self.element_size)
        if self.total_elements % 2 == 0:
            self.total_elements -= 1
        self.middle_index = int(self.total_elements/2)

        for tape_element in self.tape_elements:
            self.remove_widget(tape_element)
        self.tape_elements = []

        for i in range(0,self.total_elements):

            if i == self.middle_index:
                tape_element = TapeElement(text = '_', color = (0,0,0,1))
                tape_element.bg_color.r = 0
                tape_element.bg_color.g = 1
                tape_element.bg_color.b = 1
            else:
                tape_element = TapeElement(text = '_')

            self.add_widget(tape_element)
            self.tape_elements.append(tape_element)

        self.update_tape()

    def set_initial_tape(self, tape_str):
        self.tape.set_tape(tape_str)
        self.curr_index = 0
        self.update_tape()

    def reset_tape_head(self):
        self.curr_index = self.tape.get_first_index()
        self.tape.tape_index = self.curr_index
        self.update_tape()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.turing_simulator.run_mode:
            if touch.pos[0] > self.x and touch.pos[0] < self.x+self.width/2:
                self.move_left()
            else:
                self.move_right()
            self.update_tape()

    def update_tape(self):
        tape_chars = self.tape.get_characters(self.curr_index-self.middle_index, self.total_elements)

        for index, tape_char in enumerate(tape_chars):
            self.tape_elements[index].text = tape_char

    def get_tape_str(self):
        return self.tape.get_tape_str()
            

    def get_curr_letter(self):
        """
        @desc: mimics identical method in TuringTape class.
        @return: the current letter pointed to on the tape.
        """
        return self.tape.get_curr_letter()

    def write(self, str):
        """
        @desc: mimics identical method in TuringTape class
        @param: str - a single character string, this is what
        is written to the tape
        """
        self.tape.write(str)

    def move_left(self):
        """
        @desc: mimics identical method in TuringTape class
        @return: returns the new value being pointed to by the tapehead
        """
        self.curr_index = self.tape.move_left()

    def move_right(self):
        """
        @desc: mimics identical method in TuringTape class
        @return: returns the new value being pointed to by the tapehead
        """
        self.curr_index = self.tape.move_right()

class TapeElement(Label):

    def __init__(self, **kwargs):
        super(TapeElement, self).__init__(**kwargs)

        self.bind(size=self.resize)

        self.bg_color = Color(.3,.3,.3)
        self.bg_rect = Rectangle()

        self.canvas.before.add(self.bg_color)
        self.canvas.before.add(self.bg_rect)

    def resize(self, instance, size):
        self.bg_rect.size = (self.size[0], self.size[1]*.6)
        self.bg_rect.pos = (self.pos[0], self.pos[1]+self.size[1]*.2)