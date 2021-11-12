## Introduction

Notification Mailer is a customizable application designed to send email notificaitons to an individual or a group of individuals. The application is designed from a high level and allows the user to provide necessary information using specified environment files. The environment file will provide the details necessary for creating the email notification. 

### 

### Environment Variables 

Note: Multiple Environment Files may be used. It is recommended to create a "base" environment file that specifies variables shared across email notifications. 

#### Required Environment Variables 

##### Oracle Credentials

ORACLE_SERVER
ORACLE_PORT
ORACLE_SID
ORACLE_USERNAME
ORACLE_PASSWORD
ORACLE_CURRENT_SCHEMA
ORACLE_TNS_NAME

##### User Options 

EMAIL_SMTP_SERVER 
EMAIL_FROM - Specifies the Sender Email Address 
TABLE_CSS - Specifies the Styling for the Table in the Email
LOG_FILE - Specifies where the Application will Store Loging Information
EMAIL_SUBJECT - Specifies the Subject Line of the Email
EMAIL_TABLE_HEADER - 
TABLE_COLUMNS
QUERY

#### Optional Environmental Variables 

SQL_EMAIL_ROW - 
EMAIL_RECIPIENT - Specifies where the Email will be sent
EMAIL_CC
EMAIL_FOOTER

### Using Notification Mailer 

There are several ways to use the Notification Mailer. If your email is designed to be sent on a regular basis I would recommend using a scheduled chron task. 

QUERY_ENV_FILE=/home/ocr-apps/apps/notification-mailer/env_files/tasklist.env LOG_OUTPUT_FOLDER=/home/ocr-apps/apps/notification-mailer/notifier_tasklist_logs/  LOG_DOCKER_FOLDER=/app/notifier_tasklist_logs/ CONTAINER_NAME=tasklist docker-compose --file /home/ocr-apps/apps/notification-mailer/docker-compose.yml up
