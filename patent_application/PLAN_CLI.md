# Patent Classifier – AWS Deployment Plan

This document describes a phased approach to deploying the Patent Classifier
Streamlit application to AWS. The application is a single-container web app
that calls Amazon Bedrock (Claude Haiku 4.5 via a cross-region inference
profile) and requires no database or persistent storage.

The recommended hosting target is **AWS App Runner** — it is the simplest
path from a container image to a publicly accessible HTTPS endpoint with
auto-scaling, and it has native IAM role support so no credentials ever
touch the container.

---

## Phase 1 — IAM Foundations

**Goal:** Create the least-privilege IAM role the application will assume at
runtime. Nothing is deployed that serves traffic yet. Completing this phase
first means the permissions are reviewed and approved before any compute
resource is created.

### Steps

1. **Create the application IAM role**

   Create a role named `patent-classifier-app-role` with the following
   trust policy so that App Runner tasks can assume it:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Service": "tasks.apprunner.amazonaws.com"
         },
         "Action": "sts:AssumeRole"
       }
     ]
   }
   ```

2. **Attach a least-privilege inline policy**

   The application needs exactly one Bedrock action on exactly one resource
   (the cross-region inference profile). Create and attach an inline policy
   named `BedrockInvokePolicy`:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "AllowBedrockInference",
         "Effect": "Allow",
         "Action": "bedrock:InvokeModel",
         "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"
       }
     ]
   }
   ```

   > **Note:** If you use the cross-region inference profile ARN
   > (`us.anthropic.claude-haiku-4-5-20251001-v1:0`) instead of the
   > foundation model ARN, add a second statement that allows
   > `bedrock:InvokeModel` on the inference profile ARN as well, or use a
   > wildcard scoped to your account:
   > `arn:aws:bedrock:us-east-1:<ACCOUNT_ID>:inference-profile/*`

3. **Create the App Runner access role** (needed for ECR image pulls)

   App Runner also needs a build-time role to pull images from ECR. Create a
   role named `patent-classifier-ecr-role` with trust policy:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Service": "build.apprunner.amazonaws.com"
         },
         "Action": "sts:AssumeRole"
       }
     ]
   }
   ```

   Attach the AWS-managed policy
   `AmazonEC2ContainerRegistryReadOnly` to this role.

### Verification

- Confirm both roles exist in the IAM console with the correct trust policies.
- Confirm no `*` actions or `*` resources appear in the inline policy.
- Optionally run `aws iam simulate-principal-policy` to verify that only
  `bedrock:InvokeModel` is granted.

---

## Phase 2 — Container Image

**Goal:** Package the application as a Docker image and push it to Amazon
Elastic Container Registry (ECR).

### Steps

1. **Create an ECR repository**

   ```bash
   aws ecr create-repository \
     --repository-name patent-classifier \
     --region us-east-1
   ```

2. **Write a Dockerfile**

   ```dockerfile
   FROM python:3.12-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY doc.py prompt_config.txt ./

   EXPOSE 8081

   CMD ["streamlit", "run", "doc.py", \
        "--server.port=8081", \
        "--server.address=0.0.0.0", \
        "--server.headless=true"]
   ```

3. **Build and push the image**

   ```bash
   # Authenticate Docker to ECR
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin \
     <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

   # Build
   docker build -t patent-classifier .

   # Tag
   docker tag patent-classifier:latest \
     <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/patent-classifier:latest

   # Push
   docker push \
     <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/patent-classifier:latest
   ```

### Verification

- Confirm the image appears in the ECR repository.
- Optionally run the container locally to confirm it starts cleanly:
  ```bash
  docker run -p 8081:8081 patent-classifier:latest
  ```
  (Local Bedrock calls will fail without credentials, but the UI should load.)

---

## Phase 3 — App Runner Service

**Goal:** Deploy the container as a publicly accessible HTTPS service using
AWS App Runner, wiring in the IAM roles from Phase 1.

### Steps

1. **Create the App Runner service**

   Via the AWS Console or CLI:

   ```bash
   aws apprunner create-service \
     --service-name patent-classifier \
     --source-configuration '{
       "ImageRepository": {
         "ImageIdentifier": "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/patent-classifier:latest",
         "ImageConfiguration": {
           "Port": "8081"
         },
         "ImageRepositoryType": "ECR"
       },
       "AuthenticationConfiguration": {
         "AccessRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/patent-classifier-ecr-role"
       },
       "AutoDeploymentsEnabled": false
     }' \
     --instance-configuration '{
       "Cpu": "1 vCPU",
       "Memory": "2 GB",
       "InstanceRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/patent-classifier-app-role"
     }' \
     --region us-east-1
   ```

2. **Wait for the service to reach `RUNNING` state**

   ```bash
   aws apprunner describe-service \
     --service-arn <SERVICE_ARN> \
     --region us-east-1 \
     --query 'Service.Status'
   ```

3. **Retrieve the public URL**

   ```bash
   aws apprunner describe-service \
     --service-arn <SERVICE_ARN> \
     --region us-east-1 \
     --query 'Service.ServiceUrl'
   ```

   The application is served at `https://<service-url>` (App Runner provides
   TLS termination automatically).

### Verification

- Open the service URL in a browser and confirm the Streamlit UI loads.
- Upload a sample PDF and click **Classify** to confirm the Bedrock call
  succeeds end-to-end.
- Check App Runner logs in CloudWatch for any errors.

---

## Phase 4 — Observability and Hardening (Optional)

These steps are recommended before sharing the application with end users.

| Concern | Recommendation |
|---|---|
| **Access control** | Place the App Runner service behind an Application Load Balancer with Cognito authentication, or restrict access to a VPC using App Runner VPC ingress. |
| **Custom domain** | Associate a custom domain via `aws apprunner associate-custom-domain`. |
| **Logging** | App Runner streams stdout to CloudWatch Logs automatically. Create a log-based metric and alarm for Bedrock errors. |
| **Cost control** | Set an AWS Budget alert for Bedrock token spend. App Runner charges only when requests are being served (no idle cost beyond the minimum instance). |
| **Image updates** | Enable `AutoDeploymentsEnabled: true` on the App Runner service, or add a CI/CD pipeline (e.g., GitHub Actions → ECR push → App Runner redeploy) to automate future deployments. |
| **Bedrock model access** | Confirm the Claude Haiku 4.5 model is enabled in the Bedrock Model Access console for your account in `us-east-1`. |

---

## Summary of AWS Resources Created

| Phase | Resource | Name |
|---|---|---|
| 1 | IAM Role (runtime) | `patent-classifier-app-role` |
| 1 | IAM Role (ECR pull) | `patent-classifier-ecr-role` |
| 2 | ECR Repository | `patent-classifier` |
| 3 | App Runner Service | `patent-classifier` |
