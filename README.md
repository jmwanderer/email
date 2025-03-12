# Email Utilities and Configuration

## Exim4 with Amazon SES

This is a summary of configuring Exim4 to send and receive email via
Amazon SES with the help of a Python script. The Exim4 mail transfer 
agent is running on Debian 12 Linux and configured to
work with Amazon SES as a smart host.

### System Setup
- Exim4 is configured for local email and smarthost
- Amazon SES configured to handle mail for a domain: e.g. example.net
- Send Email:
    - Local email delivered to local mailboxes
    - Exim4 forwards all non-local email to the Amazon SES endpoint
- Receiving email:
    - Amazon SES stores email received to the domain in an S3 bucket
    - An AWS user is configured for access to SES SMTP service and S3 bucket
    - The Python script retrieves email from the S3 bucket and delivers locally

###  Email Download Script

Script: *get_s3_email.py*

Fetches email from S3 bucket and send to the local SMTP server listening
on 127.0.0.1

#### Script Process
- Get a list of objects in the S3 bucket
- For each object in the lop level
    - Download object
    - Parse object as an email message
    - Attempt to send to local SMTP deliver
    - Success: copy to /processed directory in S3 bucket
    - Fail: copy to /error directory in S3 bucket
    - Delete original object

#### Script Setup

Clone or download the project, example assumes the project directory is *email*.

Steps:

- Create a Python venv and activate
- Install boto
- Configure AWS credentials
- Test S3 bucket access
- Run Script
- Setup cron entry

##### Create venv and Install boto

```
cd email
python -m venv venv
source venv/bin/activate
pip install boto
```

##### Configure AWS Credentials

An easy way to configure aws_access_key_id and aws_secret_access_key 
for access to the S3 bucket is to set up ~/.aws/credentials. 


##### Test Bucket Access

AWS S3 bucket:

- __bucket-name__  e.g. domain-email
- aws s3 ls s3://__bucket-name__


##### Run script

```
cd email
source venv/bin/activate
python get_s3_email.py __bucket-name__
```

##### Cron entry:

Fetch email every 15 minutes:

```
0,15,30,45 * * * * cd ~/email; . ./venv/bin/activate; python get_s3_mail.py __bucket-name__
```

### SMTP Settings Amazon SES

Amazon SES setup:

- SMTP endpoint: e.g. email-smtp.us-west-2.amazonaws.com
- SES Configuration > Email Recieving
    - Default rule with:
        - Condition:  @domain
        - Action: deliver to an amazon S3 bucket

### AWS User and Credentials

It is good practice to create a dedicated user with limited
capability for use in accessing the Amazon SES SMTP endpoint and the
S3 bucket. 

- Policy of AmazonSESFullAccess for SMTP access credentials
- Policy for access to S3 bucket. Amazon S3 > Buckets > _bucket name_
    - Add to bucket policy:


```
       {
            "Sid": "Email-Access",
            "Effect": "Allow",
            "Principal": {
                "AWS": "__user ARN__"
            },
            "Action": [
                "s3:ListBucket",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::__bucket-name__/*",
                "arn:aws:s3:::__bucket-name__"
            ]
        }

```


### Exim4 Configuration

Run configuration with: `sudo dpkg-reconfigure exim4-config`

- Select: mail sent by smarthost
- System mail name: the default is a safe choice
- IP Address to listen: default (127.0.0.1, ::1)
- Other destinations for which mail is accepted:
    - leave the system name
    - add the domain-name (e.g. example.net)
- Machines to relay mail for: leave blank
- Hostname of outgoing smart host:
    - SES SMTP endpoint name, *double colon*, port 587
    - e.g. email-smtp.us-west-2.amazonaws.com::587  *note the double colon*
- Hide local mail name in going mail
    - Yes, enable rewriting (ensure that From: has what SES expects/requires)
- Visible domain name for local users:
    - enter the domain name (e.g. example.net)
- Keep DNS queries minimal: No
- Deliver method for local email: your choise, I use mbox
- Split configuration into small files: you choice, I select No

Further system configuration:

Configure specific email addresses to be delivered to specific users.
For example, forward info@example.net to the local user jim

- /etc/aliases
    - Entries to direct email addresses to local users
    - format   email-name: local-user
    - e.g.     info: jim
 
Configure SMTP login credentials to access Amazon SES SMTP endpoint.

- /etc/exim4/passwd.client:
    - configure access credentials for Exi4 to access SES SMTP
    - _SMTP endpoint_:_login_:_password_
    - e.g.  email-smtp.us-west-2.amazonaws.com:34343DDE3:DSDFDSF23432

### Resources
- https://wiki.debian.org/Exim#Configuration
- https://aws.amazon.com/ses
- https://aws.amazon.com/s3/



