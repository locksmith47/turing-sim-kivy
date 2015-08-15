import subprocess
from plyer_lach.facades import TTS
from plyer_lach.utils import whereis_exe


class EspeakTextToSpeech(TTS):
    ''' Speaks using the espeak program
    '''
    def _speak(self, **kwargs):
        subprocess.call(["espeak", kwargs.get('message')])


def instance():
    if whereis_exe('espeak.exe'):
        return EspeakTextToSpeech()
    return TTS()
