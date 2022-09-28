import smtplib
import ssl
import certifi
import sys
import re
import argparse
import pathlib
from os import environ,path
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
import logging
import datetime as dt

"""
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 587
DEFAULT_TIMEOUT = 5
DEFAULT_DEBUG = False
DEFAULT_ENCRYPTION = "starttls"

ENCRYPTION_OPTIONS = ["tls", "starttls", "none"]
"""
ATTR_DATA = "data"

ATTR_IMAGES = "images"

# Text to notify user of
ATTR_MESSAGE = "message"

# Target of the notification (user, device, etc)
ATTR_TARGET = "target"

# Title of notification
ATTR_TITLE = "title"
ATTR_TITLE_DEFAULT = "SMTP AGENT"

_LOGGER = logging.getLogger(__name__)

def client_context() -> ssl.SSLContext:
    """Return an SSL context for making requests."""

    cafile = environ.get("REQUESTS_CA_BUNDLE", certifi.where())

    context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=cafile)
    return context


class MailNotificationService(object):
    """Implement the notification service for E-mail messages."""

    def __init__(
        self,
        server,
        port,
        sender,
        encryption,
        username,
        password,
        recipients,
        sender_name,
        debug,
        verify_ssl,
    ):
        """Initialize the SMTP service."""
        self._server = server
        self._port = port
        self._sender = sender
        self.encryption = encryption
        self.username = username
        self.password = password
        self.recipients = recipients
        self._sender_name = sender_name
        self.debug = debug
        self._verify_ssl = verify_ssl
        self.tries = 2

    def connect(self):
        """Connect/authenticate to SMTP Server."""
        ssl_context = client_context() if self._verify_ssl else None
        if self.encryption == "tls":
            mail = smtplib.SMTP_SSL(
                self._server,
                self._port,
                context=ssl_context,
            )
        else:
            mail = smtplib.SMTP(self._server, self._port)
        mail.set_debuglevel(self.debug)
        mail.ehlo_or_helo_if_needed()
        if self.encryption == "starttls":
            mail.starttls(context=ssl_context)
            mail.ehlo()
        if self.username and self.password:
            mail.login(self.username, self.password)
        return mail

    def connection_is_valid(self):
        """Check for valid config, verify connectivity."""
        server = None
        try:
            server = self.connect()
        except (smtplib.socket.gaierror, ConnectionRefusedError):
            _LOGGER.exception(
                "SMTP server not found or refused connection (%s:%s). "
                "Please check the IP address, hostname, and availability of your SMTP server",
                self._server,
                self._port,
            )

        except smtplib.SMTPAuthenticationError:
            _LOGGER.exception(
                "Login not possible. "
                "Please check your setting and/or your credentials"
            )
            return False

        finally:
            if server:
                server.quit()

        return True

    def send_message(self, message="",recipients=[] , **kwargs):
        """
        Build and send a message to a user.

        Will send plain text normally, or will build a multipart HTML message
        with inline image attachments if images config is defined, or will
        build a multipart HTML if html config is defined.
        """
        subject = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)

        if data := kwargs.get(ATTR_DATA):
            msg = _build_multipart_msg(message, images=data.get(ATTR_IMAGES, []))
        else:
            msg = _build_text_msg(message)

        msg["Subject"] = subject

        if not (recipients := kwargs.get(ATTR_TARGET)):
            recipients = self.recipients
        msg["To"] = recipients if isinstance(recipients, str) else ",".join(recipients)
        if self._sender_name:
            msg["From"] = f"{self._sender_name} <{self._sender}>"
        else:
            msg["From"] = self._sender
        msg["X-Mailer"] = "SMTP AGENT"
        msg["Date"] = email.utils.format_datetime(dt.datetime.now(dt.timezone.utc))
        msg["Message-Id"] = email.utils.make_msgid()

        return self._send_email(msg, recipients)

    def _send_email(self, msg, recipients):
        """Send the message."""
        mail = self.connect()
        for _ in range(self.tries):
            try:
                mail.sendmail(self._sender, recipients, msg.as_string())
                break
            except smtplib.SMTPServerDisconnected:
                _LOGGER.warning(
                    "SMTPServerDisconnected sending mail: retrying connection"
                )
                mail.quit()
                mail = self.connect()
            except smtplib.SMTPException:
                _LOGGER.warning("SMTPException sending mail: retrying connection")
                mail.quit()
                mail = self.connect()
        mail.quit()


def _build_text_msg(message):
    """Build plaintext email."""
    _LOGGER.debug("Building plain text email")
    return MIMEText(message)


def _attach_file(atch_name, content_id):
    """Create a message attachment."""
    try:
        with open(atch_name, "rb") as attachment_file:
            file_bytes = attachment_file.read()
    except FileNotFoundError:
        _LOGGER.warning("Attachment %s not found. Skipping", atch_name)
        return None

    try:
        attachment = MIMEImage(file_bytes)
    except TypeError:
        _LOGGER.warning(
            "Attachment %s has an unknown MIME type. Falling back to file",
            atch_name,
        )
        #file_name = re.search('^/(.+\/)*(.+.+)$', atch_name).group(2)
        file_name = path.basename(atch_name)
        attachment = MIMEApplication(file_bytes, Name=file_name)
        attachment["Content-Disposition"] = f'attachment; filename="{file_name}"'

    attachment.add_header("Content-ID", f"<{content_id}>")
    return attachment


def _build_multipart_msg(message, images):
    """Build Multipart message with in-line images."""
    _LOGGER.debug("Building multipart email with embedded attachment(s)")
    msg = MIMEMultipart("related")
    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    body_txt = MIMEText(message)
    msg_alt.attach(body_txt)
    body_text = [f"<p>{message}</p><br>"]

    for atch_num, atch_name in enumerate(images):
        cid = f"image{atch_num}"
        body_text.append(f'<img src="cid:{cid}"><br>')
        attachment = _attach_file(atch_name, cid)
        if attachment:
            msg.attach(attachment)
    return msg


def get_main_app(argv=[]):
    mail = MailNotificationService(
    "smtp.gmail.com",
    587,
    "$gmail",
    "starttls",
    "$gmail.com",
    "$key", #yfrslystmffwnkhp
    "gmail",
    "name",
    0,
    True,
    )
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--message", type=str)
    arg_parser.add_argument("--target", type=str, nargs="+")
    arg_parser.add_argument("--data", type=pathlib.Path, default=None, nargs="*")

    args = arg_parser.parse_args(argv[1:])

    if args.message is None:
        print("not find message value")
        sys.exit(0)

        
    if args.data is None:
        print("No specify data, use text mode")
        if mail.connection_is_valid():
            mail.send_message(message=args.message, target=args.target)
    else:
        images = {"images":[]}
        for item_path in args.data:
            if not path.exists(item_path):
                raise ValueError(f"not find file path {item_path}")
            else:
                images["images"].append(str(item_path.resolve()))
        
        mail.send_message(message=args.message, target=args.target,data=images)

    # if mail.connection_is_valid():
    #     images = {"images":["a.py","c.py"]}
    #     mail.send_message(message="test my smtp agent", target=["hammer6395@gmail.com","danny788995@gmail.com"],data=images)

if __name__ == "__main__":
    get_main_app(sys.argv)
