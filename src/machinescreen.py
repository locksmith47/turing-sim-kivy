import kivy
import math
# import random

from kivy.uix.widget import Widget
from kivy.vector import Vector
from kivy.graphics import *
from kivy.properties import *
from kivy.graphics.transformation import Matrix

from turingstate import TuringState
from turingtransition import TuringTransition
from temptransitionline import TempTransitionLine
from undohandler import *

kivy.require('1.9.0')
"""
    Desc: This is the turing machine gui. All states and transitions are stored here.
    States and Transitions are implemented as normal python classes but also have gfx info in them.
    This way we only have to handle one touch event for the whole widget. Based on this single touch
    we can finely tune what needs to happen to the 'children' of the class.
    TODO: RENAME AS TuringMachineGUI
""" 
class MachineScreen(Widget):

    # Watched by the root app class. Set to True to close menus.
    close_menus = BooleanProperty()

    # Watched by the root app class. If either of these are set to not None, a menu will be shown
    # in the root class.
    selected_state = ObjectProperty(None, allownone=True)
    selected_transition = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(MachineScreen, self).__init__(**kwargs)

        self.start_state = None
        # This gets set by the root widget
        self.undo_handler = None

        self.states = []
        self.transitions = []

        self.handled_touches = []

        # TODO: DON'T HARD CODE THIS
        self.blank_char = '_'

        self.canvas_created = False

        # Used to differentiate between objects.
        self.unique_id = 0

        self.bgGrabbed = False
        self.grabbed_object = None
        self.initial_grab_pt = None
        self.grabPt = (0, 0)

        self.held_state = None

        # Listened to by main.py to close state/transition menus.
        self.close_menus = False
        self.selected_state = None

        # Initial distance between two touches.
        self.initial_dist = 1
        self.multitouch = False
        self.previous_scale = 1
        self.temp_scale = 1

        # We check the simulator to see if its running when handling touches.
        self.turing_simulator = None

        self.state_group = InstructionGroup()
        self.transition_group = InstructionGroup()

        self.transitionline = TempTransitionLine(self.get_unique_id())
    """
    Desc: Each object (for now state and transition) has a unique id. This is used predominately
          in the display queue and in the undo handler.
    """ 
    def get_unique_id(self):
        self.unique_id += 1
        return self.unique_id

    """
    Desc: Creates a new machine by wiping the current states and transitions.
          Clears the frame buffer, and resets the undo_handler.
    """
    def create_new_machine(self):

        # Removing visual components
        self.fbo.bind()
        self.fbo.clear_buffer()
        for state in self.states:

            invalid_transitions = state.delete()
            self.state_group.remove_group(state.get_unique_id())

            for transition in invalid_transitions:
                self.transition_group.remove_group(transition.get_unique_id())

        self.fbo.release()

        self.undo_handler.reset()

        self.states = []
        self.transitions = []
        self.start_state = None

    # ------------------------ GRAPHICS ----------------------- #
    """
    Desc: Called on the first resize (moving from default (100,100) dimensions)
          Builds the frame buffer which we draw everything onto (much faster than individual widgets)
          Also sets up our transformation matricies that we use for scaling and translations.
    """ 
    def initialise_canvas(self, size):
        self.matrix = Matrix()

        with self.canvas:
            self.fbo = Fbo(size=size)
            Color(1, 1, 1, 1)
            self.bg = Rectangle(
                size=self.size, pos=self.pos, texture=self.fbo.texture)
            self.canvas_created = True
        with self.fbo:
            self.matrix_instruction = MatrixInstruction()
            self.matrix_instruction.matrix = self.matrix

        self.fbo.add(self.transition_group)
        self.fbo.add(self.state_group)

    """
    Desc: Bound in the root class, updates the widget size when app size is adjusted.
    """
    def resize(self, size, pos):
        if not self.canvas_created:
            self.initialise_canvas(size)
        self.bg.size = size
    """
    Desc: Adds an instruction group at given index.
    WARNING: Don't add at multiple index's without first clearing the
    original instruction group from the display list.
    """
    def add_at_index(self, ins, index):
        self.fbo.bind()
        self.fbo.clear_buffer()
        self.fbo.insert(index, ins)
        self.fbo.release()
    """
    Desc: Moves an instruction group to the top of another instruction group.
    EG. Moving a state to the top of the state display list.
    The ins must already be in the ins_group or an exception will be raised.
    """
    def add_to_top(self, ins_group, ins, ins_uid):
        self.fbo.bind()
        self.fbo.clear_buffer()
        ins_group.remove_group(ins_uid)
        ins_group.add(ins)
        self.fbo.release()
        self.fbo.ask_update()

    """
    Desc: Updates the screen after the change of a graphic instruction.
    If the graphic instruction doesn't change, this will clear the screen.
    """
    def update_graphic_ins(self, ins, args):
        self.fbo.bind()
        self.fbo.clear_buffer()
        return_value = ins(*args)
        self.fbo.release()
        self.fbo.ask_update()
        return return_value
    """
    Desc: Pans the main fbo by a vector delta.
    """
    def pan(self, delta):
        self.matrix = self.matrix.multiply(
            Matrix().translate(delta[0], delta[1], 0))

        self.fbo.bind()
        self.fbo.clear_buffer()
        self.matrix_instruction.matrix = self.matrix
        self.fbo.release()

    """
    Desc: Zooms the fbo at a world point by a factor. Keeps the screen centred on the zoom.
    """
    def zoom(self, origin, factor):
        self.matrix = self.matrix.multiply(
            Matrix().translate(origin[0], origin[1], 0))
        self.matrix = self.matrix.multiply(
            Matrix().scale(factor, factor, factor))
        self.matrix = self.matrix.multiply(
            Matrix().translate(-origin[0], -origin[1], 0))

        self.fbo.bind()
        self.fbo.clear_buffer()
        self.matrix_instruction.matrix = self.matrix
        self.fbo.release()

    # -------------------- COORDINATE FUNCTIONS --------------------- #
    """
    Desc: Uses the transformation matrix we are using on the fbo to transfer a point on the root screen
    to world space. (Used for adding transitions etc.)
    """
    def screen_to_world(self, screenPos):
        worldPos = self.matrix.inverse().transform_point(
            screenPos[0], screenPos[1] - self.parent.y, 0)
        return worldPos
    """
    Desc: Uses the transformation matrix we are using on the fbo to transfer a point on our world screen to
    the root app screen. (Used for getting the proper point to put state/transition menus at)
    """
    def world_to_screen(self, objPos):
        screenPos = self.matrix.transform_point(objPos[0], objPos[1], 0)
        return (screenPos[0], screenPos[1] + self.parent.y, 0)

    # -------------------- TOUCH EVENT HANDLERS ---------------------- #
    """
    Desc: Handles a touch onto the gui. All touches are stored for later use (with multitouch functionality) and 
    also movement functionality such as dragging a state around.
    """
    def handle_touch_down(self, instance, touch):
        if touch not in self.handled_touches:
            # Set up the reference variable. A single touch won't shut menus
            # but a move (outside stray) or 'click' will shut menu.
            self.close_menus = False
            # Only want to handle at max 2 touches.
            if len(self.handled_touches) < 2:
                self.handled_touches.append(touch)

                if not self.multitouch and len(self.handled_touches) == 2:
                    self.multitouch = True

                    # As this is the first multitouch, we want to close menus, drop held objects etc.
                    self.close_menus = True
                    self.bgGrabbed = False
                    self.grabbed_object = None

                    if self.held_state:
                        self.unhold_state(None)

                if self.multitouch and len(self.handled_touches) == 2:

                    # Set up for scaling.
                    self.initial_dist = Vector(self.handled_touches[0].pos).distance(
                        Vector(self.handled_touches[1].pos))
                    # Remember the current scale before more scaling.
                    self.temp_scale = self.previous_scale
    """
    Desc: Handles a touch up (no matter where it happened, or even if we're tracking it)
    If we are tracking the touch, various things can happen. If its a zoom we stop zooming,
    if we're creating a transition we'll create it etc.
    """
    def handle_touch_up(self, instance, touch):
        # We no longer need to remember the touch, so remove it.
        if touch in self.handled_touches:
            self.handled_touches.remove(touch)

        # To get out of multitouch mode all touches need to be removed. Simplifies things a bit.
        if len(self.handled_touches) == 0:
            self.multitouch = False

        # If a touch and hold had been activated, we need to unhighlight the state.
        self.unhold_state(touch.pos)
        self.bgGrabbed = False
        if self.grabbed_object:
            self.undo_handler.add_action(Action_MoveObject(self.grabbed_object.get_unique_id(),
                                        self.initial_grab_pt,self.grabbed_object.get_position()))
        self.grabbed_object = None
    """
    Desc: Handles a touch move on the gui. We are only interested in moves which origininated on the gui.
    """
    def handle_touch_move(self, instance, move_triggered):
        # Handling new touches to the machine.
        touch = instance.curr_touch_move
        if touch in self.handled_touches:

            if not self.multitouch:
                if touch.strayed:
                    self.close_menus = True
                    if not self.held_state:
                        if not self.grabbed_object and not self.bgGrabbed:
                            self.handle_initial_grab(touch.opos)
                        self.handle_grab(touch.pos)
                    else:
                        self.handle_transition_move(touch)
            else:
                self.handle_scale()
    """
    Desc: Listens to the touchhandler for a click_triggered event. (ie, a quick tap)
          If a transition or state is under the tap, it will be selected and an event will
          be fired too the root app to create the respective menu.
    """
    def handle_click(self, instance, click_triggered):
        if click_triggered and not self.turing_simulator.run_mode:
            world_pos = self.screen_to_world(instance.initial_touch.opos)
            for state in self.states:
                if Vector(world_pos).distance(Vector(state.pos)) < state.radius:

                    if self.selected_transition:
                        self.deselect_objects()
                        self.close_menus = True

                    if self.selected_state and state is not self.selected_state:
                        self.deselect_objects()

                    self.update_graphic_ins(state.set_highlight, (0, 1, 1))
                    # Brings the selected state to the top of the display list.
                    self.add_to_top(self.state_group, state.get_instruction_group(), state.get_unique_id())
                    self.selected_state = state
                    return

            for transition in self.transitions:
                if transition.collide_point(world_pos):

                    if self.selected_state:
                        self.deselect_objects()
                        self.close_menus = True

                    if self.selected_transition and transition is not self.selected_transition:
                        self.deselect_objects()

                    self.update_graphic_ins(transition.set_highlight, (0, 1, 1))
                    self.add_to_top(self.transition_group, transition.get_instruction_group(), transition.get_unique_id())
                    self.selected_transition = transition
                    return

            # If we're at this point we know that no states/transitions have
            # been selected.
            self.close_menus = True
    """
    Desc: Listens to the touchhandler for a hold_triggered event. If this happens ontop of a state we go into 
    transition creation mode.
    """
    def handle_hold(self, instance, hold_triggered):
        if hold_triggered and not self.turing_simulator.run_mode:
            world_pos = self.screen_to_world(instance.initial_touch.opos)
            for state in self.states:
                if Vector(world_pos).distance(Vector(state.pos)) < state.radius:
                    self.update_graphic_ins(state.set_highlight, (1, 1, 0))
                    self.held_state = state
    """
    Desc: Listens to the touchhandler for a double_triggered event. If the double tap is on empty space
    a new state will be created.
    """
    def handle_double_touch(self, instance, double_triggered):
        if double_triggered and not self.turing_simulator.run_mode:
            world_pos = self.screen_to_world(instance.initial_touch.opos)
            for state in self.states:
                if Vector(world_pos).distance(Vector(state.pos)) < state.radius:
                    return
            self.add_state(instance.initial_touch.opos, False)

    # --------------------------  MACHINE FUNCTIONS ------------------------ #
    # (Majority of these will be called by the above touch handlers)

    # Checks if either the background or a state has been selected on the move
    # Background selected: Pan's camera
    # State selected: Move state
    def handle_initial_grab(self, pos):
        world_pos = self.screen_to_world(pos)
        self.grabPt = (world_pos[0], world_pos[1])
        if not self.turing_simulator.run_mode:
            for state in self.states:
                if Vector(world_pos).distance(Vector(state.pos)) < state.radius:
                    self.grabbed_object = state
                    self.add_to_top(self.state_group, state.get_instruction_group(), state.get_unique_id())
                    break
            for transition in self.transitions:
                if transition.collide_point(world_pos):
                    self.grabbed_object = transition
                    self.add_to_top(self.transition_group, transition.get_instruction_group(), transition.get_unique_id())
                    break
        if self.grabbed_object:
            self.initial_grab_pt = self.grabbed_object.get_position()
        else:
            self.bgGrabbed = True

    def handle_grab(self, pos):
        world_pos = self.screen_to_world(pos)
        if self.grabbed_object:
            self.update_graphic_ins(
                self.grabbed_object.set_position, [world_pos])
        elif self.bgGrabbed:
            # pan by the delta position
            self.pan(
                (world_pos[0] - self.grabPt[0], world_pos[1] - self.grabPt[1]))

    def handle_transition_move(self, touch):
        world_pos = self.screen_to_world(touch.pos)
        world_pos = (world_pos[0], world_pos[1])
        if self.transitionline.displayed:
            if Vector(world_pos).distance(Vector(self.held_state.pos)) > self.held_state.radius:
                self.update_graphic_ins(self.transitionline.update_line, (self.held_state.pos,
                                                                          world_pos, False))
            else:
                self.update_graphic_ins(self.transitionline.update_line, (self.held_state.pos,
                                                                          world_pos, True))
        else:
            if Vector(world_pos).distance(Vector(self.held_state.pos)) > self.held_state.radius:
                self.transitionline.update_line(self.held_state.pos,
                                                world_pos, False)
                # Need to remove the held state and re-add it
                self.update_graphic_ins(self.state_group.remove_group, [self.held_state.get_unique_id()])
                self.add_at_index(
                    self.transitionline.get_instruction_group(), 3)
                self.add_at_index(self.held_state.get_instruction_group(), 4)
                self.transitionline.displayed = True

    def handle_scale(self):
        if len(self.handled_touches) == 2:
            new_dist = Vector(self.handled_touches[0].pos).distance(
                Vector(self.handled_touches[1].pos))
            new_scale = (new_dist / self.initial_dist) * self.temp_scale

            if new_scale < .8:
                new_scale = .8
            if new_scale > 3:
                new_scale = 3

            pivot_pt = self.screen_to_world((
                Vector(self.handled_touches[0].pos) +
                Vector(self.handled_touches[1].pos)) / 2)

            self.zoom(pivot_pt, new_scale / self.previous_scale)

            self.previous_scale = new_scale

    # If any states/transitions are selected removes the highlight and forgets
    # the object.
    def deselect_objects(self):
        if self.selected_state:
            # Stop the hold highlight disappearing.
            if self.selected_state is not self.held_state:
                self.update_graphic_ins(
                    self.selected_state.set_highlight, (.8, .8, .8))
            self.selected_state = None

        if self.selected_transition:
            self.update_graphic_ins(
                    self.selected_transition.set_highlight, (.8, .8, .8))
            self.selected_transition = None

    # Handles a touch up after a hold.
    # For now this is when a transition has tried to be created.
    # pos: (x, y) or None if no transition is wanted to be created.
    def unhold_state(self, pos):
        if self.transitionline.displayed:
            if pos:
                world_pos = self.screen_to_world(pos)
                for state in self.states:
                    if Vector(world_pos).distance(Vector(state.pos)) < state.radius:
                        # Create a new transition.
                        self.add_transition(self.held_state, state, None, 'L', self.blank_char, self.blank_char)
                        break
            # Remove the state from the main buffer
            self.update_graphic_ins(
                self.fbo.remove_group, [self.held_state.get_unique_id()])
            # Add it back to the state_group instruction group
            self.update_graphic_ins(self.state_group.add,
                                    [self.held_state.get_instruction_group()])
            # Remove the temporary transition line from the main buffer
            self.update_graphic_ins(
                self.fbo.remove_group, [self.transitionline.get_unique_id()])
            self.transitionline.displayed = False
        if self.held_state:
            self.update_graphic_ins(self.held_state.set_highlight, (.8, .8, .8))
            self.held_state = None

    def add_transition(self, from_state, to_state, anchor_offset, direction, read_sym, write_sym, unique_id = -1, from_undo = False):

        if from_state == to_state:
            if not anchor_offset:
                anchor_offset = Vector(self.transitionline.loop_ctrl_pt) - Vector(from_state.pos)
        else :
            if not anchor_offset:
                anchor_offset = (20, 20)
        if unique_id == -1:
            u_id = self.get_unique_id()
        else:
            u_id = unique_id

        new_transition = TuringTransition(from_state, to_state, anchor_offset, direction, read_sym, write_sym, u_id)
            
        self.transitions.append(new_transition)
        from_state.add_out_transition(new_transition)

        if from_state is not to_state:
            to_state.add_in_transition(new_transition)

        if not from_undo:
            self.undo_handler.add_action(Action_AddTransition(new_transition))

        self.update_graphic_ins(self.transition_group.add, [new_transition.get_instruction_group()])

    def delete_transition(self, transition, from_undo = False):
        if not from_undo:
            self.undo_handler.add_action(Action_DeleteTransition(transition))

        self.update_graphic_ins(self.transition_group.remove_group, [transition.get_unique_id()])
        transition.delete()
        self.transitions.remove(transition)
        
    def add_state(self, new_pos, absolute, name = '', from_undo = False, unique_id = -1):
        if not absolute:
            world_pos = self.screen_to_world(new_pos)
        else:
            world_pos = new_pos

        if name == '':
            state_name = 'state' + str(len(self.states))
            i = 1
            while self.get_state_by_name(state_name):
                state_name = 'state' + str(len(self.states)+i)
                i += 1
        else:
            state_name = name

        self.deselect_objects()

        if unique_id == -1:
            u_id = self.get_unique_id()
        else:
            u_id = unique_id

        new_state = TuringState(world_pos, state_name, u_id)
        self.states.append(new_state)

        self.update_graphic_ins(self.state_group.add, [new_state.get_instruction_group()])

        if not from_undo:
            self.undo_handler.add_action(Action_AddState(state_name, world_pos, new_state.get_unique_id()))

        return new_state

    def delete_state(self, state, from_undo = False):
        # Create the undo action now (before transitions are lost etc)
        if not from_undo:
            print('handle meh')
            self.undo_handler.add_action(Action_DeleteState(state.name, state.pos, state.final_state, state.start_state, state.out_transitions, state.in_transitions, state.get_unique_id()))
        # Makes sure we remove all references of the state
        if state == self.start_state:
            self.start_state = None

        # Remove connected transitions
        invalid_transitions = state.delete()

        # Prepare the fbo for a redraw.
        self.fbo.bind()
        self.fbo.clear_buffer()

        # Remove invalid transitions from display and local storage.
        for transition in invalid_transitions:
            self.transition_group.remove_group(transition.get_unique_id())
            self.transitions.remove(transition)

        # Remove from the display list
        self.state_group.remove_group(state.get_unique_id())

        # Remove from the state list
        self.states.remove(state)

        self.fbo.release()

    def get_state_by_name(self, name):
        for state in self.states:
            if state.name == name:
                return state
        return None

    def get_obj_by_id(self, unique_id):
        for state in self.states:
            if state.get_unique_id() == unique_id:
                return state
        for transition in self.transitions:
            if transition.get_unique_id() == unique_id:
                return transition
        return None


