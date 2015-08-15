from kivy.uix.widget import Widget
from kivy.properties import NumericProperty

# Note that this class contains no graphics. We subclass widget here to use kivy Properties.
class UndoHandler(Widget):

	curr_action = NumericProperty(0)

	def __init__(self):

		self.undo_stack = []
		self.curr_action = -1

		self.tm_gui = None
		self.tape_gui = None

	def reset(self):
		self.undo_stack = []
		self.curr_action = -1

	def get_total_actions(self):
		return len(self.undo_stack)

	def add_action(self, action):
		if len(self.undo_stack) != 0:
			self.undo_stack = self.undo_stack[:self.curr_action+1]
		self.undo_stack.append(action)
		self.curr_action += 1

	def undo_action(self):
		if self.curr_action > -1:
			self.undo_stack[self.curr_action].undo_action(self.tm_gui, self.tape_gui)
			self.curr_action -= 1
		else:
			print('Undo out of range')

	def redo_action(self):
		if self.curr_action < len(self.undo_stack) - 1 and len(self.undo_stack) is not 0:
			self.curr_action += 1
			self.undo_stack[self.curr_action].redo_action(self.tm_gui, self.tape_gui)
		else:
			print('Redo out of range')
		

class MachineAction:

	def __init__(self):
		pass

	def undo_action(self, tm_gui, tape_gui):
		pass

	def redo_action(self, tm_gui, tape_gui):
		pass

class Action_AddState(MachineAction):

	def __init__(self, state_name, pos, unique_id):
		self.state_name = state_name
		self.pos = (pos[0], pos[1])
		self.unique_id = unique_id

	def undo_action(self, tm_gui, tape_gui):
		state = tm_gui.get_state_by_name(self.state_name)
		tm_gui.delete_state(state, True)

	def redo_action(self, tm_gui, tape_gui):
		tm_gui.add_state(self.pos, True, self.state_name, True, self.unique_id)

class Action_DeleteState(MachineAction):

	def __init__(self, state_name, pos, final, start, out_transitions, in_transitions, unique_id):
		self.state_name = state_name
		self.pos = (pos[0], pos[1])
		self.out_transitions = []
		self.in_transitions = []
		self.final = final
		self.start = start
		self.unique_id = unique_id

		for transition in out_transitions:
			self.out_transitions.append(TuringTransition_Str(transition))

		for transition in in_transitions:
			self.in_transitions.append(TuringTransition_Str(transition))

	def undo_action(self, tm_gui, tape_gui):
		from_state = tm_gui.add_state(self.pos, True, self.state_name, True, self.unique_id)

		if self.final:
			from_state.set_final_state(True)
		if self.start:
			tm_gui.start_state = from_state
			from_state.set_start_state(True)
		    	
		for transition in self.out_transitions:
			to_state = tm_gui.get_state_by_name(transition.to_state)
			tm_gui.add_transition(from_state, to_state, transition.anchor_offset, transition.direction, transition.read_sym, transition.write_sym, transition.unique_id, True)

		to_state = from_state
		for transition in self.in_transitions:
			from_state = tm_gui.get_state_by_name(transition.from_state)
			tm_gui.add_transition(from_state, to_state, transition.anchor_offset, transition.direction, transition.read_sym, transition.write_sym, transition.unique_id, True)

	def redo_action(self, tm_gui, tape_gui):
		state = tm_gui.get_state_by_name(self.state_name)
		tm_gui.delete_state(state, True)

class Action_AddTransition(MachineAction):
	def __init__(self, transition):
		self.transition_str = TuringTransition_Str(transition)

	def undo_action(self, tm_gui, tape_gui):
		transition = tm_gui.get_state_by_name(self.transition_str.from_state).get_transition_by_id(self.transition_str.unique_id)
		tm_gui.delete_transition(transition, True)

	def redo_action(self, tm_gui, tape_gui):
		from_state = tm_gui.get_state_by_name(self.transition_str.from_state)
		to_state = tm_gui.get_state_by_name(self.transition_str.to_state)
		tm_gui.add_transition(from_state, to_state, self.transition_str.anchor_offset, self.transition_str.direction, self.transition_str.read_sym, 
								self.transition_str.write_sym, self.transition_str.unique_id, True)

class Action_DeleteTransition(MachineAction):
	def __init__(self, transition):
		self.transition_str = TuringTransition_Str(transition)
		
	def undo_action(self, tm_gui, tape_gui):
		from_state = tm_gui.get_state_by_name(self.transition_str.from_state)
		to_state = tm_gui.get_state_by_name(self.transition_str.to_state)
		tm_gui.add_transition(from_state, to_state, self.transition_str.anchor_offset, self.transition_str.direction, self.transition_str.read_sym, 
								self.transition_str.write_sym, self.transition_str.unique_id, True)

	def redo_action(self, tm_gui, tape_gui):
		transition = tm_gui.get_state_by_name(self.transition_str.from_state).get_transition_by_id(self.transition_str.unique_id)
		tm_gui.delete_transition(transition, True)

class Action_ChangeStateName(MachineAction):

	def __init__(self, prev_name, curr_name):
		self.prev_name = prev_name
		self.curr_name = curr_name

	def undo_action(self, tm_gui, tape_gui):
		state = tm_gui.get_state_by_name(self.curr_name)
		tm_gui.update_graphic_ins(state.change_name,
                                                      [self.prev_name])
	
	def redo_action(self, tm_gui, tape_gui):
		state = tm_gui.get_state_by_name(self.prev_name)
		tm_gui.update_graphic_ins(state.change_name,
                                                      [self.curr_name])

class Action_ChangeStateFinal(MachineAction):

	def __init__(self, state_name, prev_bool, curr_bool):
		self.state_name = state_name
		self.prev_bool = prev_bool
		self.curr_bool = curr_bool

	def undo_action(self, tm_gui, tape_gui):
		state = tm_gui.get_state_by_name(self.state_name)
		tm_gui.update_graphic_ins(state.set_final_state,
                                                  [self.prev_bool])
	
	def redo_action(self, tm_gui, tape_gui):
		state = tm_gui.get_state_by_name(self.state_name)
		tm_gui.update_graphic_ins(state.set_final_state,
                                                  [self.curr_bool])

class Action_ChangeStateStart(MachineAction):

	def __init__(self, state_name, prev_bool, curr_bool, prev_state_name):
		self.state_name = state_name
		self.prev_state_name = prev_state_name
		self.prev_bool = prev_bool
		self.curr_bool = curr_bool

	def undo_action(self, tm_gui, tape_gui):
		state = tm_gui.get_state_by_name(self.state_name)
		# This means the user decided to remove the start property. (Easy case)
		if self.prev_bool:
			tm_gui.update_graphic_ins(state.set_start_state,
                                                     [True])
			tm_gui.start_state = state
		# This is a bit harder. Setting a state to be a start state potentially removes this property from another state.
		else:
			tm_gui.update_graphic_ins(state.set_start_state,
                                                          [False])
			if self.prev_state_name:
				prev_state = tm_gui.get_state_by_name(self.prev_state_name)
				tm_gui.update_graphic_ins(prev_state.set_start_state,
                                                          [True])
				tm_gui.start_state = prev_state
			else:
				tm_gui.start_state = None

	def redo_action(self, tm_gui, tape_gui):
		state = tm_gui.get_state_by_name(self.state_name)
		
		if self.curr_bool:
			if self.prev_state_name:
				prev_state = tm_gui.get_state_by_name(self.prev_state_name)
				tm_gui.update_graphic_ins(prev_state.set_start_state,
                                                          [False])
			tm_gui.update_graphic_ins(state.set_start_state,
                                                          [True])
			tm_gui.start_state = state
		else:
			tm_gui.update_graphic_ins(state.set_start_state,
                                                          [False])
			tm_gui.start_state = None

class Action_MoveObject(MachineAction):

	def __init__(self, unique_id, prev_pos, curr_pos):
		self.unique_id = unique_id
		self.prev_pos = prev_pos
		self.curr_pos = curr_pos

	def undo_action(self, tm_gui, tape_gui):
		obj = tm_gui.get_obj_by_id(self.unique_id)
		if obj.type == 'transition':
			tm_gui.update_graphic_ins(obj.set_anchor, [self.prev_pos])
		else:
			tm_gui.update_graphic_ins(obj.set_position, [self.prev_pos])

	def redo_action(self, tm_gui, tape_gui):
		obj = tm_gui.get_obj_by_id(self.unique_id)
		if obj.type == 'transition':
			tm_gui.update_graphic_ins(obj.set_anchor, [self.curr_pos])
		else:
			tm_gui.update_graphic_ins(obj.set_position, [self.curr_pos])

class Action_TransDir(MachineAction):

	def __init__(self, unique_id, prev_dir, curr_dir):
		self.unique_id = unique_id
		self.prev_dir = prev_dir
		self.curr_dir = curr_dir

	def undo_action(self, tm_gui, tape_gui):
		transition = tm_gui.get_obj_by_id(self.unique_id)
		tm_gui.update_graphic_ins(transition.update_transition_vals, [self.prev_dir, None, None])

	def redo_action(self, tm_gui, tape_gui):
		transition = tm_gui.get_obj_by_id(self.unique_id)
		tm_gui.update_graphic_ins(transition.update_transition_vals, [self.curr_dir, None, None])

class Action_TransRead(MachineAction):

	def __init__(self, unique_id, prev_read, curr_read):
		self.unique_id = unique_id
		self.prev_read = prev_read
		self.curr_read = curr_read

	def undo_action(self, tm_gui, tape_gui):
		transition = tm_gui.get_obj_by_id(self.unique_id)
		tm_gui.update_graphic_ins(transition.update_transition_vals, [None, self.prev_read, None])

	def redo_action(self, tm_gui, tape_gui):
		transition = tm_gui.get_obj_by_id(self.unique_id)
		tm_gui.update_graphic_ins(transition.update_transition_vals, [None, self.curr_read, None])

class Action_TransWrite(MachineAction):

	def __init__(self, unique_id, prev_write, curr_write):
		self.unique_id = unique_id
		self.prev_write = prev_write
		self.curr_write = curr_write

	def undo_action(self, tm_gui, tape_gui):
		transition = tm_gui.get_obj_by_id(self.unique_id)
		tm_gui.update_graphic_ins(transition.update_transition_vals, [None, None, self.prev_write])

	def redo_action(self, tm_gui, tape_gui):
		transition = tm_gui.get_obj_by_id(self.unique_id)
		tm_gui.update_graphic_ins(transition.update_transition_vals, [None, None, self.curr_write])

class Action_ChangeTape(MachineAction):
	def __init__(self, prev_tape, curr_tape):
		self.prev_tape = prev_tape
		self.curr_tape = curr_tape

	def undo_action(self, tm_gui, tape_gui):
		tape_gui.set_initial_tape(self.prev_tape)

	def redo_action(self, tm_gui, tape_gui):
		tape_gui.set_initial_tape(self.curr_tape)

class TuringTransition_Str():

	def __init__(self, transition):

		self.from_state = transition.from_state.name
		self.to_state = transition.to_state.name
		self.anchor_offset = (transition.anchor_offset[0], transition.anchor_offset[1])
		self.direction = transition.direction
		self.read_sym = transition.read_sym
		self.write_sym = transition.write_sym
		self.unique_id = transition.unique_id