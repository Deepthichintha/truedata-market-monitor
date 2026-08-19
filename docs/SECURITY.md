# TrueData Market Monitor - Security Guidelines

## 1. Sensitive Information

Treat the following as secrets:

- `TRUEDATA_USERNAME`
- `TRUEDATA_PASSWORD`
- `DATABASE_URL` when it contains credentials
- API tokens
- Database passwords
- Authorization headers

## 2. Local Configuration

Use `.env` for local secrets and `.env.example` as the safe configuration template.

Never commit the real `.env` file.

## 3. Repository Checks

Before committing, inspect the repository for accidental secrets:

```bash
git grep -n -I -E 'TRUEDATA_USERNAME=|TRUEDATA_PASSWORD=|DATABASE_URL=|Bearer '
```

If a credential has been committed, rotate it immediately and remove exposed secrets from repository history as appropriate.

## 4. Database Security

Production recommendations:

- Dedicated least-privilege database user
- Strong credential policy
- TLS for remote connections
- Private database networking
- No unnecessary public exposure
- Automated backups
- Credential rotation

## 5. API Security

The current project is a local proof of concept and should not be considered production-secured by default.

Production should add:

- Authentication
- Authorization
- HTTPS
- Restricted CORS
- Rate limiting
- Input validation
- Audit logging

## 6. Frontend Security

Never expose TrueData credentials, database credentials, or private API keys in browser-side code.

Only intentionally public frontend configuration may be exposed to users.

## 7. Logging

Never log passwords, access tokens, authorization headers, cookies, or database credentials.

## 8. Production Secret Management

Use a managed secret solution such as:

- AWS Secrets Manager
- Azure Key Vault
- GCP Secret Manager
- Kubernetes Secrets backed by an external secret manager
