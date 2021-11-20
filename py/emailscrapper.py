import imaplib, email
import os
import re

username = 'oluochodhiambo11@gmail.com'
password = '#################'
imap_url = "imap.gmail.com"
pdf_attachment_dir = "C:/Users/TASH-PC/Desktop/bioOCR/pdf"

## authentication 
def auth(username, password, imap_url):
    con = imaplib.IMAP4_SSL(imap_url, 993)
    con.login(username, password)
    return con

## get mail body
def get_body(msg):
    if msg.is_multipart():
        return get_body(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)

# get key value pair
def search(key, value, con):
    result, data = con.search(None, key, f"{value}")
    return data

def get_emails(result_bytes, con):
    msgs = []
    for num in result_bytes[0].split():
        typ, data = con.fetch(num, "(RFC822)")
        msgs.append(data)
    return msgs

def get_attachments(msg):
    for part in msg.walk():
        if part.get_content_maintype()== "multipart":
            continue
        if part.get("Content-Disposition") is None:
            continue
        fileName = part.get_filename()

        if bool(fileName):
            filePath = os.path.join(pdf_attachment_dir, fileName)
            with open(filePath, "wb") as f:
                f.write(part.get_payload(decode=True))

con = auth(username, password, imap_url)
con.select("INBOX")

# msgs = get_emails(search("FROM", "bioworkflow@biofoods.co.ke", con), con)


result, data = con.search(None, '(UNSEEN)') and con.search(None, "FROM", "bioworkflow@biofoods.co.ke")
msgs = get_emails(data, con)


for msg in msgs:
    raw = email.message_from_bytes(msg[0][1])
    msg = get_body(raw)
    get_attachments(raw)
    print("######################################################################################")

# result, data = con.fetch(b"13362", "(RFC822)")
# raw = email.message_from_bytes(data[0][1])
# print(get_body(raw))
# get_attachments(raw)




