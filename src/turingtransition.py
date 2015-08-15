import kivy
import math

from kivy.vector import Vector
from kivy.core.text import Label
from kivy.graphics import *
from kivy.properties import *

kivy.require('1.7.0')


class TuringTransition():

    instruction_group = None
    trans_line_color = None
    trans_bezier = None
    trans_arrow = None
    trans_label_bg = None
    trans_label = None
    trans_label_rect = None

    """
    @Desc: Initialises a transition for use by the simulator.
    @param: from_state - A TuringState object defining the state the transition begins.
    @param: to_state - A TuringState object defining the state the transition ends.
    @param: anchor_pt - The anchor point of the bezier
    @param: direction - A single character, 'L' for left or 'R' for right.
    @param: read_sym - A single character.
    @param: write_sym - A single character.
    """

    def __init__(self, from_state, to_state, anchor_offset, direction, read_sym, write_sym, unique_id):

        self.type = 'transition'
        
        self.from_state = from_state
        self.to_state = to_state
        self.anchor_offset = anchor_offset
        self.direction = direction
        self.read_sym = read_sym
        self.write_sym = write_sym

        self.unique_id = unique_id

        if self.to_state == self.from_state :
            self.loop = True
        else:
            self.loop = False

        self.setUpCanvas()

    def setUpCanvas(self):
        self.tb_size = (50,20)

        self.instruction_group = InstructionGroup(group=self.get_unique_id())

        self.trans_line_color = Color(.9, .9, .9)
        self.trans_bezier = Line(cap='round', joint='round', width=2, bezier_precision=75)
        self.trans_arrow_color = Color(.5, .5, .5)
        self.trans_arrow = Triangle()

        self.trans_label_bg_color = Color(.6,.6,.6, 1)
        self.trans_label_bg = Rectangle(size=self.tb_size)
        self.trans_label_highlight_color = Color(.9,.9,.9)
        self.trans_label_highlight = Line(cap='round', joint='round', width=1.5)
        self.trans_label = Label(text_size=self.tb_size, halign='center', valign='middle')
        self.trans_label.text = str(self.direction)+': '+str(self.read_sym)+', '+str(self.write_sym)
        self.trans_label.refresh()
        self.trans_label_color = Color(1, 1, 1, 1)
        self.trans_label_rect = Rectangle(size=self.tb_size, texture=self.trans_label.texture)

        self.instruction_group.add(self.trans_line_color)
        self.instruction_group.add(self.trans_bezier)
        self.instruction_group.add(self.trans_arrow_color)
        self.instruction_group.add(self.trans_arrow)

        self.instruction_group.add(self.trans_label_bg_color)
        self.instruction_group.add(self.trans_label_bg)
        self.instruction_group.add(self.trans_label_highlight_color)
        self.instruction_group.add(self.trans_label_highlight)
        self.instruction_group.add(self.trans_label_color)
        self.instruction_group.add(self.trans_label_rect)

        self.update_positions()

    def update_positions(self):
        if self.loop:
            start_pt = Vector(self.from_state.pos)
            self.anchor_pt = start_pt + Vector(self.anchor_offset)
            dir_to_anchor = (Vector(self.anchor_pt)-start_pt).normalize()
            dir_orth_anchor = Vector(-dir_to_anchor[1], dir_to_anchor[0])
            loop_start_pt = start_pt-dir_orth_anchor*20
            loop_end_pt = start_pt+dir_orth_anchor*20

            self.trans_bezier.bezier = (loop_start_pt[0], loop_start_pt[1], self.anchor_pt[0], self.anchor_pt[1],
                                        loop_end_pt[0], loop_end_pt[1])
            self.bez_mid = self.get_bezier_mid(loop_start_pt, self.anchor_pt, loop_end_pt)-dir_orth_anchor*5
            dir_vec = dir_orth_anchor
            dir_orth_vec = dir_to_anchor
        else:
            self.anchor_pt = (Vector(self.from_state.pos)+Vector(self.to_state.pos))/2+self.anchor_offset
            self.trans_bezier.bezier = (self.from_state.pos[0], self.from_state.pos[1], self.anchor_pt[0], self.anchor_pt[1],
                                        self.to_state.pos[0], self.to_state.pos[1])

            dir_vec = (Vector(self.from_state.pos)-Vector(self.to_state.pos)).normalize()
            dir_orth_vec = Vector(-dir_vec[1], dir_vec[0])
            self.bez_mid = self.get_bezier_mid(self.from_state.pos, self.anchor_pt, self.to_state.pos)
        
        arrow_left = self.bez_mid+dir_vec*12+dir_orth_vec*10
        arrow_right = self.bez_mid+dir_vec*12-dir_orth_vec*10
    
        self.trans_arrow.points = (arrow_left[0], arrow_left[1], self.bez_mid[0], self.bez_mid[1], arrow_right[0], arrow_right[1])
        self.label_pos = self.bez_mid - Vector(self.tb_size[0],-self.tb_size[1])/2 + dir_vec*6
        self.trans_label_bg.pos = self.label_pos
        self.trans_label_highlight.rectangle = (self.label_pos[0],self.label_pos[1],self.tb_size[0],self.tb_size[1])
        self.trans_label_rect.pos = self.label_pos

    # transitionMidPointBeforeMove = mousePressedTransition.getMidpoint();
    # moveTransitionClickOffsetX = (int)transitionMidPointBeforeMove.getX() - e.getX();
    # moveTransitionClickOffsetY = (int)transitionMidPointBeforeMove.getY() - e.getY();
    # newCPX = 4.0/3.0 * (midpoint.getX() - (fromState.getX() + TM_State.STATE_RENDERING_WIDTH / 2) / 4.0);
    # newCPY = 4.0/3.0 * (midpoint.getY() - (fromState.getY() + TM_State.STATE_RENDERING_WIDTH / 2) / 4.0);
    # newCPX = 4.0/3.0 * (200 - (startPt[0]) / 4.0);
    # newCPY = 4.0/3.0 * (200 - (startPt[1]) / 4.0);
    # newCPX = 2.0 * midpoint.getX() - 0.5 * (fromState.getX() + TM_State.STATE_RENDERING_WIDTH / 2
    #            + toState.getX() + TM_State.STATE_RENDERING_WIDTH / 2);

    def set_position(self, new_pos):
        label_mid = Vector(self.label_pos) + Vector(self.tb_size)/2
        click_offset = label_mid - Vector(new_pos[0],new_pos[1])

        self.anchor_offset = Vector(self.anchor_offset) - Vector(click_offset)
        self.update_positions()

    def set_anchor(self, new_anchor):
        self.anchor_offset = new_anchor
        self.update_positions()

    def get_position(self):
        return (self.anchor_offset[0], self.anchor_offset[1])

    def collide_point(self, point):
        if point[0] > self.label_pos[0] and point[0] < self.label_pos[0] + self.tb_size[0]:
            if point[1] > self.label_pos[1] - 10 and point[1] < self.label_pos[1] + self.tb_size[1]:
                return True
        return False

    def set_highlight(self, r, g, b):
        self.trans_line_color.r = r
        self.trans_line_color.g = g
        self.trans_line_color.b = b

        self.trans_label_highlight_color.r = r
        self.trans_label_highlight_color.g = g
        self.trans_label_highlight_color.b = b

    def update_transition_vals(self, direction, read_sym, write_sym):
        if direction:
            self.direction = direction
        if read_sym:
            self.read_sym = read_sym
        if write_sym:
            self.write_sym = write_sym

        self.trans_label.label = str(self.direction)+': '+str(self.read_sym)+', '+str(self.write_sym)
        self.trans_label.refresh()

    # Deletes the references states has to this transition
    def delete(self):
        # If we have a loop transition the transition can be deleted twice. This causes errors.
        if self.from_state is not self.to_state:
            self.to_state.remove_in_transition(self)

        self.from_state.remove_out_transition(self)
        self.from_state = None
        self.to_state = None


    def get_instruction_group(self):
        return self.instruction_group

    def get_unique_id(self):
        return str(self.unique_id)

    def get_bezier_mid(self, pt1, anchor, pt2):
        points = []
        segments = 2
        T = [pt1[0], pt1[1], anchor[0], anchor[1], pt2[0], pt2[1]]
        for x in range(segments):
            l = x / (1.0 * segments)
            for i in range(1, len(T)):
                for j in range(len(T) - 2 * i):
                    T[j] = T[j] + (T[j + 2] - T[j]) * l

            points.append(T[0])
            points.append(T[1])
        return Vector(points[2], points[3])