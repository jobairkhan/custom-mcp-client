# Deployment Guide

This guide provides instructions for deploying the Apprentice MCP Agent to AWS Lambda.

## GitHub Actions Deployment

This section describes how to set up a continuous deployment pipeline using GitHub Actions.

### Continuous Integration with `ci.yml`

The `ci.yml` workflow, located at `.github/workflows/ci.yml`, is responsible for running tests and linting against the codebase. It is triggered on every push and pull request to the `main` and `develop` branches, ensuring code quality and consistency.

## Creating the Lambda Deployment Package - not CD

When deploying to AWS Lambda, it's important to ensure that the deployment package (the zip file) contains binaries that are compatible with the Lambda runtime environment (which is based on Linux). If you are developing on a non-Linux machine (like Windows or macOS), you need to build the deployment package inside a Linux environment. Docker is a great tool for this.

The following PowerShell command uses a Docker container to build a Lambda-compatible zip file. It mounts the current project directory into the container, installs the dependencies, and creates a `lambda_bundle.zip` file in the `dist` directory.

```powershell
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
docker run --rm -v ${PWD}:/app -w /app python:3.10-slim bash -c "apt-get update >/dev/null && apt-get install -y zip >/dev/null && rm -rf build && mkdir -p build dist && python -m pip install -r requirements.txt -t build && cp -r src build/ && cd build && zip -r ../dist/lambda_bundle-$stamp.zip ."
```

> **Note**: The command uses the `python:3.10-slim` Docker image to match the Python version of the project. If you are using a different Python version, update the image tag accordingly.

This command will produce a file named `lambda_bundle-<timestamp>.zip` in the `dist` directory. This is the file you will upload to AWS Lambda.

## Deploying to AWS Lambda from the Console

This section provides a step-by-step guide on how to deploy the `lambda_bundle.zip` file to AWS Lambda using the AWS Management Console.

### Prerequisites

- An AWS account with permissions to create and manage Lambda functions and IAM roles.
- The `lambda_bundle.zip` file created in the previous step.

### Step 1: Create the Lambda Function

1.  Navigate to the [AWS Lambda console](https://console.aws.amazon.com/lambda/).
2.  Click **Create function**.
3.  Select **Author from scratch**.
4.  For **Function name**, enter `apprentice-mcp-agent`.
5.  For **Runtime**, select **Python 3.10**.
6.  For **Architecture**, select **x86_64**.
7.  Under **Permissions**, create a new execution role with basic Lambda permissions or use an existing one.
8.  Click **Create function**.

### Step 2: Upload the Deployment Package

1.  In the **Code source** section, click the **Upload from** button.
2.  Select **.zip file**.
3.  Upload the `lambda_bundle-<timestamp>.zip` file that you created.
4.  Click **Save**.

### Step 3: Configure the Handler

1.  In the **Runtime settings** section, click **Edit**.
2.  For **Handler**, enter `src.lambda_handler.lambda_handler`.
3.  Click **Save**.

### Step 4: Configure Environment Variables

1.  Navigate to the **Configuration** tab.
2.  Go to the **Environment variables** section and click **Edit**.
3.  Add the necessary environment variables from your `.env.example` file (e.g., `OPENAI_API_KEY`, `JIRA_URL`, etc.).

### Step 5: Configure General Settings

1.  In the **General configuration** section, click **Edit**.
2.  Set the **Timeout** to a reasonable value (e.g., 5 minutes).
3.  Set the **Memory** to a reasonable value (e.g., 512 MB).
4.  Click **Save**.

### Step 6: Create a Function URL

1.  In the Lambda function's configuration, navigate to the **Function URL** section.
2.  Click **Create function URL**.
3.  For **Auth type**, select **NONE** to create a public URL.
4.  Configure CORS (Cross-Origin Resource Sharing) if needed.
5.  Click **Save**.

This will create a public URL that you can use to invoke your Lambda function.
