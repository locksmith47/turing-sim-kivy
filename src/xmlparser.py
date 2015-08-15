try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import os
"""
@Author: Lachlan Smith
@Modified: 9/05/2015
@Desc: This is a class of various XML Parsing functions.
	   It implements loading and saving turing machines.
"""


class XmlParser:

	"""
	STATIC METHOD
	@desc: Loads, from an XML file, a turing machine as specified on the
		   spec sheet. The xml file is then converted to a TuringMachine
		   (see turingmachine.py)
	@param: path - path of a valid XML file.
	@param: tm_gui - the turing machine gui which we can add states/transitions to
	@param: tape_gui - the turing tape gui which we can load the tape into.
	"""
	def load_machine(path, tm_gui, tape_gui):
		try:
			with open(path) as stream:
				tm_str = stream.read()
		except IOError:
			print('Invalid path:' + str(path))
			return False

		try:
		    turingXML = ET.fromstring(tm_str)
		except ET.ParseError:
		    print ('Invalid xml file: ' + str(path))
		    return False

		# TODO: PROPER ERROR CHECKING.
		# TODO: ALPHABET AND BLANK CHARACTER.
		tm_gui.create_new_machine()

		xmlRoot = turingXML

		tape_gui.set_initial_tape(xmlRoot.find('initialtape').text)
		# alphabet = xmlRoot.find('alphabet').text
		# blankChar = xmlRoot.find('blank').attrib['char']
		initial_state_name = xmlRoot.find('initialstate').attrib['name']

		# Parsing final states
		end_states = []

		final_states_XML = xmlRoot.find('finalstates')

		for stateXML in final_states_XML:
		    end_states.append(stateXML.attrib['name'])

		statesXML = xmlRoot.find('states')
		transitions = []

		for stateXML in statesXML:
		    state_name = stateXML.attrib['name']
		    pos = (float(stateXML.attrib['xpos']), float(stateXML.attrib['ypos']))
		    new_state = tm_gui.add_state(pos, True, state_name)

		    if state_name == initial_state_name:
		    	new_state.set_start_state(True)
		    	tm_gui.start_state = new_state

		    if state_name in end_states:
		    	new_state.set_final_state(True)

		    for transitionXML in stateXML:
		        newTransition = (new_state, transitionXML.attrib['newstate'], (float(transitionXML.attrib['ctlx']), 
		        				float(transitionXML.attrib['ctly'])), transitionXML.attrib['move'],
		        				transitionXML.attrib['seensym'], transitionXML.attrib['writesym'])
		        transitions.append(newTransition)

		# Creating transitions
		for t_xml in transitions:
			to_state = tm_gui.get_state_by_name(t_xml[1])
			tm_gui.add_transition(t_xml[0], to_state, t_xml[2], t_xml[3], t_xml[4], t_xml[5])
		tm_gui.undo_handler.reset()
		
		return True

	load_machine = staticmethod(load_machine)

	"""
	STATIC METHOD
	@desc: Uses the two guis to save a .tm file 
	@param: path - path to save the machine at.
	@param: tm_gui - the turing machine gui which we can read states/transitions from
	@param: tape_gui - the turing tape gui which we can read the tape from.
	"""
	def save_machine(path, tm_gui, tape_gui) :
		root = ET.Element('turingmachine')

		ET.SubElement(root, 'alphabet').text = 'ab'
		ET.SubElement(root, 'blank', {'char':'_'})
		tape_str = tape_gui.get_tape_str()
		
		if tape_str == '':
			ET.SubElement(root, 'initialtape').text = '_'
		else:
			ET.SubElement(root, 'initialtape').text = tape_gui.get_tape_str()
		

		if tm_gui.start_state:
			ET.SubElement(root, 'initialstate', {'name':tm_gui.start_state.name})
		else:
			ET.SubElement(root, 'initialstate', {'name':'no_initial_state'})

		finalstates = ET.SubElement(root, 'finalstates')
		states = ET.SubElement(root, 'states')

		for state in tm_gui.states:

			if state.final_state:
				ET.SubElement(finalstates, 'finalstate', {'name':state.name})

			newstate = ET.SubElement(states, 'state', {'name':state.name, 'xpos':str(int(state.pos[0])), 
									'ypos':str(int(state.pos[1]))})

			for transition in state.out_transitions:
				ET.SubElement(newstate, 'transition', {'seensym':transition.read_sym,
				              'writesym':transition.write_sym, 'newstate':transition.to_state.name, 
				              'move':transition.direction,'ctlx':str(int(transition.anchor_offset[0])),
				              'ctly':str(int(transition.anchor_offset[1]))})
					
		machine_str = ET.tostring(root, encoding='utf8', method='xml')

		try:
			with open(path, 'w') as stream:
				stream.write(machine_str)
		except IOError:
			print('Invalid path:' + str(path))
			return False

		return True

	save_machine = staticmethod(save_machine)
