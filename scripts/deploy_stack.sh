#!/bin/bash
# Deploy IAM Key Expiry Monitoring stack via CloudFormation

# Load configuration
CONFIG_FILE="../config/config.json"
AWS_ACCOUNT_NAME=$(jq -r '.aws_account_name' $CONFIG_FILE)
AWS_ACCOUNT_ID=$(jq -r '.aws_account_id' $CONFIG_FILE)
NOTIFICATION_EMAIL=$(jq -r '.notification_email' $CONFIG_FILE)
EXPIRY_DAYS=$(jq -r '.expiry_days' $CONFIG_FILE)

STACK_NAME="IAM-Key-Expiry-Monitor"
TEMPLATE_FILE="../cloudformation/expiring-keys-monitor.yaml"

echo "Deploying CloudFormation stack: $STACK_NAME"
echo "Account Name: $AWS_ACCOUNT_NAME"
echo "Account ID: $AWS_ACCOUNT_ID"
echo "Notification Email: $NOTIFICATION_EMAIL"
echo "Expiry Days: $EXPIRY_DAYS"

aws cloudformation deploy \
  --stack-name $STACK_NAME \
  --template-file $TEMPLATE_FILE \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      AccountName=$AWS_ACCOUNT_NAME \
      AccountID=$AWS_ACCOUNT_ID \
      NotificationEmail=$NOTIFICATION_EMAIL

echo "Deployment complete. Check AWS Console for stack status."
