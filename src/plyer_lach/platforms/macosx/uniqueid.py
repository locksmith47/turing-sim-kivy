from subprocess import Popen, PIPE
from plyer_lach.facades import UniqueID
from plyer_lach.utils import whereis_exe

from os import environ


class OSXUniqueID(UniqueID):
    def _get_uid(self):
        old_lang = environ.get('LANG')
        environ['LANG'] = 'C'

        ioreg_process = Popen(["ioreg", "-l"], stdout=PIPE)
        grep_process = Popen(["grep", "IOPlatformSerialNumber"],
            stdin=ioreg_process.stdout, stdout=PIPE)
        ioreg_process.stdout.close()
        output = grep_process.communicate()[0]

        environ['LANG'] = old_lang

        if output:
            return output.split()[3][1:-1]
        else:
            return None


def instance():
    import sys
    if whereis_exe('ioreg'):
        return OSXUniqueID()
    sys.stderr.write("ioreg not found.")
    return UniqueID()
