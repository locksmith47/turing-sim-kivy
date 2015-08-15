# File name: layouts.py
import kivy
from kivy.uix.slider import Slider

kivy.require('1.7.0')

class SpeedSlider(Slider):

	def __init__(self, **kwargs):
		super(SpeedSlider, self).__init__(**kwargs)
		self.min = 1
		self.max = 200
		self.value = 50
		self.touches_on = 0

	def on_touch_down(self, touch):
		if self.disabled or not self.collide_point(*touch.pos):
			return
		if touch.is_mouse_scrolling:
			if 'down' in touch.button or 'left' in touch.button:
				if self.step:
					self.value = min(self.max, self.value + self.step)
				else:
					self.value = min(
						self.max,
						self.value + (self.max - self.min) / 20)
			if 'up' in touch.button or 'right' in touch.button:
				if self.step:
					self.value = max(self.min, self.value - self.step)
				else:
					self.value = max(
						self.min,
						self.value - (self.max - self.min) / 20)
		else:
			touch.grab(self)
			self.touches_on += 1
			self.value_pos = touch.pos
		return True

	def on_touch_up(self, touch):
		if super(SpeedSlider, self).on_touch_up(touch):
			self.touches_on -= 1
			return True
