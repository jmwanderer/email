# Email Utilities and Configuration

## Exim4 with Amazon SES

The Exim4 mail transfer agent running on Debian Linux configured to
work with Amazon SES as a smart host.

### Setup
- Exim4 is configured for local email and smarthost
- Amazon SES configured to handle mail for a domain: e.g. example.net
- Send Email:
    - Local email delivered to local mailboxes
    - Exim4 forwards all non-local email to the Amazon SES enpoint
- Receiving email:
    - Amazon SES stores email received to domain in an S3 bucket
    - AWS user configured for access to SES SMTP service and S3 bucket
    - Run a Python script to retrieve email from the S3 bucket and deliver locally

### SMTP Settings Amazon SES
- SMTP endpoint: e.g. email-smtp.us-west-2.amazonaws.com
- SES Configuration > Email Recieving
    - Default rule with:
        - Condition:  @domain
        - Action: deliver to an amazon S3 bucket

### AWS User and Credentials
- Reduced capability dedicated AWS user for email
- Policy of AmazonSESFullAccess for SMTP access credentials
- Policy for access to S3 bucket. Amazon S3 > Buckets > _bucket name_
    - Add to bucket policy:


```
       {
            "Sid": "Email-Access",
            "Effect": "Allow",
            "Principal": {
                "AWS": "user ARN"
            },
            "Action": [
                "s3:ListBucket",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::bucket-name/*",
                "arn:aws:s3:::bucket-name"
            ]
        }

```

#### Exim4 Configuration

Run conmfiguration with: `sudo dpkg-reconfigure exim4-config`

Selections:

- Smart host with local email
- System mail name: default
- IP Address to listen: default (127.0.0.1, ::1)
- Other destinations for which mail is accepted:
    - system-name
    - domain-name (e.g. example.net)
- Hostname of outgoing smart host:
      - SES SMTP endpoing. (e.g. email-smtp.us-west-2.amazonaws.com::587 (note the double colon)
- Hide local mail name in going mail
    - Yes
    - Enable rewriting (ensure From: has what SES expects/requires)
- Visible domain name for local users:
    - domain name (e.g. example.net)
- Keep DNS queries minimal: No
- Deliver method for local email: your choise, I use mbox
- Split configuration into small files: you choice, I select No

Further configuration:

- /etc/aliases
    - Entries to direct email addresses to local users
    - format   email-name: local-user
    - e.g.     info: jim
- /etc/exim4/passwd.client:
    - configure access credentials for Exi4 to access SES SMTP
    - _SMTP endpoint_:_login_:_password_
    - e.g.  email-smtp.us-west-2.amazonaws.com:34343DDE3:DSDFDSF23432

### Script: get_s3_email.py

Fetch email from S3 bucket and deliver locally

#### Process
- Get a list of objects in the S3 bucket
- For each object in the lop level
    - Download
    - Parse as an email message
    - Attempt to send with local SMTP deliver
    - Success: copy to /processed directory in S3 bucket
    - Fail: copy to /error directory in S3 bucket
    - Delete original object

#### Setup

Create a directory for the script. Copy script, create a Python venv, and install the boto library.

```
mkdir process_email
cd process_email
cp ~/email/get_s3_email.py .
python -m venv .venv
source .venv/bin/activate
pip install boto
```

AWS S3 bucket:
- bucket-name
- aws s3 ls s3://bucket-name

Run script:

```
python get_s3_emai.py bucket-name
```

Cront entry:

```
0,15,30,45 * * * * cd ~/process_email; . ./venv/bin/activate; python get_s3_mail.py bucket-name
```

### Resources
- https://wiki.debian.org/Exim#Configuration
- https://aws.amazon.com/ses
- https://aws.amazon.com/s3/




```

