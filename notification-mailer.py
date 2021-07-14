import os
import logging
import cx_Oracle
import smtplib
from email.message import EmailMessage
    
def composeEmailMessage(css, emailTableHeader, columns, emailContent, emailFooter):

    html = "<html>"
    
    html += css
    
    html += "<h1>{}</h1>".format(emailTableHeader)
    
    html += "<table><tr>"
    for column in columns:
    
        columnFormattedName = column.replace('_', ' ')
        columnFormattedName = columnFormattedName.title()
        
        html += "<th>{}</th>".format(columnFormattedName)
   
    html += "</tr>"
    
    for task in range(len(emailContent)):
        
        html += "<tr>"
        
        for column in columns:
        
            html += "<td>{}</td>".format(emailContent[task][column])
        
        html += "</tr>"
        
    html += "</table>"
    
    if emailFooter:
        html += emailFooter
        
    html += "</html>"

    return html

def composeEmail(smtpEmail, receiverEmailAddress, ccEmail, emailSubject, html):

    emailToSend = EmailMessage()
    emailToSend['From'] = smtpEmail
    emailToSend['To'] = 'cshannon@ufl.edu' #receiverEmailAddress
    emailToSend['Cc'] = ccEmail
    emailToSend['Subject'] = emailSubject
    emailToSend.add_alternative(htmlContent, subtype ='html')

    return emailToSend
    
def sendEmail(smtpServer, emailToSend):

    with smtplib.SMTP(smtpServer, 25) as smtp:

        smtp.send_message(emailToSend)

def connectToDatabase(oracleServer, oraclePort, oracleSID, oracleUsername, oraclePassword):

    try:
#        dsn_tns = cx_Oracle.makedsn(oracleServer, oraclePort, oracleSID)
    
        connection = cx_Oracle.connect(user=oracleUsername, password=oraclePassword, dsn="prod", encoding="UTF-8")
            
        return connection
            
    except cx_Oracle.DatabaseError as e:
        print("There was a problem connecting to the Oracle database", e)


def getTableColumns(query, connection):

    try:
        cursor = connection.cursor()
      
        cursor.execute(query)
        
        queryDescription = cursor.description
        
        columns = []
        
        for column in range(len(queryDescription)):
            
            columns.append(queryDescription[column][0])
            
            print(queryDescription[column][1])
        
        return columns
        
    except cx_Oracle.DatabaseError as e:
        print("There was a problem getting the columns for the query", e)
    
    finally:
        if cursor:
            cursor.close()


def getTableContents(query, connection, columns, userProviedEmailAddress):
        
    emailAddresses = set()
    emailContent = {}
        
    try:
        cursor = connection.cursor()
        
        cursor.execute(query)
        
        dataLeftToProcess = True
        
        while dataLeftToProcess:
        
            row = cursor.fetchone()
            
            if row is None:
            
                dataLeftToProcess = False
                        
            if row is not None:
            
                # Create a dictionary where the columns are the keys and the query results are the values.
                queryRow = (dict(zip(columns, row)))
                
                if userProviedEmailAddress:
                    
                    emailContent[userProviedEmailAddress] = [queryRow]
                    emailAddresses.add(userProviedEmailAddress)
            
                elif queryRow['STAFF_EMAIL'] is not None:
                
                    taskAssignedEmails = set(queryRow['STAFF_EMAIL'].split(';'))
            
                    for email in taskAssignedEmails:
                    
                        # If the email is already in the dictionary then append the task to the existing tasklist
                        if email in emailContent.keys():
                    
                            emailContent[email].append(queryRow)
    
                        # If the email is not in the dictionary then add the email to the dictionary with the task as its value
                        else:
                        
                            emailContent[email] = [queryRow]
                        
                        emailAddresses.add(email)
                        
        return emailAddresses, emailContent
  
    except cx_Oracle.DatabaseError as e:
        print("There was a problem getting data from the query", e)

    finally:
        if cursor:
            cursor.close()


def main():
    
    css = os.getenv('TABLE_CSS')

    query = os.getenv('QUERY')
    userRequestedColumns = os.getenv('TABLE_COLUMNS').split(',')
    
    oracleServer = os.getenv('ORACLE_SERVER')
    oraclePort = os.getenv('ORACLE_PORT')
    oracleSID = os.getenv('ORACLE_SID')
    oracleUsername = os.getenv('ORACLE_USERNAME')
    oraclePassword = os.getenv('ORACLE_PASSWORD')
    oracleCurrentSchema = os.getenv('ORACLE_CURRENT_SCHEMA')
    
    userProviedEmailAddress = os.getenv('EMAIL_RECIPIENT')
    smtpEmail = os.getenv('EMAIL_FROM')
    smtpServer = os.getenv('EMAIL_SMTP_SERVER')
    ccEmail = os.getenv('EMAIL_CC')
    emailSubject = os.getenv('EMAIL_SUBJECT')
    emailTableHeader = os.getenv('EMAIL_TABLE_HEADER')
    emailFooter = os.getenv('EMAIL_FOOTER')
    
    connection = connectToDatabase(oracleServer, oraclePort, oracleSID, oracleUsername, oraclePassword)

    if connection:
        connection.current_schema = oracleCurrentSchema
        
        columns = getTableColumns(query, connection)
        emailAddresses, emailContent = getTableContents(query, connection, columns, userProviedEmailAddress)
        connection.close()
        
        for receiverEmailAddress in emailAddresses:
            
            emailHTML = composeEmailMessage(css, emailTableHeader, userRequestedColumns, emailContent[receiverEmailAddress], emailFooter)

#            emailToSend = composeEmail(smtpEmail, receiverEmailAddress, ccEmail, emailSubject, emailHTML)

#            sendEmail(smtpServer, emailToSend)
            
            print(emailHTML)
            print('\n')
            
if __name__ == "__main__":
    main()
