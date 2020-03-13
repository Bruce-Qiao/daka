from PIL import Image, ImageDraw, ImageFont
import datetime, sys
import httplib2
import os
import oauth2client
from oauth2client import client, tools, file
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery
import mimetypes
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'daka'

def watermark_text(input_iamge_path,
                   output_image_path,
                   text,
                   text_font,
                   text_color,
                   pos):
    """
    Draw text on a photo.
    """

    photo = Image.open(input_iamge_path)

    # make the image editable
    drawing = ImageDraw.Draw(photo)

    drawing.text(pos, text, fill=text_color, font=text_font)
    photo.show()
    photo.save(output_image_path)

def generate_image(day):
    """
    Use a special day draw text on a photo.
    """

    black = (3, 8, 12)
    white = (255, 255, 255)

    watermark_text("workout_background.jpeg",
                   "workout.jpeg",
                   text=f"   {day.month}月{day.day}号\n\n9组锻炼打卡",
                   text_font=ImageFont.truetype("ZCOOLKuaiLe-Regular.ttf", 200),
                   text_color=black,
                   pos=(100, 300))
    watermark_text("study_background.jpeg", 
                   "study.jpeg",
                   text=f"   {day.month}月{day.day}号\n\n9组学习打卡",
                   text_font=ImageFont.truetype("Songti.ttc", 200),
                   text_color=white,
                   pos=(100, 300))    

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-email-send.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def SendMessage(sender, to, subject, msgHtml, msgPlain, attachmentFile=None):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    if attachmentFile:
        message1 = createMessageWithAttachment(sender, to, subject, msgHtml, msgPlain, attachmentFile)
    else: 
        message1 = CreateMessageHtml(sender, to, subject, msgHtml, msgPlain)
    result = SendMessageInternal(service, "me", message1)
    return result

def SendMessageInternal(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)
        return "Error"
    return "OK"

def CreateMessageHtml(sender, to, subject, msgHtml, msgPlain):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(msgPlain, 'plain'))
    msg.attach(MIMEText(msgHtml, 'html'))
    return {'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()}

def createMessageWithAttachment(
    sender, to, subject, msgHtml, msgPlain, attachmentFile):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      msgHtml: Html message to be sent
      msgPlain: Alternative plain text message for older email clients          
      attachmentFile: The path to the file to be attached.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEMultipart('mixed')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    messageA = MIMEMultipart('alternative')
    messageR = MIMEMultipart('related')

    messageR.attach(MIMEText(msgHtml, 'html'))
    messageA.attach(MIMEText(msgPlain, 'plain'))
    messageA.attach(messageR)

    message.attach(messageA)

    print("create_message_with_attachment: file: %s" % attachmentFile)
    content_type, encoding = mimetypes.guess_type(attachmentFile)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(attachmentFile, 'rb')
        msg = MIMEText(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(attachmentFile, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(attachmentFile, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(attachmentFile, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()
    filename = os.path.basename(attachmentFile)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}


def main():

    if len(sys.argv) == 2 and sys.argv[1] == "today":
        day = datetime.date.today()
    else:
        day = datetime.date.today() + datetime.timedelta(days=1)

    generate_image(day)

    to = "bruceq619@foxmail.com"
    sender = "bruceq619@gmail.com"
    subject_study = f"{day.month}月{day.day}日学习打卡照片"
    subject_workout = f"{day.month}月{day.day}日健康打卡照片"
    msgHtml = "Hi<br/>Have a good day!"
    msgPlain = "Hi\nHave fun!"
    # SendMessage(sender, to, subject, msgHtml, msgPlain)
    # Send message with attachment: 
    SendMessage(sender, to, subject_study, msgHtml, msgPlain, 'study.jpeg')
    SendMessage(sender, to, subject_workout, msgHtml, msgPlain, 'workout.jpeg')

if __name__ == '__main__':
    main()