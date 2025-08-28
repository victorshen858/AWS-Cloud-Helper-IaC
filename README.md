# AWS-Cloud-Expired-IAM-Access-Keys-Detector

## IAM Access Key Expiry Monitor (Generic, GovCloud-Compatible) **Use Case / Purpose**

AWS IAM access keys are **sensitive credentials** that, if compromised, can lead to unauthorized access to your account. Security best practices recommend **rotating access keys regularly** and avoiding keys that are older than 180 days.  

## Features

- **Automated Lambda Function:** Monitors IAM access keys and identifies expired or near-expiry keys.
- **SNS Notifications:** Sends alerts to subscribed emails when keys are nearing expiration.
- **GovCloud Compatible:** Works in both standard AWS regions and AWS GovCloud (US) regions.
- **CloudFormation Support:** Infrastructure-as-Code (IaC) template included for fast, repeatable deployments.
- **Configurable:** Threshold days (`EXPIRY_DAYS`), SNS topic, and other parameters can be customized via environment variables or configuration file.

---

## Repository Contents

| File | Description |
|------|-------------|
| `expiring-keys-monitor.yaml` | CloudFormation template to deploy Lambda, IAM Role, EventBridge Scheduler, and SNS Topic |
| `config.json` | Optional configuration file for custom parameters (EXPIRY_DAYS, SNS_TOPIC_ARN, ACCOUNT_NAME, ACCOUNT_ID) |
| `lambda_only/lambda_function.py` | Inline Lambda Python code for IAM access key monitoring |
| `scripts/deploy_stack.sh` | Optional shell script to deploy CloudFormation stack via AWS CLI |
| `aws-expiring-iam-access-keys-monitor.zip` | Lambda deployment package |
| `README.md` | This documentation |

---

## How It Works

1. **Lambda Execution:** Runs daily (via EventBridge Scheduler) and lists all IAM users and their active access keys.
2. **Expiration Check:** Compares key creation date to threshold (`EXPIRY_DAYS`, default 150).
3. **Alerting:** Publishes a notification to the configured SNS topic for keys older than threshold.
4. **Logging:** Logs all activity to CloudWatch for auditing and troubleshooting.

This workflow ensures administrators can act before keys reach the AWS 180-day rotation recommendation.

---

## Deployment

### CloudFormation (Recommended)

```bash
aws cloudformation deploy \
  --template-file expiring-keys-monitor.yaml \
  --stack-name iam-expired-keys-monitor \
  --capabilities CAPABILITY_NAMED_IAM
```

## **Why Use CloudFormation (IaC) for IAM Key Monitoring?**

Before using this CloudFormation template, setting up IAM key expiry monitoring manually in AWS would require completing all the following steps in the console:

1. Creating an **SNS topic** and subscribing email addresses.  
2. Creating an **IAM role** with the correct trust relationships and permissions for Lambda and EventBridge Scheduler.  
3. Configuring the **Lambda function**:
   - Uploading Python code  
   - Setting environment variables (`ACCOUNT_NAME`, `ACCOUNT_ID`, `SNS_TOPIC_ARN`, `EXPIRY_DAYS`)  
   - Allocating **memory, timeout, and ephemeral storage**  
4. Creating an **EventBridge Scheduler** to run Lambda daily with the correct timezone and flexible time window.  
5. Testing the Lambda and confirming SNS delivery.  

> Each of these steps is time-consuming, error-prone, and easy to misconfigure — especially for beginners.  

With **CloudFormation (IaC)**, all of these steps are automated:  

- **Single deployment:** Upload the template and provide required parameters.  
- **Consistent state:** Resources are created exactly as specified.  
- **Rollback on error:** If any part of the stack fails, CloudFormation rolls back to the previous state — avoiding partial or broken setups.  
- **Reproducibility:** You can redeploy the same template across multiple accounts or regions in minutes.  
- **Easy updates:** Changing a parameter (e.g., `EXPIRY_DAYS`) and redeploying updates the stack without manual reconfiguration.  

This template demonstrates the **power of IaC**, saving you time, reducing mistakes, and giving a fully automated, production-ready setup for monitoring IAM access keys.

---

## **Manual Deployment via AWS Console**

### **Step 1: Create SNS Topic**
1. Open **AWS Console → SNS → Topics → Create topic**.  
2. Choose **Standard Topic**.  
3. Name: `IAMKeyAlerts` (or your preferred name).  
4. Create the topic.  
5. Add **subscription** to your email for notifications. Confirm subscription.

---

### **Step 2: Create IAM Role**
1. Open **AWS Console → IAM → Roles → Create role**.  
2. Select **Lambda** as trusted entity.  
3. Add another **trusted entity**: EventBridge Scheduler (if using GovCloud, ensure the Scheduler principal is correct).  
4. Attach policy with the following permissions:

{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["iam:ListUsers","iam:ListAccessKeys"], "Resource": "*"},
    {"Effect": "Allow", "Action": ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"], "Resource": "*"},
    {"Effect": "Allow", "Action": ["sns:Publish"], "Resource": "arn:aws:sns:REGION:ACCOUNT_ID:IAMKeyAlerts"},
    {"Effect": "Allow", "Action": ["kms:Decrypt"], "Resource": "*"},
    {"Effect": "Allow", "Action": ["organizations:DescribeAccount"], "Resource": "*"}
  ]
}



### **Step 3: Create Lambda Function**

1. Open **AWS Lambda → Create function → Author from scratch**.  
2. Name: `iam-check-expired-access-keys`.  
3. Runtime: **Python 3.13**.  
4. Permissions: Choose **Use an existing role** → `iam-expired-keys-monitor`.  
5. Configure **Memory & Timeout**:
   - Memory: `8 GB` (8000 MB)  
   - Timeout: `15 min` (900 seconds)  
   - Ephemeral storage: `1.8 GB`  
6. Set **Environment Variables**:
   ```text
   ACCOUNT_NAME = your account name
   ACCOUNT_ID = your AWS account ID
   SNS_TOPIC_ARN = SNS topic ARN
   EXPIRY_DAYS = 150
### **Step 4: Test Lambda**

1. Open **Test → Configure test event** → name: `default`, payload: `{}`.  
2. Run **Test**.  
3. Check **CloudWatch logs** for output: `Using EXPIRY_DAYS = 150` and expired keys.  
4. Verify **SNS email** received.

---

### **Step 5: Create EventBridge Scheduler**

1. Open **AWS Console → EventBridge → Scheduler → Create schedule**.  
2. Name: `IAMAccessKeysMonitorDaily`.  
3. Frequency: **Rate expression** → `rate(1 day)`.  
4. Timezone: `America/New_York`.  
5. FlexibleTimeWindow: **OFF** (avoids scheduling confusion).  
6. Target: Lambda function `iam-check-expired-access-keys`.  
7. Role: Choose **existing role** → `iam-expired-keys-monitor`.  
8. Input: `{}` (default).

---

### **Step 6: Verify Everything Works**

- Lambda logs in **CloudWatch**.  
- SNS sends alerts for expired keys.  
- EventBridge Scheduler runs daily automatically.

---

## **Lessons Learned / Common Pitfalls**

1. **FlexibleTimeWindow “OFF”** is critical — otherwise Scheduler may delay invocation.  
2. **IAM Role trust**: Lambda + Scheduler must be included. Missing either → invocation fails.  
3. **Environment variables** must match deployed values. `EXPIRY_DAYS` mismatch is a common source of false alerts.  
4. **GovCloud KMS**: Ensure `kms:Decrypt` is granted.  
5. **Lambda memory/timeout**: Large accounts require 8 GB and 15 min timeout for pagination.  
6. **SNS Subscription confirmation**: Forgetting this prevents email delivery.
