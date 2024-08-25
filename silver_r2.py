import smtplib
import sys
import requests
import os
import time

# SRC: https://medium.com/testingonprod/how-to-send-text-messages-with-python-for-free-a7c92816e1a4
# Thank you David Mentgen

CARRIERS = {
    "att": "@mms.att.net",
    "tmobile": "@tmomail.net",
    "verizon": "@vtext.com",
    "sprint": "@messaging.sprintpcs.com",
    "gmail": "@gmail.com"
}

# Input personal email and password
# Must use app-specific password to bypass 2-factor auth
EMAIL = "example@email.com"
PASSWORD = "password"
 
def send_message(recipient, message):
    auth = (EMAIL, PASSWORD)
 
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(auth[0], auth[1])
 
    server.sendmail(auth[0], recipient, message)
 
def get_data(source):
    # Read from reference data, or download reference data if file does not exist
    try:
        ref_fd = open("refdata.csv", "r")

    except:
        r = requests.get(source)
        open("refdata.csv", "wb").write(r.content)
        ref_fd = open("refdata.csv", "r")

    refdata = ref_fd.readlines()
    ref_fd.close()

    # Downloading comparison data as file comp.csv
    r = requests.get(source)
    open("comp.csv", "wb").write(r.content)
    comp_fd = open("comp.csv", "r")
    compdata = comp_fd.readlines()
    comp_fd.close()

    # Delete temp comparison file
    os.remove("comp.csv")
    
    # Compare new data to old data
    if refdata == compdata:
        return
    
    # Replace old data with new data if different
    else:
        fd = open("refdata.csv", "w")
        fd.write(''.join(compdata)) 
        fd.close()
        margin, compMargin = get_margins(refdata, compdata)
        return build_brief(margin, compMargin)

def get_margins(refData, compData):
    
    # Calculate margins from existing data
    margin = dict()
    for line in refData[1:]:
        row = line.split(",")
        margin[row[0]] = float(row[1]) - float(row[2])

    # calculate margins from new pulled data
    compMargin = dict()
    for line in compData[1:]:
        row = line.split(",")
        compMargin[row[0]] = float(row[1]) - float(row[2])

    return margin, compMargin

def build_brief(margin, compMargin):
    
    # Uses return values from get_margins()
    brief = ""
    
    # Harris/Trump +X.xx or Even +0.00
    for state in margin:
        if margin[state] > 0:
            leader = "Harris"
            lead = margin[state]
        elif margin[state] < 0:
            leader = "Trump"
            lead = -1*margin[state]
        else:
            leader = "Even"
            lead = margin[state]

        # Printing new margins
        if compMargin[state] > 0:
            compLeader = "Harris"
            compLead = compMargin[state]
        elif compMargin[state] < 0:
            compLeader = "Trump"
            compLead = -1*compMargin[state]
        else:
            compLeader = "Even"
            compLead = compMargin[state]
        brief += "{:15s} {:6s} +{:.2f} -> {:6s} +{:.2f}\n\n".format(state + ":", leader, lead, compLeader, compLead)
    return brief

def mail_list(message):
    mailList = open("maillist.txt", "r").readlines()
    for address in mailList:
        recipient = address.strip()
        send_message(recipient, message)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: python3 {sys.argv[0]} <PHONE_NUMBER> <CARRIER>")
        sys.exit(0)
 
    phone_number = sys.argv[1]
    carrier = sys.argv[2]
    recipient = phone_number + CARRIERS[carrier]

    count = 0
    pause = 300
    while(True):
        time.sleep(pause)
        print("Checking Data...")
        brief = get_data("https://static.dwcdn.net/data/OYvXP.csv")
        if brief != None:
            print("Update sent!")
            content = brief
            message = 'Subject: {}\n\n{}'.format("Update from Nate!", content)
            mail_list(message)
        elif count >= 143:
            print("Still working")
            content = "Still checking though!"
            message = 'Subject: {}\n\n{}'.format("No updates :(", content)
            send_message(recipient, message)
            count = 0
        else:
            count += 1
            print("Nothing new in the last {} minute(s)".format(count*pause//60))
