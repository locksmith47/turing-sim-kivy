'''
plyer_lach
=====

NOTE: This code is all essentially plyer with a few small additions.
	  The only change here is to facades/email.py and android/email.py
	  Needed to rename the classes as plyer is already included with kivy 
	  Caused confusion with imports.
'''

__all__ = ('accelerometer', 'audio', 'battery', 'camera', 'compass', 'email',
           'filechooser', 'gps', 'gyroscope', 'irblaster', 'orientation',
           'notification', 'sms', 'tts', 'uniqueid', 'vibrator')

__version__ = '1.2.4-dev'


from plyer_lach import facades
from plyer_lach.utils import Proxy

#: Accelerometer proxy to :class:`plyer_lach.facades.Accelerometer`
accelerometer = Proxy('accelerometer', facades.Accelerometer)

#: Accelerometer proxy to :class:`plyer_lach.facades.Audio`
audio = Proxy('audio', facades.Audio)

#: Battery proxy to :class:`plyer_lach.facades.Battery`
battery = Proxy('battery', facades.Battery)

#: Compass proxy to :class:`plyer_lach.facades.Compass`
compass = Proxy('compass', facades.Compass)

#: Camera proxy to :class:`plyer_lach.facades.Camera`
camera = Proxy('camera', facades.Camera)

#: Email proxy to :class:`plyer_lach.facades.Email`
email = Proxy('email', facades.Email)

#: FileChooser proxy to :class:`plyer_lach.facades.FileChooser`
filechooser = Proxy('filechooser', facades.FileChooser)

#: GPS proxy to :class:`plyer_lach.facades.GPS`
gps = Proxy('gps', facades.GPS)

#: Gyroscope proxy to :class:`plyer_lach.facades.Gyroscope`
gyroscope = Proxy('gyroscope', facades.Gyroscope)

#: IrBlaster proxy to :class:`plyer_lach.facades.IrBlaster`
irblaster = Proxy('irblaster', facades.IrBlaster)

#: Orientation proxy to :class:`plyer_lach.facades.Orientation`
orientation = Proxy('orientation', facades.Orientation)

#: Notification proxy to :class:`plyer_lach.facades.Notification`
notification = Proxy('notification', facades.Notification)

#: Sms proxy to :class:`plyer_lach.facades.Sms`
sms = Proxy('sms', facades.Sms)

#: TTS proxy to :class:`plyer_lach.facades.TTS`
tts = Proxy('tts', facades.TTS)

#: UniqueID proxy to :class:`plyer_lach.facades.UniqueID`
uniqueid = Proxy('uniqueid', facades.UniqueID)

#: Vibrate proxy to :class:`plyer_lach.facades.Vibrator`
vibrator = Proxy('vibrator', facades.Vibrator)
