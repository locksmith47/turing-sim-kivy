"""
@Author: Lachlan Smith
@Modified: 25/04/2015
@Desc: Stores a turing tape as a deque which can expand
	   infintely left or right.
"""

from collections import deque

class TuringTape:

    """
    @desc: Initialises a new tape by converting the initial tape string
           to a deque. (Each element can look either left or right)
    @param: tape_str - A string containing only characters defined in the alphabet.
    @param: blank_char - The character used to represent a blank character.
    @param: infinite_left - An option to enable/disable the tape moving infinitely left
                (My idea is to make the simulator compatible with Tuatara eventually)
    """

    def __init__(self, tape_str, blank_char, infinite_left):

        self.blank_char = blank_char
        self.set_tape(tape_str)
        self.infinite_left = infinite_left

    def set_tape(self, tape_str):
        if tape_str:
            self.tape = deque(tape_str)
        else:
            self.tape = deque(self.blank_char)
        self.tape_index = 0
        
    def get_curr_letter(self):
        return self.tape[self.tape_index]

    """
    @desc: Used by the simulator to write a character to the current element.
    """

    def write(self, str):
        self.tape[self.tape_index] = str

    """
    @desc: Used by the simulator to move the tape left.
    	   If the next element doesn't exist a new blank element will be created.
   	@return: Returns the newly found character string
   	"""

    def move_left(self):
        if self.tape_index == 0 :
            self.tape.appendleft(self.blank_char)
        else :
            self.tape_index -= 1
        return self.tape_index
    """
    @desc: Used by the simulator to move the tape right.
    	   If the next element doesn't exist a new blank element will be created.
   	@return: Returns the newly found character string
   	"""

    def move_right(self):
        if self.tape_index >= len(self.tape) - 1:
            self.tape.append(self.blank_char)
        self.tape_index += 1
        return self.tape_index
    
    """
    @desc: Returns a list of characters from the given index and total_chars requested.
           blank_char's are filled in for empty/non-existent elements on the tape.
    @param: from_index - an integer to begin at
    @param: total_chars - the total charaters wanted
    @return: Returns a list of characters from the tape.
    """
    def get_characters(self, from_index, total_chars):
        characters = []
        valid_list = []
        neg_list = []
        overflow_list = []
        last_index = from_index + total_chars
        tape_len = len(self.tape)

        # Deal with indicies too small
        if from_index < 0:
            if last_index < 0:
                characters = list(self.blank_char*(total_chars))
                return characters
            neg_list = list(self.blank_char*(from_index*-1))
            from_index = 0

        # Deal with indicies too large
        if last_index > tape_len:
            overflow = last_index - tape_len
            if overflow > total_chars:
                characters = list(self.blank_char*(total_chars))
                return characters
            overflow_list = list(self.blank_char*(overflow))
            last_index = tape_len

        # Deal with elements actually in the tape
        for i in range(from_index,last_index):
            valid_list.append(self.tape[i])

        return neg_list + valid_list + overflow_list

    """
    @desc: Returns the index of the first non blank character.
    """
    def get_first_index(self):
        for index, tapeElement in enumerate(self.tape):
            if tapeElement != self.blank_char:
                return index
        return -1

    """
    @desc: Returns the tape from the first non blank character in string form.
    """
    def get_tape_str(self):
        tape_str = ''

        first_index = self.get_first_index()
        if first_index != -1:
            for i in range(self.get_first_index(), len(self.tape)):
                tape_str = tape_str + self.tape[i]
        else:
            tape_str = ''

        return tape_str

    """
    @desc: Linearly runs through the deque and returns a single string.
           Puts * * around where the head of the tape is currently at.
    """
    def __str__(self):

        tapeStr = ''

        for index, tapeElement in enumerate(self.tape):
            if index == self.tape_index:
                tapeStr += '*' + tapeElement + '*'
            else:
                tapeStr += tapeElement

        return tapeStr
