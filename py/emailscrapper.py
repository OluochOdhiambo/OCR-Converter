import imaplib, email
import os
import re

email_indices_path = "C:/Users/TASH-PC/Desktop/bioOCR/dependencies/email_indices.txt"

imap_url = "imap.gmail.com"
pdf_attachment_dir = "C:/Users/TASH-PC/Desktop/bioOCR/pdf"

## authentication 
def auth(user_email, password, imap_url):
    con = imaplib.IMAP4_SSL(imap_url, 993)
    con.login(user_email, password)
    return con

## get mail body
def get_body(msg):
    if msg.is_multipart():
        return get_body(msg.get_payload(0))
    else:
        return msg.get_payload(None, True)

# get key value pair
# def search(key, value, con):
#     result, data = con.search(None, key, f"{value}")
#     return data

def get_emails(result_bytes, con, email_attachment_indices):
    msgs = []
    for num in result_bytes[0].split():
        if num.decode() in email_attachment_indices:
            continue
        else:
            typ, data = con.fetch(num, "(RFC822)")
            msgs.append(data)
            email_attachment_indices.append(num.decode())

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

### LAUNCH SCRAPPER
user_email = input("Enter bot-linked email: ...")
password = input("Enter email password: ...")

con = auth(user_email, password, imap_url)
con.select("INBOX")

## save index for downloaded email attachements
email_attachment_indices = []

with open((email_indices_path), "r", encoding="utf-8", errors="ignore") as f:
    txt = f.read()
    for index in txt.split(", "):
        if len(index) != 0:
            email_attachment_indices.append(index)

result, data = con.search(None, '(UNSEEN)') and con.search(None, "FROM", "bioworkflow@biofoods.co.ke")
msgs = get_emails(data, con, email_attachment_indices)

with open((email_indices_path), "w", encoding="utf-8", errors="ignore") as f:
    for i in range(len(email_attachment_indices)):
        if len(email_attachment_indices[i]) != 0:
            if i < len(email_attachment_indices) - 1:
                f.write(email_attachment_indices[i])
                f.write(", ")
            else:
                f.write(email_attachment_indices[i])

print("Downloading email attachments. PLEASE WAIT...")
count = 0
for msg in msgs:
    raw = email.message_from_bytes(msg[0][1])
    msg = get_body(raw)
    get_attachments(raw)
    count = count + 1

print(f"{count} files downloaded.")


# result, data = con.fetch(b"13362", "(RFC822)")
# raw = email.message_from_bytes(data[0][1])
# print(get_body(raw))
# get_attachments(raw)




