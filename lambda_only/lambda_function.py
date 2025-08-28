import boto3
from datetime import datetime, timezone
import os

# Environment variables (set via Lambda console or CloudFormation)
ACCOUNT_NAME = os.environ["ACCOUNT_NAME"]
ACCOUNT_ID = os.environ["ACCOUNT_ID"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
EXPIRY_DAYS = int(os.environ.get("EXPIRY_DAYS"))

# AWS clients
iam = boto3.client("iam")
sns = boto3.client("sns")
sts = boto3.client("sts")

def lambda_handler(event, context):
    now = datetime.now(timezone.utc)
    expired_keys = []

    # List all IAM users
    users = iam.list_users()["Users"]
    for user in users:
        user_name = user["UserName"]
        keys = iam.list_access_keys(UserName=user_name)["AccessKeyMetadata"]
        for key in keys:
            key_id = key["AccessKeyId"]
            status = key["Status"]
            create_date = key["CreateDate"]
            age_days = (now - create_date).days
            if age_days >= EXPIRY_DAYS:
                expired_keys.append({
                    "UserName": user_name,
                    "AccessKeyId": key_id,
                    "Status": status,
                    "CreateDate": create_date.strftime("%Y-%m-%d"),
                    "AgeDays": age_days
                })

    # Prepare report
    if expired_keys:
        report_lines = [
            f"User: {k['UserName']} | KeyId: {k['AccessKeyId']} | Status: {k['Status']} | Created: {k['CreateDate']} | Age: {k['AgeDays']} days"
            for k in expired_keys
        ]
        report_content = "\n".join(report_lines)
    else:
        report_content = "No expired or expiring keys found."

    # Publish to SNS
    email_subject = f"IAM Access Key Expiry Report - Account {ACCOUNT_ID}"
    email_body = (
        "AWS Account ID: " + ACCOUNT_ID + "\n"
        "AWS Account Name: " + ACCOUNT_NAME + "\n\n"
        "The following IAM users have expired or expiring access keys (≥" + str(EXPIRY_DAYS) + " days old):\n\n"
        + report_content
    )

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=email_subject,
        Message=email_body
    )

    return {
        "statusCode": 200,
        "expired_keys_count": len(expired_keys),
        "expired_keys": expired_keys
    }
