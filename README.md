Here's a refined version of your README with improved structure, clarity, and formatting:

---

# Contributor License Agreement (CLA) Bot  

A GitHub Application that manages Contributor License Agreement (CLA) signing for repositories where it's installed.

## Key Features  

- **Agreement Management**:  
  - Create and manage CLAs via Django Admin  
  - Markdown-formatted agreements  
  - "Write once" design to prevent modifications  
  - Compatibility marking between agreements to honor historical signatures  

- **User Experience**:  
  - Secure login to view pending agreements  
  - Access to signature history  
  - Email address management for past signatures  

- **Automated Workflow**:  
  - Monitors GitHub Pull Requests in real-time  
  - Validates CLA signatures for all contributors  
  - Provides clear status updates:  
    - Commit status indicators  
    - Automated PR comments with signing instructions  
    - Updates existing comments when signatures are completed  

## Development Setup  

### Technologies Used  
- Django  
- django-github-app  
- gidgethub  
- Docker & Docker Compose  
- GNU make  

### Prerequisites  

1. **GitHub Application Setup**:  
   - Create a new GitHub App with these settings:  
     - **Basic Information**:  
       - App name: `My CLA Bot` (customize as needed)  
       - Homepage URL: `https://my-cla-bot.ngrok.io`  
       - Callback URL: `https://my-cla-bot.ngrok.io/auth/gh/`  

     - **Webhook**:  
       - Active: ✓  
       - URL: `https://my-cla-bot.ngrok.io/gh/`  
       - Secret: Generate with:  
         ```shell
         python3 -c 'import secrets; print(secrets.token_urlsafe())'
         ```  

     - **Permissions**:  
       - Repository:  
         - Commit statuses: Read & write  
         - Pull requests: Read & write  
       - Organization: Members: Read-only  
       - Account: Email addresses: Read-only  

     - **Subscribe to Events**:  
       - Pull request: ✓  

   - Generate and securely store:  
     - Client secret  
     - Private key  

2. **Local Environment Setup**:  
   - Use ngrok for webhook tunneling:  
     ```shell
     ngrok http 8000 -subdomain my-cla-bot
     ```  

   - Create `.env` file with:  
     ```shell
     DJANGO_ALLOWED_HOSTS=localhost,my-cla-bot.ngrok.io
     DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://my-cla-bot.ngrok.io
     DJANGO_SITE_URL=https://my-cla-bot.ngrok.io/
     GITHUB_APP_ID=<GitHub App ID>
     GITHUB_CLIENT_ID=<GitHub Client ID>
     GITHUB_NAME="My CLA Bot"
     GITHUB_OAUTH_APPLICATION_ID=<GitHub Client ID>
     GITHUB_OAUTH_APPLICATION_SECRET=<Client secret>
     GITHUB_WEBHOOK_SECRET=<Webhook Secret>
     GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
     <Private key contents>
     <Maintain exact formatting>
     <No leading line break>
     <Trailing line break required>
     -----END RSA PRIVATE KEY-----
     "
     ```  

### Running the Application  

```shell
make serve
```  

Access at:  
- Local: `http://localhost:8000`  
- Public: `https://my-cla-bot.ngrok.io`  

## Usage  

Once installed:  
1. The bot automatically monitors PRs  
2. Contributors receive clear instructions for unsigned CLAs  
3. Maintainers see real-time signature status  

---
