'''
iOS Compass
---------------------
'''

from plyer_lach.facades import Compass
from pyobjus import autoclass


class IosCompass(Compass):

    def __init__(self):
        super(IosCompass, self).__init__()
        self.bridge = autoclass('bridge').alloc().init()
        self.bridge.motionManager.setMagnetometerUpdateInterval_(0.1)

    def _enable(self):
        self.bridge.startMagnetometer()

    def _disable(self):
        self.bridge.stopMagnetometer()

    def _get_orientation(self):
        return (
            self.bridge.mg_x,
            self.bridge.mg_y,
            self.bridge.mg_z)


def instance():
    return IosCompass()
