# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Zdroj: http://stackoverflow.com/questions/3362600/how-to-send-email-attachments-with-python
#
# Description: Modul pro posilani zprav na exchange
# Upravil: f:D
# Volani: (pomoci r'.\py_tools\__init__.py')
#    import py_tools.SendMail
# ---------------------------------------------------------------------------

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email.utils import formatdate
from email import encoders

def send_mail( send_from, send_to, subject, text, files=[], server='ex1.ipr.praha.eu', port=None, username=None, password=None, isTls=None ):
   msg = MIMEMultipart()
   msg['From'] = send_from
   msg['To'] = COMMASPACE.join(send_to)
   msg['Date'] = formatdate(localtime = True)
   msg['Subject'] = subject

   msg.attach( MIMEText(text) )

   for f in files:
      part = MIMEBase('application', "octet-stream")
      part.set_payload( open(f,"rb").read() )
      encoders.encode_base64(part)
      part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(f)))
      msg.attach(part)

   smtp = smtplib.SMTP(server, port)
   if isTls: smtp.starttls()
   if username != None: smtp.login(username,password)
   smtp.sendmail(send_from, send_to, msg.as_string())
   smtp.quit()

if __name__ == "__main__":
   to_ = ['drda@ipr.praha.eu']         # list adres ','
   from_ = 'job_update_ruian@ipr.praha.eu'
   subject = "skript-win3: test"
   body = "Telo testovaci zpravy."
   file_ = [r'D:\cesta\k\souboru.txt'] # list souboru ','

   try:
      send_mail( from_, to_, subject, body )
      print '\nINFO: Byl poslan e-mail.'

   except Exception as e:
      # If an error occurred, print line number and error message
      import traceback
      import sys
      import datetime
      print datetime.datetime.now().strftime("%H:%M:%S")
      tb = sys.exc_info()[2]
      tbinfo = traceback.format_tb(tb)[0]
      pymsgs = '\nPYTHON ERRORS:\n Error Info:\n An error occured on line %i' % tb.tb_lineno + '\n Traceback info:\n' + tbinfo
      print str(e)
      print pymsgs
