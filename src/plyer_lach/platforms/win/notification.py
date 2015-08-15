from threading import Thread as thread

from plyer_lach.facades import Notification
from plyer_lach.platforms.win.libs.balloontip import balloon_tip


class WindowsNotification(Notification):
    def _notify(self, **kwargs):
        thread(target=balloon_tip, kwargs=kwargs).start()


def instance():
    return WindowsNotification()
