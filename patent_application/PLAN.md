# Patent Classifier – AWS Deployment Plan

This document describes a phased approach to deploying the Patent Classifier
Streamlit application to AWS using **CloudFormation** for all infrastructure.
Using CloudFormation means every resource is tracked in a stack, changes are
reviewable as changesets before they are applied, and teardown is a single
stack-delete command.

The hosting target is **AWS App Runner** — it is the simplest path from a
container image to a publicly accessible HTTPS endpoint with auto-scaling,
and it has native IAM role support so no credentials ever touch the container.

All templates should be saved to the `infra/` directory of this project.

---

## Phase 1 — IAM Foundations

**Goal:** Deploy only the IAM roles the application needs. No compute or
network resources are created yet. This lets the permissions be reviewed and
approved in isolation before anything serves traffic.

### Template — `infra/phase1-iam.yaml`

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: IAM roles for the Patent Classifier application

Resources:

  # Runtime role — assumed by the running App Runner container
  AppRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: patent-classifier-app-role
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: tasks.apprunner.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: BedrockInvokePolicy
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Sid: AllowBedrockInference
                Effect: Allow
                Action: bedrock:InvokeModel
                Resource:
                  # Foundation model ARN
                  - !Sub "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"
                  # Cross-region inference profile ARN (scoped to this account)
                  - !Sub "arn:aws:bedrock:us-east-1:${AWS::AccountId}:inference-profile/*"

  # ECR access role — assumed by App Runner at build time to pull images
  EcrAccessRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: patent-classifier-ecr-role
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: build.apprunner.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

Outputs:
  AppRoleArn:
    Value: !GetAtt AppRole.Arn
    Export:
      Name: patent-classifier-app-role-arn

  EcrAccessRoleArn:
    Value: !GetAtt EcrAccessRole.Arn
    Export:
      Name: patent-classifier-ecr-role-arn
```

### Deploy

```bash
aws cloudformation deploy \
  --stack-name patent-classifier-iam \
  --template-file infra/phase1-iam.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Verification

```bash
# Confirm stack reached CREATE_COMPLETE
aws cloudformation describe-stacks \
  --stack-name patent-classifier-iam \
  --region us-east-1 \
  --query "Stacks[0].StackStatus"

# Confirm the inline policy contains no wildcard actions
aws iam get-role-policy \
  --role-name patent-classifier-app-role \
  --policy-name BedrockInvokePolicy
```

---

## Phase 2 — Container Image

**Goal:** Create an ECR repository via CloudFormation, then build and push
the application image. The image build step is a local Docker operation;
only the repository itself is managed as infrastructure.

### Template — `infra/phase2-ecr.yaml`

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: ECR repository for the Patent Classifier container image

Resources:

  EcrRepository:
    Type: AWS::ECR::Repository
    Properties:
      RepositoryName: patent-classifier
      ImageScanningConfiguration:
        ScanOnPush: true
      LifecyclePolicy:
        LifecyclePolicyText: |
          {
            "rules": [
              {
                "rulePriority": 1,
                "description": "Keep only the 5 most recent images",
                "selection": {
                  "tagStatus": "any",
                  "countType": "imageCountMoreThan",
                  "countNumber": 5
                },
                "action": { "type": "expire" }
              }
            ]
          }

Outputs:
  RepositoryUri:
    Value: !GetAtt EcrRepository.RepositoryUri
    Export:
      Name: patent-classifier-ecr-uri
```

### Deploy

```bash
aws cloudformation deploy \
  --stack-name patent-classifier-ecr \
  --template-file infra/phase2-ecr.yaml \
  --region us-east-1
```

### Write the Dockerfile

Save the following as `Dockerfile` in the project root:

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

### Build and push the image

```bash
# Get the repository URI from the stack output
REPO_URI=$(aws cloudformation describe-stacks \
  --stack-name patent-classifier-ecr \
  --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='RepositoryUri'].OutputValue" \
  --output text)

# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  "$(echo $REPO_URI | cut -d/ -f1)"

# Build, tag, and push
docker build -t patent-classifier .
docker tag patent-classifier:latest $REPO_URI:latest
docker push $REPO_URI:latest
```

### Verification

```bash
aws ecr describe-images \
  --repository-name patent-classifier \
  --region us-east-1 \
  --query "imageDetails[*].imageTags"
```

---

## Phase 3 — App Runner Service

**Goal:** Deploy the App Runner service using the image from Phase 2 and the
IAM roles from Phase 1. Stack exports are used to reference cross-stack
resources so there are no hard-coded ARNs.

### Template — `infra/phase3-apprunner.yaml`

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: App Runner service for the Patent Classifier application

Parameters:
  ImageTag:
    Type: String
    Default: latest
    Description: The ECR image tag to deploy

Resources:

  AppRunnerService:
    Type: AWS::AppRunner::Service
    Properties:
      ServiceName: patent-classifier
      SourceConfiguration:
        AuthenticationConfiguration:
          AccessRoleArn: !ImportValue patent-classifier-ecr-role-arn
        AutoDeploymentsEnabled: false
        ImageRepository:
          ImageIdentifier: !Sub
            - "${RepoUri}:${ImageTag}"
            - RepoUri: !ImportValue patent-classifier-ecr-uri
          ImageRepositoryType: ECR
          ImageConfiguration:
            Port: "8081"
      InstanceConfiguration:
        Cpu: 1 vCPU
        Memory: 2 GB
        InstanceRoleArn: !ImportValue patent-classifier-app-role-arn

Outputs:
  ServiceUrl:
    Description: Public HTTPS URL for the Patent Classifier
    Value: !Sub "https://${AppRunnerService.ServiceUrl}"
```

### Deploy

```bash
aws cloudformation deploy \
  --stack-name patent-classifier-service \
  --template-file infra/phase3-apprunner.yaml \
  --region us-east-1
```

To deploy a specific image tag:

```bash
aws cloudformation deploy \
  --stack-name patent-classifier-service \
  --template-file infra/phase3-apprunner.yaml \
  --parameter-overrides ImageTag=v1.2.0 \
  --region us-east-1
```

### Retrieve the service URL

```bash
aws cloudformation describe-stacks \
  --stack-name patent-classifier-service \
  --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='ServiceUrl'].OutputValue" \
  --output text
```

### Verification

- Open the URL in a browser and confirm the Streamlit UI loads.
- Upload a sample PDF and click **Classify** to confirm the Bedrock call
  succeeds end-to-end.
- Check App Runner logs in the CloudWatch console for any errors.

---

## Phase 4 — Observability and Hardening (Optional)

These steps are recommended before sharing the application with end users.
Each item can be added to an `infra/phase4-hardening.yaml` template or
incorporated as additional resources in the Phase 3 template.

| Concern | CloudFormation approach |
|---|---|
| **Bedrock model access** | Confirm the Claude Haiku 4.5 model is enabled in the Bedrock Model Access console for `us-east-1` before deploying Phase 3. This is a one-time console action; it cannot be managed via CloudFormation. |
| **Access control** | Add an `AWS::AppRunner::VpcIngressConnection` to restrict access to a VPC, or front the service with an ALB and Cognito. |
| **Custom domain** | Use `aws apprunner associate-custom-domain` (CLI only — no CloudFormation resource available as of late 2026). |
| **CloudWatch alarm** | Add an `AWS::CloudWatch::Alarm` on the App Runner `Http5xxRequests` metric to catch Bedrock errors. |
| **Cost control** | Add an `AWS::Budgets::Budget` resource with an alert threshold for Bedrock token spend. |
| **Image updates** | Set `AutoDeploymentsEnabled: true` in the Phase 3 template, or add a CodePipeline stack that triggers on ECR push events. |

---

## Teardown

Delete stacks in reverse order to avoid dependency errors:

```bash
aws cloudformation delete-stack --stack-name patent-classifier-service --region us-east-1
aws cloudformation wait stack-delete-complete --stack-name patent-classifier-service --region us-east-1

aws cloudformation delete-stack --stack-name patent-classifier-ecr --region us-east-1
aws cloudformation wait stack-delete-complete --stack-name patent-classifier-ecr --region us-east-1

aws cloudformation delete-stack --stack-name patent-classifier-iam --region us-east-1
```

> **Note:** ECR repositories that contain images will block stack deletion.
> Either set `EmptyOnDelete: true` on the `AWS::ECR::Repository` resource,
> or manually delete the images before tearing down the ECR stack.

---

## Summary of AWS Resources and Stacks

| Phase | Stack | Resource type | Logical name |
|---|---|---|---|
| 1 | `patent-classifier-iam` | `AWS::IAM::Role` | `AppRole` |
| 1 | `patent-classifier-iam` | `AWS::IAM::Role` | `EcrAccessRole` |
| 2 | `patent-classifier-ecr` | `AWS::ECR::Repository` | `EcrRepository` |
| 3 | `patent-classifier-service` | `AWS::AppRunner::Service` | `AppRunnerService` |
