'''
Facades
=======

Interface of all the features available.

'''

__all__ = ('Accelerometer', 'Audio', 'Battery', 'Camera', 'Compass', 'Email',
           'FileChooser', 'GPS', 'Gyroscope', 'IrBlaster', 'Orientation',
           'Notification', 'Sms', 'TTS', 'UniqueID', 'Vibrator')

from plyer_lach.facades.accelerometer import Accelerometer
from plyer_lach.facades.audio import Audio
from plyer_lach.facades.battery import Battery
from plyer_lach.facades.camera import Camera
from plyer_lach.facades.compass import Compass
from plyer_lach.facades.email import Email
from plyer_lach.facades.filechooser import FileChooser
from plyer_lach.facades.gps import GPS
from plyer_lach.facades.gyroscope import Gyroscope
from plyer_lach.facades.irblaster import IrBlaster
from plyer_lach.facades.orientation import Orientation
from plyer_lach.facades.notification import Notification
from plyer_lach.facades.sms import Sms
from plyer_lach.facades.tts import TTS
from plyer_lach.facades.uniqueid import UniqueID
from plyer_lach.facades.vibrator import Vibrator
