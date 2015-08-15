# Python 2.7.9 uses integer division by default for some reason.
from __future__ import division

# File name: layouts.py
import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.popup import Popup

from machinescreen import MachineScreen
from turingtape import TuringTape
from touchhandler import TouchHandler
from turingsimulator import TuringSimulator
from xmlparser import XmlParser
from undohandler import *

from kivy.vector import Vector
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.properties import BooleanProperty
from kivy.logger import Logger

import os

# Android import only
try:
    from jnius import autoclass
except:
    pass

# Allows native support of platform specific stuff (vibrations, email etc)
from plyer_lach import email
# Allows us to check what platform we are on
from plyer_lach.utils import Platform

# from kivy.core.window import Window
# import random

from kivy.config import Config
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '800')
# Config.set('modules', 'monitor', '1')
# Config.set('graphics', 'fullscreen', '1')

kivy.require('1.9.0')
Builder.load_file('speedslider.kv')
Builder.load_file('touchhandler.kv')
Builder.load_file('machinescreen.kv')
Builder.load_file('boundedinput.kv')
Builder.load_file('turingtape.kv')

# Used to block touch propagation.
class MenuLayoutGrid(GridLayout):

    def on_touch_down(self, touch):
        super(MenuLayoutGrid, self).on_touch_down(touch)
        if self.collide_point(*touch.pos):
            return True

# Used again to block touch propagation.
class MenuLayoutStack(StackLayout):
    def on_touch_down(self, touch):
        super(MenuLayoutStack, self).on_touch_down(touch)
        if self.collide_point(*touch.pos):
            return True

# POPUP DIALOGS (see main.kv for their definitions)
class ConfirmDialog(FloatLayout):
    func_cancel = ObjectProperty(None)
    func_new_machine = ObjectProperty(None)

class EditTapeDialog(FloatLayout):
    func_cancel = ObjectProperty(None)
    func_change_tape = ObjectProperty(None)

class StateNameDialog(FloatLayout):
    func_cancel = ObjectProperty(None)
    func_change_name = ObjectProperty(None)

class LoadDialog(FloatLayout):
    func_load = ObjectProperty(None)
    func_cancel = ObjectProperty(None)
    file_root = StringProperty()
    save_path = StringProperty()

class SaveDialog(FloatLayout):
    func_save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    func_cancel = ObjectProperty(None)
    file_root = StringProperty()
    save_path = StringProperty()

"""
Desc: The Main app. This gets called straight away when kivy is opened.

Note: For most of the functions in this file you will see the arguments structured as:
        (self, instance, variable)
      These functions are referenced in the .kv file and are used for interactions with
      buttons, checkboxes, textboxes and other custom binds.
      instance - the object raising the event
      variable - the bound variable which causes the event raise.

"""
class Main(FloatLayout):

    intent_file = StringProperty(None)
    intent_ready = BooleanProperty()

    """
    Desc: This is the root of the app. All widgets are placed on top of this and
          all of the main plugins (turing_simulator, undo_handler etc) have references here.
    """
    def __init__(self, **kwargs):

        super(Main, self).__init__(**kwargs)

        # For use in android when opening the app with another .tm file.
        self.bind(intent_ready=self.use_intent)
        
        self.undo_handler = UndoHandler()

        self.init_binds()

        self.create_directories()

        self.intent_ready = False
        self.tape_resized = False
        self.tm_resized = False
        
        self.curr_machine_name = 'untitled.tm'
        self.selected_state = None
        self.selected_transition = None
        self.instant_run = False
        self.mode = 'edit'

    """
    Desc: This function achieves two things:
          - Creates strong references to widgets which can be removed (otherwise GC will clear them)
          - Creates various binds (ie event listeners) to our objects
    """
    def init_binds(self):
        # Get strong references of widgets which can be removed. (Stops weak
        # ref error)
        self.speed_slider = self.ids._slider.__self__
        self.speed_slider.visible = False
        self.remove_widget(self.speed_slider)
        self.speed_slider.bind(value=self.update_sim_speed)

        # Main Menu (top left)
        self.main_menu = self.ids._main_menu.__self__
        self.main_menu.visible = False
        self.remove_widget(self.main_menu)

        # State Menu
        self.state_menu = self.ids._state_menu.__self__
        self.state_menu.visible = False
        self.remove_widget(self.state_menu)

        # Transition menu
        self.trans_menu = self.ids._transition_menu.__self__
        self.trans_menu.visible = False
        self.remove_widget(self.trans_menu)

        # Halt notifier
        self.halt_notifier = self.ids._halt_notifier.__self__
        self.halt_notifier.visible = False
        self.remove_widget(self.halt_notifier)

        # Undo/Redo button layout
        self.undo_redo_layout = self.ids._undo_redo_layout.__self__
        self.undo_redo_layout.visible = True

        # Undo/Redo button references
        self.undo_btn = self.ids._undo_btn
        self.redo_btn = self.ids._redo_btn
        self.redo_btn.disabled = True
        self.undo_btn.disabled = True

        # Tape GUI
        self.tape_gui = self.ids._tape_gui.__self__
        self.tape_gui.bind(size=self.resize_tape_gui)

        # Run Mode Menu (step forward, backward, pause etc.)
        self.run_mode_menu = self.ids._run_mode_menu.__self__
        self.run_mode_menu.visible = False
        self.remove_widget(self.run_mode_menu)
        
        # State menu children (ids are tied to root for some reason)
        self.state_menu_name_btn = self.ids._state_name_btn
        self.state_menu_start_cb = self.ids._state_start_cb
        self.state_menu_final_cb = self.ids._state_final_cb
        self.state_menu_delete_btn = self.ids._state_delete_btn

        # Transition menu children
        self.trans_menu_left_btn = self.ids._trans_left_btn
        self.trans_menu_right_btn = self.ids._trans_right_btn
        self.trans_menu_read_tb = self.ids._trans_read_tb
        self.trans_menu_write_tb = self.ids._trans_write_tb

        # Set binds for state menu check boxes.
        self.state_menu_start_cb.bind(active=self.state_menu_set_start)
        self.state_menu_final_cb.bind(active=self.state_menu_set_final)

        # Handles resizing (only necessary for desktop implementation)
        self.main_space = self.ids._main_space.__self__
        self.main_space.bind(size=self.resize_tm_gui)

        # Turing machine gui binds
        self.tm_gui = self.ids._machinescreen.__self__
        self.tm_gui.undo_handler = self.undo_handler
        self.tm_gui.bind(close_menus=self.close_machine_menus)
        self.tm_gui.bind(selected_state=self.open_state_menu)
        self.tm_gui.bind(selected_transition=self.open_trans_menu)

        # Touch Handler Binds (Bound to machinescreen functions)
        self.touchhandler = self.ids._touch_handler.__self__
        self.touchhandler.bind(click_triggered=self.tm_gui.handle_click)
        self.touchhandler.bind(hold_triggered=self.tm_gui.handle_hold)
        self.touchhandler.bind(double_triggered=self.tm_gui.handle_double_touch)
        self.touchhandler.bind(curr_touch_down=self.tm_gui.handle_touch_down)
        self.touchhandler.bind(move_triggered=self.tm_gui.handle_touch_move)
        self.touchhandler.bind(curr_touch_up=self.tm_gui.handle_touch_up)

        # We use this to actually run the machine.
        self.turing_simulator = TuringSimulator(self.tm_gui, self.tape_gui)
        self.turing_simulator.bind(machine_halted=self.open_halt_notifier)
        self.turing_simulator.bind(curr_step=self.update_step_slider)
        self.update_sim_speed(None, self.speed_slider.value)

        # Run menu buttons/slider
        self.run_menu_slider = self.ids._run_slider
        self.run_menu_slider.bind(value_normalized=self.change_sim_step)
        self.run_menu_left_btn = self.ids._run_step_left
        self.run_menu_right_btn = self.ids._run_step_right
        self.run_menu_play_pause_btn = self.ids._run_play_pause

        # Buttons we need to disable when the machine is running
        self.main_menu_btn = self.ids._main_menu_btn
        self.edit_tape_btn = self.ids._edit_tape_btn
        self.reset_tape_btn = self.ids._reset_tape_btn

        # Need to change the text on the start/stop button when running
        self.run_machine_btn = self.ids._run_machine_btn
        self.run_speed_btn = self.ids._speed_btn

        self.tm_gui.turing_simulator = self.turing_simulator
        self.tape_gui.turing_simulator = self.turing_simulator

        # Halt notifier label
        self.halt_notifier_label = self.ids._halt_reason_label

        # Giving the undo_handler the references to both of the guis.
        self.undo_handler.tm_gui = self.tm_gui
        self.undo_handler.tape_gui = self.tape_gui

        # Lets us enable/disable the undo buttons depending on what action we're at.
        self.undo_handler.bind(curr_action=self.update_undo_buttons)

    """
    Desc: Regardless of platform, this creates the required directories to store our turing machines.
          We also create a temporary directory for storing files to be shared, and data recovery.
    """
    def create_directories(self):
        platform = str(Platform())
        if platform =='android':
            # Check the android environment for the main 'external' storage dir. Normally the user accessable internal storage.
            android_env = autoclass('android.os.Environment')
            self.internal_path = android_env.getExternalStorageDirectory().toString()
        else:
            # Assuming the C drive is accessable (temporary)
            self.internal_path = 'C:/'

        # Using the internal_path found, we create the required folders to store our data.
        self.save_path = os.path.join(self.internal_path,'Turing Machines')
        if not os.path.exists(self.save_path):
            os.mkdir(self.save_path)

        self.temp_path = os.path.join(self.save_path, 'temp')
        if not os.path.exists(self.temp_path):
            os.mkdir(self.temp_path)

    """
    Desc: Once both of the gui's have been initialised (this happens on the second frame)
          we can load the file given in the intent.
    """
    def use_intent(self, instance, intent_ready):
        if intent_ready:
            Logger.info(str(self.intent_file))
            if self.intent_file:
                self.load_machine_uri(self.intent_file)

    """
    Desc: Resizes the turing machine gui (pretty buggy on desktop) android will only resize once.
    """
    def resize_tm_gui(self, instance, size):
        # This actually builds the turing machine gui (we don't know sizes until second frame)
        self.tm_gui.resize(size, (0, 0))
        self.tm_resized = True
        if self.tm_resized and self.tape_resized:
            self.intent_ready = True
    """
    Desc: Resizes the tape gui. Required as the tape gui will dynamically size the amount of elements shown.
    """
    def resize_tape_gui(self, instance, size):
        self.tape_gui.resize(size)
        self.tape_resized = True
        if self.tm_resized and self.tape_resized:
            self.intent_ready = True

    # --------------------------- TOUCH HANDLERS --------------------------- #
    """
    Desc: If a touch propagates to the root, we close all open main menus.
          Can also be called without an instance, or touch. self.close_menus(None, None)
    """
    def close_menus(self, instance, touch):
        if self.speed_slider.visible:
            self.toggle_speed_slider(None)
        if self.main_menu.visible:
            self.toggle_main_menu(None)
        self.close_halt_notifier(None)
        return True

    # --------------------------- UNDO HANDLER FUNCTIONS -------------------- #
    """
    Desc: Attempts to undo the last action. The button will be disabled if no undos are available.
    """
    def undo_action(self, instance):
        if not instance or instance.collide_point(*instance.last_touch.pos):
            self.close_machine_menus(None, True)
            self.undo_handler.undo_action()
    """
    Desc: Attempts to redo the last undone acton. This button will be also disabled if no redos available.
    """
    def redo_action(self, instance):
        if not instance or instance.collide_point(*instance.last_touch.pos):
            self.close_machine_menus(None, True)
            self.undo_handler.redo_action()
    """
    Desc: Every time an undo/redo is successful the curr_action will change. Depending on the value we 
          enable/disable the undo redo buttons.
    """
    def update_undo_buttons(self, instance, curr_action):
        if curr_action == -1:
            self.undo_btn.disabled = True
        else:
            self.undo_btn.disabled = False
        if curr_action >= self.undo_handler.get_total_actions() - 1:
            self.redo_btn.disabled = True
        else:
            self.redo_btn.disabled = False

    # --------------------------- MAIN MENU FUNCTIONS ----------------------- #
    """
    Desc: Called by the menu button in the top left corner. Opens the main menu.
          Can also be called without a button press. Just parse instance to be None.
          TODO: Add animation here (more slick)
    """
    def toggle_main_menu(self, instance):
        # The collide_point statement ensures the function only continues if the touch was on the button.
        if not instance or instance.collide_point(*instance.last_touch.pos):
            self.close_machine_menus(None, True)
            self.main_menu.visible = not self.main_menu.visible
            if not self.main_menu.visible:
                self.remove_widget(self.main_menu)
            else:
                self.add_widget(self.main_menu)

    """
    Desc: Opens up a confirmation popup for creating a new machine.
    """
    def main_menu_new_tm(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            content = ConfirmDialog(func_cancel = self.main_menu_dismiss_popup, func_new_machine=self.create_new_machine)
            self._popup = Popup(content=content, title='New Machine', size_hint=(.5,.35))
            self._popup.open()
    """
    Desc: Creates a new machine. Wipes both the tape and the machine gui.
    """
    def create_new_machine(self):
        self.close_menus(None, True)
        self.undo_btn.disabled = True
        self.redo_btn.disabled = True
        self.tape_gui.set_initial_tape('')
        self.tm_gui.create_new_machine()
        self._popup.dismiss()

    """
    Desc: Opens the save dialog. Uses the built in kivy directory explorer.
    """
    def main_menu_toggle_save(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            content = SaveDialog(func_save=self.save_machine, func_cancel=self.main_menu_dismiss_popup, file_root=self.internal_path, save_path=self.save_path)
            self._popup = Popup(content=content, title='Save Machine',
                                size_hint=(0.9, 0.9))
            self._popup.open()
    """
    Desc: Opens the load dialog. Uses the built in kivy directory explorer.
    """
    def main_menu_toggle_load(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            content = LoadDialog(func_load=self.load_machine, func_cancel=self.main_menu_dismiss_popup, file_root=self.internal_path, save_path=self.save_path)
            self._popup = Popup(content=content, title='Load Machine',
                                size_hint=(0.9, 0.9))
            self._popup.open()
    """
    Desc: Used by all of the popup instances as a function to shut them.
    """
    def main_menu_dismiss_popup(self):
        self._popup.dismiss()

    """
    Desc: Saves the current machine temporarily and uses the OS's respective sharing service to send it.
    """
    def main_menu_share_machine(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            # Creating the temp machine file.
            temp_path = self.temp_save_machine()
            if temp_path:
                email.send(text='Check out this Turing Machine', file_path=temp_path)

    # --------------------------- SAVE / LOAD FUNCTIONS ------------------------ #


    """
    Desc: Given the proper path and file name, saves a .tm file (which is just xml)
          Any path/file combo can be given here, any issues will be caught by the xml class.
    """
    def save_machine(self, file_path, file_name):
        file_name = file_name.strip()
        if file_name != '':
            if file_name[-3:] != '.tm':
                file_name = file_name + '.tm'
            full_path = os.path.join(file_path, file_name)
            io_success = XmlParser.save_machine(full_path, self.tm_gui, self.tape_gui)

            if io_success:
                self.curr_machine_name = file_name
                self.close_menus(None, None)
                self._popup.dismiss()

    """
    Desc: Saves the current machine to the temp.tm file in the temporary directory (see self.temp_path)
    Returns: The path of the temp file.
    """
    def temp_save_machine(self):
        full_path = os.path.join(self.temp_path, self.curr_machine_name)
        io_success = XmlParser.save_machine(full_path, self.tm_gui, self.tape_gui)
        if io_success:
            return full_path
        return None

    """
    Desc: Attempts to load a .tm file at the given path. If this fails (such as failing half way through a load)
          a new blank machine will be created.
          TODO: Give user feedback on failed loads.
    """
    def load_machine(self, file_path, file_name):
        if len(file_name) != 0:
            full_path = os.path.join(file_path, file_name[0])
            io_success = XmlParser.load_machine(full_path, self.tm_gui, self.tape_gui)

            if io_success:
                self.curr_machine_name = file_name[0]
                self.close_menus(None, None)
                self._popup.dismiss()
            else:
                self.tm_gui.create_new_machine()
    """
    Desc: Used by android when loading from an intent. The intent provides a full path.
    """
    def load_machine_uri(self, full_path):
        io_success = XmlParser.load_machine(full_path, self.tm_gui, self.tape_gui)

        if not io_success:
            self.tm_gui.create_new_machine()

    # --------------------------- RUN MENU FUNCTIONS --------------------------- #
    """
    Desc: Toggles the app mode between 'edit' and 'running'. 
          This is pretty ugly, needs a redo. Too many buttons and things enabled and disabled.
          TODO: MAKE THIS NICER.
    """
    def run_menu_change_mode(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            #if not self.turing_simulator.running:
            if self.mode == 'edit':
                self.close_menus(None, None)
                self.close_machine_menus(None, True)

                self.edit_disable_buttons()
                        
                if self.turing_simulator.enter_run_mode():
                    self.mode = 'running'

                    self.run_menu_play_pause_btn.text = 'Play'
                    self.run_menu_left_btn.disabled = True
                    self.run_menu_right_btn.disabled = False
                    self.run_menu_slider.disabled = False
                    self.run_menu_slider.value_normalized = 1

                    self.undo_redo_layout.visible = False
                    self.remove_widget(self.undo_redo_layout)

                    if not self.run_mode_menu.visible:
                        self.add_widget(self.run_mode_menu)
                        self.run_mode_menu.visible = True
                    
                    self.run_machine_btn.text = 'Edit Mode'
                else:
                    self.open_halt_notifier_str('No initial state. Cannot enter run mode.')

            else:
                self.mode = 'edit'

                self.edit_enable_buttons()
                self.run_machine_btn.text = 'Run Mode'
                self.turing_simulator.exit_run_mode()

                if self.run_mode_menu.visible:
                    self.remove_widget(self.run_mode_menu)
                    self.run_mode_menu.visible = False

                if not self.undo_redo_layout.visible:
                    self.undo_redo_layout.visible = True
                    self.add_widget(self.undo_redo_layout)
    
    """
    Desc: Disables buttons not used in run mode.
    """   
    def edit_disable_buttons(self):
        self.main_menu_btn.disabled = True
        self.edit_tape_btn.disabled = True
        self.reset_tape_btn.disabled = True
    """
    Desc: Re-enables buttons used in edit mode.
    """  
    def edit_enable_buttons(self):
        self.main_menu_btn.disabled = False
        self.edit_tape_btn.disabled = False
        self.reset_tape_btn.disabled = False

    # ------------------------ RUN MODE FUNCTIONS ----------------- #
    """
    Desc: Disables buttons in run mode when the machine is being run by the clock.
    """  
    def run_menu_disable_buttons(self):
        self.run_menu_left_btn.disabled = True
        self.run_menu_right_btn.disabled = True
        self.run_menu_slider.disabled = True

    """
    Desc: Enables buttons in run mode after the clock has been paused or finished.
    """  
    def run_menu_enable_buttons(self):
        if self.turing_simulator.curr_step > 0:
            self.run_menu_left_btn.disabled = False
        self.run_menu_right_btn.disabled = False
        self.run_menu_slider.disabled = False
        self.run_menu_play_pause_btn.disabled = False
        self.run_speed_btn.disabled = False
    
    # These next few are pretty self explanatory. 
    def run_menu_step_back(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            left_max = self.turing_simulator.step_machine_back(True)
            if left_max:
                self.run_menu_left_btn.disabled = True

    def run_menu_step_forward(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            if self.turing_simulator.step_machine_forward(True):
                self.run_menu_left_btn.disabled = False

    def run_menu_play_pause(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            if self.turing_simulator.running:
                self.run_menu_play_pause_btn.text = 'Play'

                # (re)Enable the run_menu buttons 
                self.run_menu_enable_buttons()
                self.turing_simulator.pause_machine()
            else:
                # Disable the run_menu buttons (except pause btn)
                self.run_menu_play_pause_btn.text = 'Pause'
                self.run_menu_disable_buttons()

                # Run the machine via the clock.
                self.turing_simulator.run_machine()

    """
    Desc: Updates the step slider when machine steps forward/backwards. 
          This function is disabled when the user is moving the slider themselves
          (or we get an endless loop of callbacks)
    """
    def update_step_slider(self, instance, curr_step):
        if self.run_menu_slider.touches_on == 0:
            if self.turing_simulator.total_steps <= 1:
                self.run_menu_slider.value_normalized = 1
            else:
                val_norm = curr_step/(self.turing_simulator.total_steps-1)
                if val_norm > 1:
                    val_norm = 1
                self.run_menu_slider.value_normalized = val_norm
    """
    Desc: Handles the user moving the slider to step through the machine.
          Pass the simulator a value between 0-1 and the simulator will find the proper step to skip to.
    """
    def change_sim_step(self, instance, norm_value):
        if self.run_menu_slider.touches_on > 0:
            left_max = self.turing_simulator.change_step_norm(norm_value)
            if left_max:
                self.run_menu_left_btn.disabled = True
            else:
                self.run_menu_left_btn.disabled = False
    """
    Desc: Hides and shows the speed slider.
    """  
    def toggle_speed_slider(self, instance):
        if not instance or instance.collide_point(*instance.last_touch.pos):
            self.close_machine_menus(None, True)
            self.speed_slider.visible = not self.speed_slider.visible
            if not self.speed_slider.visible:
                self.remove_widget(self.speed_slider)
            else:
                self.add_widget(self.speed_slider)
    """
    Desc: Bound the speed slider, updates the simulator speed when it runs clocked.
    """            
    def update_sim_speed(self, instance, speed):
        # The simulator run_speed is from 0 to 60.
        # 1 = 1 movement per second
        # 60 = 60 movements per second (way too fast)
        self.turing_simulator.run_speed = .5 + (speed/200)*(speed/200)*(speed/200)*60
    """
    Desc: The notifier which opens when the machine has halted.
          TODO: REPLACE THIS WITH KIVY POPUP CLASS.
    """
    def open_halt_notifier(self, instance, halted):
        if halted:
            self.run_menu_play_pause_btn.disabled = True
            self.run_menu_disable_buttons()
            if self.turing_simulator.halt_successful:
                self.open_halt_notifier_str('Machine Stopped: Halt Successful!')
            else:
                self.open_halt_notifier_str('Machine Stopped: Halt Failed!')

    def open_halt_notifier_str(self, halt_reason):
        if halt_reason:
            if not self.halt_notifier.visible:
                self.halt_notifier.visible = True
                self.add_widget(self.halt_notifier)
                self.halt_notifier_label.text = halt_reason
            
            # Need to disable other run buttons here too.
            self.run_machine_btn.disabled = True
            self.run_speed_btn.disabled = True

    def close_halt_notifier(self, instance):
        if not instance or instance.collide_point(*instance.last_touch.pos):
            if self.halt_notifier.visible:
                self.halt_notifier.visible = False
                self.remove_widget(self.halt_notifier)

                self.run_machine_btn.disabled = False

                self.run_menu_play_pause_btn.text = 'Play'
                self.run_menu_enable_buttons()

                if self.mode == 'edit':
                    self.edit_enable_buttons()
        
    # ----------------------------- TAPE MENU FUNCTIONS ---------------- #
    """
    Desc: Creates the pop up used to edit the tape. 
    """ 
    def toggle_tape_menu(self, instance):
        if not instance or instance.collide_point(*instance.last_touch.pos):
            content = EditTapeDialog(func_cancel = self.main_menu_dismiss_popup, func_change_tape=self.tape_menu_change_tape)
            content.ids._tape_edit_tb.text = self.tape_gui.get_tape_str()
            self._popup = Popup(content=content, title='Change Tape',
                                size_hint=(0.9, 0.25), separator_height='2dp')
            self._popup.pos_hint = {'center_x': .5, 'y':.65}
            self._popup.open()
    """
    Desc: Used by the edit tape popup to change the initial contents of the tape. (Can be called by anything however)
    """ 
    def tape_menu_change_tape(self, tape_txt):
        self.undo_handler.add_action(Action_ChangeTape(self.tape_gui.get_tape_str(), tape_txt))
        self.tape_gui.set_initial_tape(tape_txt)
        self._popup.dismiss()

    """
    Desc: Finds the first non-blank character on the tape and moves the head of the tape to this position.
    """ 
    def run_menu_reset_tape_head(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            self.tape_gui.reset_tape_head()

    # --------------------------- STATE MENU FUNCTIONS --------------------- #
    """
    Desc: Waits for the 'state' ObjectProperty to be set by the tm_gui. If a state is selected the state
          menu is opened (or moved if it was already open)
    """ 
    def open_state_menu(self, instance, state):
        if state:
            if not self.state_menu.visible:
                self.state_menu.visible = True
                self.add_widget(self.state_menu)

            # This is done so bind functions attached to the menu don't affect
            # states (they still fire).
            self.selected_state = None
            self.state_menu_name_btn.text = state.name
            self.state_menu.pos = self.tm_gui.world_to_screen(
                Vector(state.pos) + Vector(state.radius + 3, 0))[0:2]
            self.state_menu_start_cb.active = state.start_state
            self.state_menu_final_cb.active = state.final_state
            self.selected_state = state

            # Shift the menu so it won't leave the screen.
            if self.state_menu.pos[1] + self.state_menu.height > self.height:
                self.state_menu.pos = (
                    self.state_menu.pos[0], self.height - self.state_menu.height - 5)
            if self.state_menu.pos[0] + self.state_menu.width > self.width:
                scaled_radius = self.tm_gui.previous_scale * \
                    (state.radius + 3)
                self.state_menu.pos = (self.state_menu.pos[
                                       0] - self.state_menu.width - 2 * (scaled_radius), self.state_menu.pos[1])
    """
    Desc: Bound to the state menu delete button, deletes the current state selected.
    """ 
    def state_menu_delete(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            if self.selected_state:
                self.tm_gui.delete_state(self.selected_state)
                self.close_machine_menus(None, True)
    """
    Desc: Opens up the state name dialog. (This is done to keep all of the textboxes in the app above the halfway point.)
    """ 
    def state_menu_name_diag(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            content = StateNameDialog(func_cancel = self.main_menu_dismiss_popup, func_change_name = self.state_menu_update_txt)
            content.ids._name_edit_tb.text = instance.text
            self._popup = Popup(content=content, title='Change State Name',
                                size_hint=(0.5, 0.25))
            self._popup.pos_hint = {'center_x': .5, 'y':.7}
            self._popup.open()
    """
    Desc: Error checks the new inputted name. If it already exists it will not accept.
          TODO: Add user notifications for invalid inputs.
    """
    def state_menu_update_txt(self, text):
        if self.selected_state:
            if text == '':
                text = ' '
            text = text.strip()[0:7]
            # We don't want states with the same names. (Need to add a notifier here)
            if self.selected_state.name == text or not self.tm_gui.get_state_by_name(text):
                self.undo_handler.add_action(Action_ChangeStateName(self.selected_state.name, text))
                self.tm_gui.update_graphic_ins(self.selected_state.change_name,
                                                      [text])
                self.state_menu_name_btn.text = text
                self._popup.dismiss()
    """
    Desc: Sets the currently selected state to be the starting state. As there can only be one starting state
          this function will also take the start state property from the previous state (if it exists)
    """ 
    def state_menu_set_start(self, instance, active):
        if self.selected_state:
            # Checking if we already have a start state
            if active:
                prev_name = None
                if self.tm_gui.start_state:
                    # This start state will be overwritten, removing arrow graphic.
                    self.tm_gui.update_graphic_ins(self.tm_gui.start_state.set_start_state,
                                                          [False])
                    prev_name = self.tm_gui.start_state.name

                self.undo_handler.add_action(Action_ChangeStateStart(self.selected_state.name, False, True, prev_name))
                # The new start state is the current selection.
                self.tm_gui.start_state = self.selected_state
            # If this occurs, we must be removing our start state. (The machine
            # can't run now)
            if not active:
                self.undo_handler.add_action(Action_ChangeStateStart(self.selected_state.name, True, False, None))
                self.tm_gui.start_state = None

            # Either way we have to toggle the arrow graphic on the state.
            self.tm_gui.update_graphic_ins(self.selected_state.set_start_state,
                                                  [active])
    """
    Desc: Toggles the selected state between being a final state or not.
    """ 
    def state_menu_set_final(self, instance, active):
        if self.selected_state:
            if self.selected_state.final_state is not active:
                self.undo_handler.add_action(Action_ChangeStateFinal(self.selected_state.name, self.selected_state.final_state, active))
                self.tm_gui.update_graphic_ins(self.selected_state.set_final_state,
                                                  [active])

    # ----------------------- TRANSITION MENU FUNCTIONS ---------------------- #
    """
    Desc: Listens for a selected transition in tm_gui. If a transition is selected then this menu shown.
    """ 
    def open_trans_menu(self, instance, transition):
        if transition:
            if not self.trans_menu.visible:
                self.trans_menu.visible = True
                self.add_widget(self.trans_menu)

            # Move the menu to the transitions anchor position.
            self.trans_menu.pos = self.tm_gui.world_to_screen(
                Vector(transition.label_pos) + Vector(transition.tb_size[0] + 5, 0))[0:2]

            # Shift the menu so it won't leave the screen.
            if self.trans_menu.pos[1] + self.trans_menu.height > self.height:
                self.trans_menu.pos = (
                    self.trans_menu.pos[0], self.height - self.trans_menu.height - 5)
            if self.trans_menu.pos[0] + self.trans_menu.width > self.width:
                scaled_width = self.tm_gui.previous_scale * \
                    (transition.tb_size[0] + 10)
                self.trans_menu.pos = (self.trans_menu.pos[
                                       0] - self.trans_menu.width - scaled_width, self.trans_menu.pos[1])

            # This is done to stop the bindings replacing the previous transitions values with
            # the newly selected transition.
            self.selected_transition = None

            # Set the values currently in the transition to the menu.
            self.trans_menu_read_tb.text = transition.read_sym
            self.trans_menu_write_tb.text = transition.write_sym

            self.selected_transition = transition

    """
    Desc: Deletes the currently selected transition and closes the transition menu (as you cannot edit it anymore)
    """ 
    def trans_menu_delete(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            if self.selected_transition:
                self.tm_gui.delete_transition(self.selected_transition)
                self.close_machine_menus(None, True)

    """
    Desc: Changes the direction of the transition to be left.
    """ 
    def trans_menu_left(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            if self.selected_transition and self.selected_transition.direction != 'L':
                self.undo_handler.add_action(Action_TransDir(self.selected_transition.get_unique_id(), 'R', 'L'))
                self.tm_gui.update_graphic_ins(self.selected_transition.update_transition_vals,
                                                      ['L', False, False])
    """
    Desc: Changes the direction of the transition to be right.
    """ 
    def trans_menu_right(self, instance):
        if instance.collide_point(*instance.last_touch.pos):
            if self.selected_transition and self.selected_transition.direction != 'R':
                self.undo_handler.add_action(Action_TransDir(self.selected_transition.get_unique_id(), 'L', 'R'))
                self.tm_gui.update_graphic_ins(self.selected_transition.update_transition_vals,
                                                      ['R', False, False])
    """
    Desc: Changes the write symbol of the transition.
          TODO: REIMPLEMENT THIS WHEN THE ALPHABET IS PROPERLY IMPLEMENTED
    """ 
    def trans_menu_write_txt(self, instance, text):
        if self.selected_transition:
            if text == '':
                text = ' '

            symbol = text[0:1]
            if symbol != self.selected_transition.write_sym:
                if symbol != ' ':
                    self.undo_handler.add_action(Action_TransWrite(self.selected_transition.get_unique_id(), self.selected_transition.write_sym, symbol))
                    self.tm_gui.update_graphic_ins(self.selected_transition.update_transition_vals,
                                                  [False, False, symbol])
    """
    Desc: Changes the read symbol of the transition.
          TODO: REIMPLEMENT THIS WHEN THE ALPHABET IS PROPERLY IMPLEMENTED
    """ 
    def trans_menu_read_txt(self, instance, text):
        if self.selected_transition:
            if text == '':
                text = ' '

            symbol = text[0:1]
            if symbol != self.selected_transition.read_sym:
                if symbol != ' ':
                    self.undo_handler.add_action(Action_TransRead(self.selected_transition.get_unique_id(), self.selected_transition.read_sym, symbol))
                    self.tm_gui.update_graphic_ins(self.selected_transition.update_transition_vals,
                                                      [False, symbol, False])
    """
    Desc: Closes all of the tm_gui related menus (state menu and transition menu)
    """ 
    def close_machine_menus(self, instance, close_menus):
        if close_menus:
            self.tm_gui.deselect_objects()
            self.selected_state = None
            self.selected_transition = None

            if self.state_menu.visible:
                self.state_menu.visible = False
                self.remove_widget(self.state_menu)

            if self.trans_menu.visible:
                self.trans_menu.visible = False
                self.remove_widget(self.trans_menu)


class MainApp(App):

    def __init__(self, **kwargs):
        super(MainApp, self).__init__(**kwargs)
        self.file_uri = None

    def build(self):
        root = Main(intent_file = self.file_uri)
        return root

    def on_pause(self):
        return True

    def on_resume(self):
        pass

if __name__ == "__main__":
    platform = str(Platform())
    
    # All of this is used to catch intents from android. Currently works well when the app is closed.
    # The way Kivy deals with intents is a bit strange. If the app was already open, kivy will try and 
    # rebuild the entire app despite the fact its already open. This creates many issues and crashes instantly.
    # We couldn't find a solution, (and couldn't find anyone with the same issue)
    # Might report to kivy devs.
    file_uri = None

    if platform == 'android':
        from jnius import cast
        from jnius import autoclass
        import android
        import android.activity
 
        # test for an intent passed to us
        PythonActivity = autoclass('org.renpy.android.PythonActivity')
        activity = PythonActivity.mActivity
        intent = activity.getIntent()
        intent_data = intent.getData()

        try:
            file_uri = intent_data.getPath()
        except AttributeError:
            pass

    main_app = MainApp()
    main_app.file_uri = file_uri
    main_app.run()
