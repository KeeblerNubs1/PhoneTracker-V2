# Architecture

## Control plane
The desktop console communicates with the FastAPI service.

## Device plane
Each enrolled Android device has a unique device ID and credential. Location reporting is authenticated with that credential.

## Security controls
- Authentication
- Least privilege
- Audit events
- Explicit enrollment
- Visible foreground tracking
- TLS in production
- Credential rotation
- Database encryption/secure hosting
- Administrative MFA

## Suggested production expansion
- PostgreSQL
- Redis job queue
- OIDC administrator login
- Role-based access control
- Prometheus metrics
- OpenTelemetry
- SIEM export
- Signed Android builds
- Device attestation
- Geofencing
- Compliance rules
- Tamper-evident audit storage
