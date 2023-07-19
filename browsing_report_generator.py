import sqlite3
import os
import datetime
import pickle
import smtplib
from tabulate import tabulate
import random
import string
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate
from reportlab.lib.units import inch
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from urllib.parse import urlparse
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
"""
from bs4 import BeautifulSoup
import requests
import re
"""
cv = joblib.load('Webclassifier.pkl')
model = joblib.load('WebVectorizier.pkl')
"""
#loading the count vectorizer
with open('WebVectorizier.pkl', 'rb') as f:
    cv = pickle.load(f)
#loading the machine learning model
with open('Webclassifier.pkl', 'rb') as f:
    model = pickle.load(f)
    
#create bag of words using count vectorizer and predict the category using model
#Here we take the website url as input.
#We extract the domain part from url as parsed url
#Then we send a request to the url and get a HTML wepage in response
#Beautiful Soup(bs4) is a Python library for pulling data out of the received HTML wepage
#We extract meta-data from wepage and search for description attribute
#If description attribute is not in meta-data response then we split the url itself into keywords and send the text to model for prediction
def predictWebsiteCatgerory( website_input):
  try:
    print("Input : "+website_input)
    website_split = website_input.split('/', 3)
    website_input = '/'.join(website_split[:3])
    print("Parsed URL : "+website_input)
    headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    }
    r = requests.get(website_input, headers=headers)
    soup = BeautifulSoup(r.content, "html")
    meta = soup.find_all('meta')
    # print(r.text)
    for tag in meta:
      if 'name' in tag.attrs.keys() and tag.attrs['name'].strip().lower() == 'description':
          print("Wesbite Description : "+tag.attrs['content'])
          data = cv.transform([tag.attrs['content']]).toarray()
          output = model.predict(data)
          print(output)
          return output
    
    content = ''
    for link in soup.findAll("a", href=True):
      content = content + link.text

    # print("Checking alternate content from links: "+content)
    if content:
          print("Could not fetch meta data. Checking alternate content from anchor tags....")
          data = cv.transform([content]).toarray()
          output = model.predict(data)
          print(output)
          return output
      
    website_input = website_input.split('//')[1]
    website_split = re.split(r"[^a-zA-Z\s]", website_input)
    website_text = ' '.join(website_split)
    data = cv.transform([website_text]).toarray()
    output = model.predict(data)
    return output
  except:
    return "Cannot Access Website"
  
#create a 30 day window starting 30 days ago
start_time = datetime.datetime.now() - datetime.timedelta(days=30)
end_time = datetime.datetime.now() 
start_time_1601 = datetime.datetime(1601, 1, 1)

#browser history uses different time format starting year 1601
start_1601 = (start_time - start_time_1601).total_seconds() * 1000000
end_1601 = (end_time - start_time_1601).total_seconds() * 1000000

print(end_1601,start_1601)
# Path to the browser history database
chrome_path = os.path.expanduser('~') + r"\AppData\Local\Google\Chrome\User Data\Profile 4\History"
firefox_path = os.path.expanduser('~') + r"\AppData\Roaming\Mozilla\Firefox\Profiles\*.default\places.sqlite"
edge_path = os.path.expanduser('~') + r"\AppData\Local\Microsoft\Edge\User Data\Default\History"

# Connect to the database
conn = sqlite3.connect(chrome_path)
#conn = sqlite3.connect(firefox_path)
# conn = sqlite3.connect(edge_path)

# Create a cursor object
#to fetch title, url,visitcount,timestamp
cur = conn.cursor()

# Execute a SQL query to fetch the browser history
query = "SELECT url, visit_count, last_visit_time FROM urls WHERE last_visit_time BETWEEN ? AND ?"
cur.execute(query, (int(start_1601), int(end_1601)))

# Loop through the results and add them to the array
array=[]
for row in cur:
    array.append(row)
    
#sort the result by visitcount
array.sort(key = lambda x: x[1],reverse = True)
#fetch top 20 results
array= array[:20]

#predict category for each result
#also convert timestamp into date
results = [['URL', 'VisitCount', 'Timestamp', 'Category']]
for row in array:
    listRecord = list(row)
    output=predictWebsiteCatgerory(listRecord[0])
    listRecord.append(output[0])
    parsed_url = urlparse(listRecord[0])
    listRecord[0] = parsed_url.netloc
    listRecord[2]=datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=row[2])
    results.append(listRecord)
    ## print(output)
# Close the cursor and connection
print(results)
cur.close()
conn.close()

#beautify results
text=tabulate(results, headers=['URL', 'VisitCount', 'Timestamp', 'Category'])
print(tabulate(results, headers=['URL', 'VisitCount', 'Timestamp', 'Category']))
pdf_file = 'output.pdf'
pagesize = (20 * inch, 10 * inch)
doc = SimpleDocTemplate(pdf_file, pagesize=pagesize)
elements = []

# create table and table style
table = Table(results,colWidths=[300,100,200,200])
style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 14),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 12),
    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
])
table.setStyle(style)

# add table to PDF file
elements.append(table)

# build PDF file
doc.build(elements)


# set up email parameters
sender_email = '123@gmail.com'
sender_password = 'rghfjzlifmkdfzdj'
receiver_email = '234@gmail.com'
subject = "Browsing History Report ID: "+''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
body = 'Please find attached the PDF file.'

# create message object instance
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = subject

# attach body to message
msg.attach(MIMEText(body, 'plain'))

# attach PDF file to message
with open(pdf_file, 'rb') as f:
    attachment = MIMEApplication(f.read(), _subtype='pdf')
    attachment.add_header('Content-Disposition', 'attachment', filename=pdf_file)
    msg.attach(attachment)

# send email
with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
    smtp.starttls()
    smtp.login(sender_email, sender_password)
    smtp.send_message(msg)

# delete PDF file
os.remove(pdf_file)

print('Email sent successfully.')
