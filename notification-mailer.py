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

def composeEmail(smtpEmail, receiverEmailAddress, ccEmail, emailSubject, htmlContent):

    emailToSend = EmailMessage()
    emailToSend['From'] = smtpEmail
    emailToSend['To'] = receiverEmailAddress

    if ccEmail:
        emailToSend['Cc'] = ccEmail

    emailToSend['Subject'] = emailSubject
    emailToSend.add_alternative(htmlContent, subtype ='html')

    return emailToSend

def sendEmail(smtpServer, emailToSend):

    with smtplib.SMTP(smtpServer, 25) as smtp:

        smtp.send_message(emailToSend)

def connectToDatabase(oracleServer, oraclePort, oracleSID, oracleUsername, oraclePassword, oracleTnsName):

    try:
        connection = cx_Oracle.connect(user=oracleUsername, password=oraclePassword, dsn=oracleTnsName, encoding="UTF-8")
        logging.info("Successfully connected to the Oracle database")

        return connection

    except cx_Oracle.DatabaseError as e:
        logging.info("There was a problem connecting to the Oracle database", e)


def getTableColumns(query, connection):

    try:
        logging.info("Gathering table columns from the provided query")

        cursor = connection.cursor()

        logging.info("Successfully opened the get table columns cursor")

        cursor.execute(query)

        queryDescription = cursor.description

        columns = []

        for column in range(len(queryDescription)):

            columns.append(queryDescription[column][0])

        return columns

    except cx_Oracle.DatabaseError as e:
        logging.info("There was a problem getting the table's columns from the provided query", e)

    finally:
        if cursor:
            logging.info("Closing the get table columns cursor")
            cursor.close()

def getTableContents(query, connection, columns, userProvidedEmailAddress, sqlEmailRow):

    emailAddresses = set()
    emailContent = {}

    try:
        logging.info("Gathering the table's content from the provided query")

        cursor = connection.cursor()

        logging.info("Successfully opened the get table contents cursor")

        cursor.execute(query)

        dataLeftToProcess = True

        while dataLeftToProcess:

            row = cursor.fetchone()

            if row is None:

                dataLeftToProcess = False

            if row is not None:

                # Create a dictionary where the columns are the keys and the query results are the values.
                queryRow = (dict(zip(columns, row)))

                if userProvidedEmailAddress:
                    # If the email is already in the dictionary then append the task to the existing tasklist
                    if userProvidedEmailAddress in emailContent.keys():
                        emailContent[userProvidedEmailAddress].append(queryRow)

                    # If the email is not in the dictionary then add the email to the dictionary with the task as its value
                    else:
                        emailContent[userProvidedEmailAddress] = [queryRow]
                        emailAddresses.add(userProvidedEmailAddress)

                elif queryRow[sqlEmailRow] is not None:

                    taskAssignedEmails = set(queryRow[sqlEmailRow].split(';'))

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
        logging.info("There was a problem getting the table's content from the provided query", e)

    finally:
        if cursor:
            logging.info("Closing the get table contents cursor")
            cursor.close()


def main():

    logging.basicConfig(filename=os.getenv('LOG_FILE'), format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%m-%d-%Y %H:%M:%S')

    css = os.getenv('TABLE_CSS')

    query = os.getenv('QUERY')
    userRequestedColumns = os.getenv('TABLE_COLUMNS').split(',')

    oracleServer = os.getenv('ORACLE_SERVER')
    oraclePort = os.getenv('ORACLE_PORT')
    oracleSID = os.getenv('ORACLE_SID')
    oracleUsername = os.getenv('ORACLE_USERNAME')
    oraclePassword = os.getenv('ORACLE_PASSWORD')
    oracleCurrentSchema = os.getenv('ORACLE_CURRENT_SCHEMA')
    oracleTnsName = os.getenv('ORACLE_TNS_NAME')

    userProvidedEmailAddress = os.getenv('EMAIL_RECIPIENT')
    sqlEmailRow = os.getenv('SQL_EMAIL_ROW')
    smtpEmail = os.getenv('EMAIL_FROM')
    smtpServer = os.getenv('EMAIL_SMTP_SERVER')
    ccEmail = os.getenv('EMAIL_CC')
    emailSubject = os.getenv('EMAIL_SUBJECT')
    emailTableHeader = os.getenv('EMAIL_TABLE_HEADER')
    emailFooter = os.getenv('EMAIL_FOOTER')

    environment = os.getenv('ENVIRONMENT').lower()

    connection = connectToDatabase(oracleServer, oraclePort, oracleSID, oracleUsername, oraclePassword, oracleTnsName)

    if connection:

        failedEmailContent = {}
        successfulEmailCount = 0
        failedEmailCount = 0
        developmentNumberOfEmails = 0

        logging.info("Setting the current schema to {}".format(oracleCurrentSchema))
        connection.current_schema = oracleCurrentSchema

        columns = getTableColumns(query, connection)
        emailAddresses, emailContent = getTableContents(query, connection, columns, userProvidedEmailAddress, sqlEmailRow)

        logging.info("Closing the connection to the database")
        connection.close()

        for receiverEmailAddress in emailAddresses:

            numberOfItems = len(emailContent[receiverEmailAddress])

            logging.info("Composing message for {}".format(receiverEmailAddress))
            emailHTML = composeEmailMessage(css, emailTableHeader, userRequestedColumns, emailContent[receiverEmailAddress], emailFooter)

            if environment == 'production':
                emailToSend = composeEmail(smtpEmail, receiverEmailAddress, ccEmail, emailSubject, emailHTML)

                try:
                    sendEmail(smtpServer, emailToSend)
                    successfulEmailCount = successfulEmailCount + 1
                    logging.info("Sent message containing {} items to {}".format(numberOfItems, receiverEmailAddress))
                except Exception as error:
                    failedEmailContent[failedEmailCount] = {"Failed_Email_Addresses": receiverEmailAddress}
                    failedEmailCount = failedEmailCount + 1
                    logging.info("The following error occurred: " + str(error))

            elif environment == 'development':
                developmentNumberOfEmails = developmentNumberOfEmails + 1
                print(emailHTML)
                print('\n')

        if failedEmailCount > 0:
            logging.info("Sending an Email to the Designated Staff to Inform them of Email Send Failures")
            emailFailureSubject = "Failure to Send: " + emailSubject
            emailFailureTableHeader = "There were issues sending " + emailTableHeader.replace(':', '') + " to the following Email Addresses:"
            emailFailureColumns = ["Failed_Email_Addresses"]
            emailFailureFooter = "Please Ensure the Attached Emails are Valid"

            emailFailureHTML = composeEmailMessage(css, emailFailureTableHeader, emailFailureColumns, failedEmailContent, emailFailureFooter)
            emailFailureToSend = composeEmail(smtpEmail, smtpEmail, '', emailFailureSubject, emailFailureHTML)

            try:
                sendEmail(smtpServer, emailFailureToSend)
                logging.info("The Notification for Failed Emails has been sent")
            except Exception as error:
                logging.info("The following error occurred: " + str(error))

        if environment == 'production':
            logging.info("The application successfully sent {} emails, {} emails failed to send".format(successfulEmailCount, failedEmailCount))
        elif environment == 'development':
            logging.info("The application found {} email addresses, the application would have sent {} emails in the Production environment".format(len(emailAddresses), developmentNumberOfEmails))

if __name__ == "__main__":
    main()
