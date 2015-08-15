from jnius import autoclass, cast
from kivy.logger import Logger
from plyer_lach.facades import Email
from plyer_lach.platforms.android import activity

Intent = autoclass('android.content.Intent')
AndroidString = autoclass('java.lang.String')
URI = autoclass('android.net.Uri')

class AndroidEmail(Email):
    def _send(self, **kwargs):
        intent = Intent(Intent.ACTION_SEND)
        intent.setType('*/*')

        recipient = kwargs.get('recipient')
        subject = kwargs.get('subject')
        text = kwargs.get('text')
        create_chooser = kwargs.get('create_chooser')
        file_path = kwargs.get('file_path')
        
        if recipient:
            intent.putExtra(Intent.EXTRA_EMAIL, [recipient])
        if subject:
            android_subject = cast('java.lang.CharSequence',
                                   AndroidString(subject))
            intent.putExtra(Intent.EXTRA_SUBJECT, android_subject)
        if file_path:
            file_uri = URI.parse('file://' + file_path)
            Logger.info(str(file_uri.toString()))
            intent.putExtra(Intent.EXTRA_STREAM, cast('android.os.Parcelable', file_uri))
            Logger.info('Added file')
        if create_chooser:
            chooser_title = cast('java.lang.CharSequence',
                                 AndroidString('Send message with:'))
            activity.startActivity(Intent.createChooser(intent,
                                                        chooser_title))
        else:
            activity.startActivity(intent)


def instance():
    return AndroidEmail()
