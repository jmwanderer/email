#
# Fetch mail files from Amazon S3 and forward to local SMTP
#
# Files that fail to send are moved to the error/ directory in the bucket.
# SMTP connection errors fail the script and leave the mail files
# in place.
#
# Report any failures to stdout, otherwise it is silent
#

import datetime
import io
import sys
import email
import email.policy
import smtplib

import boto3

verbose = False
delete_mail = False

def process_email(bucket_name: str):
    if verbose:
        print(f"Retriveing email from bucket: {bucket_name}")

    # Verify we can connect to the SMTP server before doing calls to S3.
    server = smtplib.SMTP("localhost")
    server.noop()
    server.quit()

    # Access the bucket as a resource.
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)

    # Count results
    total_count = 0
    sent_count = 0

    # Get list of bucket contents.
    contents = bucket.objects.all()

    # Walk each object in the bucket
    for obj_summary in contents:
        # Ignore sub-directories
        if '/' in obj_summary.key:
            continue

        # Download file into a bytes IO stream
        obj = bucket.Object(obj_summary.key)
        data = io.BytesIO()
        obj.download_fileobj(data)
        data.seek(0)
        total_count += 1

        # Parse email message
        msg = email.message_from_binary_file(data, policy=email.policy.default)

        # Open new SMTP connection for each send
        server = smtplib.SMTP("localhost")
        sent_ok = False
        try:
            server.send_message(msg)
            sent_count += 1
            sent_ok = True
        except (smtplib.SMTPSenderRefused,
                smtplib.SMTPRecipientsRefused,
                smtplib.SMTPDataError) as e:
            print(f"error on {obj.key}")
            print(f"msg to: {msg['To']}, subj: {msg['Subject']}")
            print(str(e))

        copy_dir = None
        if not sent_ok:    
            # Send to error directory
            copy_dir = "error"
        elif not delete_mail:
            # Send to a processed directory
            copy_dir = "processed"

        # To move, make a new copy....
        if copy_dir:
            copy = bucket.Object(f"{copy_dir}/{obj_summary.key}")
            copy.copy_from(CopySource="%s/%s" % (bucket_name, obj_summary.key))

        # Remove original file
        obj.delete()

        # Cleanup connection - one email per connection.
        server.quit()

    if verbose or sent_count != total_count:
        now = datetime.datetime.now()
        now_time = now.isoformat(timespec='seconds', sep=' ')
        print(f"{now_time}: Processed {sent_count} / {total_count} messages.")

    if sent_count != total_count:
        print(f"Check s3://{bucket_name}/error/ for undeliverable messages.")



if __name__ == '__main__':
    # Check the verbose option
    if '-v' in sys.argv:
        verbose = True
        sys.argv.remove('-v')

    # Check the delet eoption
    if '-d' in sys.argv:
        delete_mail = True
        sys.argv.remove('-d')

    if len(sys.argv) != 2:
        print("Usage: get_s3_emai.py [-v] [-d] <bucket_name>")
        sys.exit(-1)
    
    bucket_name = sys.argv[1]
    process_email(bucket_name)






