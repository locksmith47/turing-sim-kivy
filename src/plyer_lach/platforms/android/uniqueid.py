from jnius import autoclass
from plyer_lach.platforms.android import activity
from plyer_lach.facades import UniqueID

Secure = autoclass('android.provider.Settings$Secure')


class AndroidUniqueID(UniqueID):

    def _get_uid(self):
        return Secure.getString(activity.getContentResolver(),
                                Secure.ANDROID_ID)


def instance():
    return AndroidUniqueID()
