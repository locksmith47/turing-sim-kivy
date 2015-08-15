from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.properties import BooleanProperty
from kivy.properties import NumericProperty

# Note that this class contains no graphics. We subclass widget here to use kivy Properties.
class TuringSimulator(Widget):

	machine_halted = BooleanProperty()
	curr_step = NumericProperty()

	def __init__(self, tm_gui, tape_gui):
		self.tm_gui = tm_gui
		self.tape_gui = tape_gui

		self.running = False
		self.run_mode = False

		self.curr_state = None
		self.curr_transition = None

		self.curr_run = 0
		self.run_speed = 1

		self.halt_successful = False

		# Watch this value to see when the machine has stopped running
		self.machine_halted = False

		# Read this for the reason of the stop
		self.halt_reason = ''

		self.turing_steps = []
		self.curr_step = 0
		self.total_steps = 0

	""" 
	Desc: Enters the run mode. Basically, turingsimulator.py takes over all functionality 
		  until exit_run_mode is called. 
	Return: Returns true if entering run mode was successful, otherwise false (if no initial state)
	"""
	def enter_run_mode(self):
		if self.tm_gui.start_state:
			self.run_mode = True

			self.curr_step = 0
			self.total_steps = 0
			self.turing_steps = []

			self.curr_state = self.tm_gui.start_state
			self.curr_transition = self.curr_state.get_transition(self.tape_gui.get_curr_letter())
			self.highlight_curr_step()

			if self.curr_transition:
				self.add_turing_step(self.tape_gui.get_curr_letter(), self.curr_transition.write_sym, self.curr_transition.direction)
			else:
				self.add_turing_step(self.tape_gui.get_curr_letter(), None, None)
			return True

		return False

	def exit_run_mode(self):
		# Stop the machine running before exiting run mode.
		if self.running:
			self.running = False
			Clock.unschedule(self.run_machine_clocked)
		self.de_highlight_curr_step()
		self.run_mode = False

	def add_turing_step(self, read_sym, write_sym, direction):
		self.turing_steps.append(TuringStep(self.curr_state, self.curr_transition, read_sym, write_sym, direction))
		self.total_steps += 1

	def highlight_curr_step(self):
		if self.curr_transition:
			self.curr_transition.set_highlight(1,1,0)
		self.curr_state.set_highlight(1,1,0)

	def de_highlight_curr_step(self):
		if self.curr_transition:
			self.curr_transition.set_highlight(.8,.8,.8)
		self.curr_state.set_highlight(.8,.8,.8)

	def change_step_norm(self, step_norm):
		new_step = int(step_norm*(self.total_steps-1))
		self.change_step(new_step)
		if new_step == 0:
			return True
		return False

	def change_step(self, step_no):
		if step_no < self.total_steps:
			self.de_highlight_curr_step()

			while self.curr_step < step_no:
				self.step_machine_forward(False)

			while self.curr_step > step_no:
				self.step_machine_back(False)

			self.tape_gui.update_tape()
			self.highlight_curr_step() 
		else:
			print('Step out of bounds')

	# Start the machine running by itself (using kivy clock)
	def run_machine(self):
		self.running = True
		self.curr_run = 60
		Clock.schedule_interval(self.run_machine_clocked, 1/60)

	# Pause the machine from running itself (can still step forwards/backwards though)
	def pause_machine(self):
		if self.running:
			self.running = False
			Clock.unschedule(self.run_machine_clocked)

	# Runs the machine visually.
	def run_machine_clocked(self, dt):
		self.curr_run += self.run_speed
		if self.curr_run >= 60:
			self.curr_run -= 60

			step_success = self.step_machine_forward(True)

			if not step_success:
				Clock.unschedule(self.run_machine_clocked)	
				self.running = False

	def step_machine_forward(self, update_gfx):
		self.machine_halted = False
		if update_gfx:
			self.de_highlight_curr_step()
		if self.curr_transition:
			self.curr_step += 1
			self.tape_gui.write(self.curr_transition.write_sym)

			if self.curr_transition.direction == 'L':
				self.tape_gui.move_left()

			elif self.curr_transition.direction == 'R':
				self.tape_gui.move_right()

			self.curr_state = self.curr_transition.to_state
			self.curr_transition = self.curr_state.get_transition(self.tape_gui.get_curr_letter())
			
			if update_gfx:
				self.tape_gui.update_tape() 
				self.highlight_curr_step() 

			if self.curr_step >= self.total_steps:
				if self.curr_transition:
					self.add_turing_step(self.tape_gui.get_curr_letter(), self.curr_transition.write_sym, self.curr_transition.direction)
				else:
					self.add_turing_step(self.tape_gui.get_curr_letter(), None, None)

		else:
			self.highlight_curr_step()
			if self.curr_state.final_state:
				self.halt_successful = True
			else:
				self.halt_successful = False
			self.machine_halted = True
			return False
		return True

	"""
	Desc: Uses the turing_steps stack to move the machine backwards.
	Returns: Boolean - Whether we cannot move left any further.
	"""
	def step_machine_back(self, update_gfx):
		if self.curr_step > 0:
			self.curr_step -= 1
			if update_gfx:
				self.de_highlight_curr_step()
			
			turing_step = self.turing_steps[self.curr_step]
			if turing_step.direction == 'L':
				self.tape_gui.move_right()
			if turing_step.direction == 'R':
				self.tape_gui.move_left()

			self.tape_gui.write(turing_step.read_sym)

			self.curr_state = turing_step.state
			self.curr_transition = turing_step.transition

			if update_gfx:
				self.tape_gui.update_tape()
				self.highlight_curr_step()

			if self.curr_step == 0:
				return True
			return False
		return True

			
"""
Desc: Used in simulator stack to run the machine forwards and backwards.
"""
class TuringStep:
	"""
	@param: state - a turingstate instance. (used for highlighting)
	@param: transition - a turingtransition instance. (used for highlighting)

	Note: These are stored here so the use of wildcards is possible in the future.
	@param: read_sym - the symbol read (moving forwards)
	@param: write_sym - the symbol written (moving forwards)
	@param: read_sym - movement of the tape (moving forwards)
	"""
	def __init__(self, state, transition, read_sym, write_sym, direction):
		self.state = state
		self.transition = transition
		self.read_sym = read_sym
		self.write_sym = write_sym
		self.direction = direction