# Production Readiness Checklist

## Current Status

The application is a validated local proof of concept, not yet a production deployment.

Current validated functionality:

- [x] 50 NSE live symbols
- [x] 10 BSE live symbols
- [x] TrueData WebSocket subscription
- [x] Trade ingestion
- [x] Bid/Ask persistence
- [x] BSE `bidaskL2` handling
- [x] PostgreSQL persistence
- [x] FastAPI live-data APIs
- [x] IST market-session logic
- [x] 08:45 pre-market session
- [x] React NSE/BSE dashboard
- [x] ALL/NSE/BSE frontend filtering

## Application

- [ ] Production authentication
- [ ] Authorization
- [ ] Restrict CORS
- [ ] Rate limiting
- [ ] Request validation review
- [ ] Database migrations
- [ ] Automated CI tests
- [ ] Structured logging
- [ ] Production environment configuration

## TrueData Collector

- [ ] Automatic WebSocket reconnect
- [ ] Exponential backoff
- [ ] Subscription recovery
- [ ] Collector health monitoring
- [ ] Process supervision
- [ ] Ingestion metrics
- [ ] Failure alerts

The reconnect item was intentionally deferred during the current development phase.

## PostgreSQL

- [ ] Production database configuration
- [ ] Connection pooling review
- [ ] Automated backups
- [ ] Restore testing
- [ ] Tick retention policy
- [ ] Partitioning evaluation
- [ ] Query optimization
- [ ] Storage monitoring
- [ ] Historical-data ingestion strategy for BSE

## Security

- [ ] Secret manager
- [ ] HTTPS
- [ ] Database least privilege
- [ ] Credential rotation
- [ ] Verify no secrets in Git history
- [ ] Verify no secrets in logs
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
- [ ] Exchange-specific ingestion metrics

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

## Recommended Next Phase

1. Automatic reconnect with exponential backoff.
2. Subscription recovery after reconnect.
3. Collector health endpoint/heartbeat monitoring.
4. Structured logging and metrics.
5. Historical BSE data ingestion and validation.
6. Production database backup/retention strategy.
7. CI-based automated testing.
