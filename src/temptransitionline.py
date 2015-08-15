import kivy
import math

from kivy.vector import Vector
from kivy.graphics import *

class TempTransitionLine:

    def __init__(self, unique_id):
        self.unique_id = unique_id
        self.displayed = False
        self.define_lines()

    def define_lines(self):
        self.instructionGroup = InstructionGroup(group=str(self.unique_id))
        self.lineColor = Color(1, 1, 0)
        self.mainLine = Line(
            cap='round', joint='round', width=2, bezier_precision=50)
        self.arrowColor = Color(.6,.6,.6)
        self.arrow = Triangle()

        self.instructionGroup.add(self.lineColor)
        self.instructionGroup.add(self.mainLine)
        self.instructionGroup.add(self.arrowColor)
        self.instructionGroup.add(self.arrow)

    def update_line(self, startPt, endPt, loop):
        startPt = Vector(startPt)
        endPt = Vector(endPt)
        if not loop:
            line_vec = Vector(endPt) - Vector(startPt)
            line_vec_unit = line_vec.normalize()
            orth_unit_vec = Vector(-line_vec[1], line_vec[0]).normalize()
            arrow_pt = Vector(endPt)
            other_pt = - line_vec_unit * 12 + Vector(endPt)

            self.mainLine.bezier = (
                startPt[0], startPt[1], endPt[0], endPt[1])
            self.arrowColor.r = 1
            self.arrowColor.g = 1
            self.arrowColor.b = 0
            self.arrow.points = (other_pt[0] - orth_unit_vec[0] * 10, other_pt[1] - orth_unit_vec[1] * 10, arrow_pt[0], arrow_pt[1],
                                 other_pt[0] + orth_unit_vec[0] * 10, other_pt[1] + orth_unit_vec[1] * 10)
        else:
            angle = (180 / math.pi) * math.atan2(
                    endPt[1] - startPt[1], endPt[0] - startPt[0]) - 90
            loop_width = Vector(40,0).rotate(angle)
            width_orth_unit_vec = Vector(-loop_width[1], loop_width[0]).normalize()
            loop_start_pt = startPt-loop_width/2
            loop_end_pt = startPt+loop_width/2
            self.loop_ctrl_pt = startPt+width_orth_unit_vec*125

            self.mainLine.bezier = (
                loop_start_pt[0], loop_start_pt[1], self.loop_ctrl_pt[0], self.loop_ctrl_pt[1], loop_end_pt[0],loop_end_pt[1])

            loop_width_unit = loop_width.normalize()
            arrow_pt = self.get_bezier_mid(loop_start_pt, self.loop_ctrl_pt, loop_end_pt)+loop_width_unit*5
            arrow_left = arrow_pt+width_orth_unit_vec*10-loop_width_unit*10
            arrow_right = arrow_pt-width_orth_unit_vec*10-loop_width_unit*10

            self.arrowColor.r = .9
            self.arrowColor.g = .9
            self.arrowColor.b = .9
            self.arrow.points = (arrow_left[0], arrow_left[1], arrow_pt[0], arrow_pt[1], arrow_right[0], arrow_right[1])

    def get_instruction_group(self):
        return self.instructionGroup

    def get_unique_id(self):
        return str(self.unique_id)

    # Adapted from vertex_instructions_line.pyx to find the mid point of the
    # bezier to place the arrow.
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