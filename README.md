# Contributor License Agreement Bot

This implements a GitHub Application to manage Contributor License Agreement (CLA) signing for repositories it is installed in.

## Concepts

### Agreements

Agreements are managed via Django admin, are formatted in Markdown, and are “write once”. Agreements can be marked as compatible with other agreements so that historic signatures are considered valid when applicable.

### Signatures

Users can login to view agreements that are awaiting signature, past signatures, and the email addresses provided for past signatures.

### Automation

When installed, this application will monitor GitHub Pull Requests for changes and determine if a CLA has been signed for all authors.

If a new signature is required, a GitHub Commit Status will be created and a comment will be created directing users to the application in order to sign.

If an acceptable signature exists, a GitHub Commit Status will be created. If a past comment exists from the application it will be updated to indicate that all necessary signatures have been completed.

## Development

This project is built with Django, django-github-app, and gidgethub.

Local development uses Docker, Docker Compose, and GNU make.

## Pre-requisites

In order to manually test the application you will first need to create a GitHub Application and have a way of accepting GitHub webhooks from the public internet, such as ngrok.

```shell
ngrok http 8000 -subdomain my-cla-bot
```

Adjust the subdomain to make identifiable to you.

Create a GitHub Application using the following settings:

* GitHub App name: `My CLA Bot` (adjust to make identifiable to you)
* Homepage URL: `https://my-cla-bot.ngrok.io` (adjust to match your ngrok subdomain)
* Callback URL: `https://my-cla-bot.ngrok.io/auth/gh/` (adjust to match your ngrok subdomain)
* Webhook:
    * \[x\] Active
    * Webhook URL: `https://my-cla-bot.ngrok.io/gh/` (adjust to match your ngrok subdomain)
    * Secret: `aRandomlyGeneratedSecret` (consider `python3 -c 'import secrets; print(secrets.token_urlsafe())'`)
* Permissions
    * Repository Permissions:
        * Commit statuses: Read and write
        * Pull requests: Read and write
    * Organization permissions:
        * Members: Read-only
    * Account permissions:
        * Email addresses: Read-only
* Subscribe to events:
    * [x] Pull request

“Generate a new client secret” and store it safely.

“Generate a private key” and store it safely.

A development environment can now be created by writing a `.env` file in the root of the repository with the following contents:

```shell
DJANGO_ALLOWED_HOSTS=localhost,my-cla-bot.ngrok.io
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://my-cla-bot.ngrok.io
DJANGO_SITE_URL=https://my-cla-bot.ngrok.io/
GITHUB_APP_ID=<GitHub App ID>
GITHUB_CLIENT_ID=<GitHub Client ID>
GITHUB_NAME="My CLA Bot"
GITHUB_OAUTH_APPLICATION_ID=<GitHub Client ID>
GITHUB_OAUTH_APPLICATION_SECRET=<Client secret you generated above>
GITHUB_WEBHOOK_SECRET=<Webhook Secret you generated above>
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
<Contents of the private key GitHub generated for you>
<Please note the formatting must match precisely>
<NO line break at start, YES line break at end>
-----END RSA PRIVATE KEY-----
"
```

You can now start the app by running

```shell
make serve
```

And access it at `http://localhost:8000` or `https://my-cla-bot.ngrok.io`.
