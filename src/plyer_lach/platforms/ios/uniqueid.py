from pyobjus import autoclass
from pyobjus.dylib_manager import load_framework
from plyer_lach.facades import UniqueID

load_framework('/System/Library/Frameworks/UIKit.framework')
UIDevice = autoclass('UIDevice')


class iOSUniqueID(UniqueID):

    def _get_uid(self):
        uuid = UIDevice.currentDevice().identifierForVendor.UUIDString()
        return uuid.UTF8String()


def instance():
    return iOSUniqueID()
