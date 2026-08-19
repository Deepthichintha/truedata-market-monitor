# Production Readiness Checklist

## Application

- [ ] Add production authentication
- [ ] Add authorization
- [ ] Restrict CORS
- [ ] Add rate limiting
- [ ] Add request validation
- [ ] Add database migrations
- [ ] Add automated CI tests
- [ ] Add structured logging
- [ ] Configure production environment variables

## TrueData Collector

- [ ] Automatic WebSocket reconnect
- [ ] Exponential backoff
- [ ] Subscription recovery
- [ ] Collector health monitoring
- [ ] Process supervision
- [ ] Ingestion metrics
- [ ] Failure alerts

## PostgreSQL

- [ ] Production database configuration
- [ ] Connection pooling
- [ ] Automated backups
- [ ] Restore testing
- [ ] Retention policy
- [ ] Partitioning evaluation
- [ ] Query optimization
- [ ] Storage monitoring

## Security

- [ ] Secret manager
- [ ] HTTPS
- [ ] Database least privilege
- [ ] Credential rotation
- [ ] No secrets in Git history
- [ ] No secrets in logs
- [ ] API authentication
- [ ] API authorization

## Monitoring

- [ ] API latency
- [ ] API error rate
- [ ] Collector health
- [ ] WebSocket status
- [ ] Tick ingestion rate
- [ ] Database health
- [ ] Storage usage
- [ ] Stale-feed alerts

## Deployment

- [ ] Containerize backend
- [ ] Containerize collector
- [ ] Deploy frontend
- [ ] Configure load balancer
- [ ] Configure HTTPS
- [ ] Configure health checks
- [ ] Configure restart policies
- [ ] Document rollback procedure

## Disaster Recovery

- [ ] Database backups
- [ ] Backup retention
- [ ] Restore procedure
- [ ] Recovery Time Objective (RTO)
- [ ] Recovery Point Objective (RPO)
- [ ] Credential recovery process
