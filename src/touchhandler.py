import kivy

from copy import copy

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.vector import Vector
from kivy.graphics import *
from kivy.properties import BooleanProperty
from kivy.properties import ObjectProperty
from kivy.metrics import *

kivy.require('1.7.0')


class TouchHandler(Widget):
    touch_pt = None
    touch_stray = 0

    hold_time = .4
    animation_wait = .2

    hold_triggered = BooleanProperty()
    click_triggered = BooleanProperty()
    double_triggered = BooleanProperty()
    move_triggered = BooleanProperty()

    initial_touch = None
    multitouch = False
    multi_touches = []

    curr_touch_down = ObjectProperty(None)
    curr_touch_up = ObjectProperty(None)
    curr_touch_move = ObjectProperty(None)

    curr_time = 0

    def on_touch_down(self, touch):
        super(TouchHandler, self).on_touch_down(touch)

        self.curr_touch_down = touch

        if self.touch_stray == 0:
            self.touch_stray = cm(.3)

        if not self.initial_touch and not self.multitouch:
            self.initial_touch = touch
            touch.strayed = False

            # Check for a click, or move, or double touch
            self.click_triggered = False
            self.move_triggered = False
            self.double_triggered = False

            # Hold routine
            self.strayed = False
            self.canvas.clear()
            self.curr_time = 0
            self.hold_triggered = False

            # Just incase (probably not needed)
            Clock.unschedule(self.hold_routine)
            Clock.schedule_interval(self.hold_routine, 1 / 60)
        # We must have multiple touches.
        else:
            self.multi_touches.append(touch)
            self.multitouch = True

            # Assuming hold from the initial touch is running, we stop it.
            self.canvas.clear()
            Clock.unschedule(self.hold_routine)

    def on_touch_up(self, touch):
        # We have a single touch, handle single click, double click.
        if not self.multitouch and self.initial_touch:
            if self.curr_time < self.animation_wait and not touch.is_double_tap and not self.strayed:
                self.click_triggered = True
            if touch.is_double_tap and not self.strayed:
                self.double_triggered = True
            self.canvas.clear()
            Clock.unschedule(self.hold_routine)

        self.curr_touch_up = touch

        # Dealing with initial touch up
        if self.initial_touch:
            if touch == self.initial_touch:
                self.initial_touch = None

        # Dealing with any touch following the initial one.
        if touch in self.multi_touches:
            self.multi_touches.remove(touch)

        if len(self.multi_touches) == 0 and not self.initial_touch:
            self.multitouch = False

    def on_touch_move(self, touch):
        # Bit of a hacky way to see a move event, but it works.
        self.move_triggered = not self.move_triggered
        if self.initial_touch == touch:
            if Vector(self.initial_touch.opos).distance(Vector(touch.pos)) > self.touch_stray:
                touch.strayed = True
                self.strayed = True
                self.canvas.clear()
                Clock.unschedule(self.hold_routine)
        self.curr_touch_move = touch

    def hold_routine(self, dt):

        self.curr_time += dt

        self.canvas.clear()
        if self.curr_time > self.animation_wait:
            with self.canvas:

                Color(1, 1, 1, 1)
                diameter = cm(1.5)
                Line(width=2, ellipse=(self.initial_touch.opos[0] - diameter / 2, self.initial_touch.opos[1] - diameter / 2,
                                       diameter, diameter, 0,
                                       1 + 359 * (self.curr_time - self.animation_wait) / (self.hold_time - self.animation_wait)))

        if self.curr_time > self.hold_time:
            Clock.unschedule(self.hold_routine)
            self.hold_triggered = True
