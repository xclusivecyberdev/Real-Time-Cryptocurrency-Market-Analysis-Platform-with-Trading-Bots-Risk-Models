# Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)
- 20GB disk space

### Step-by-Step Deployment

1. **Clone the Repository**
```bash
git clone <repository-url>
cd crypto-market-analysis-platform
```

2. **Configure Environment**
```bash
cp .env.example .env
```

Edit `.env` and set your configuration:
```env
# Required Settings
SECRET_KEY=<generate-secure-random-key>
ENCRYPTION_KEY=<generate-32-byte-base64-key>
DATABASE_URL=postgresql+asyncpg://crypto_user:crypto_pass@postgres:5432/crypto_platform

# Optional: Exchange API Keys (for live trading)
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret
```

3. **Generate Secure Keys**
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. **Start Services**
```bash
docker-compose up -d
```

5. **Verify Deployment**
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend

# Access services
curl http://localhost:8000/health
```

### Access Points

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Grafana**: http://localhost:3001 (admin/admin)
- **Flower (Celery)**: http://localhost:5555
- **Prometheus**: http://localhost:9090

## Production Deployment

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Build and Push Images**
```bash
# Build images
docker-compose build

# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag crypto-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/crypto-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/crypto-backend:latest
```

2. **Create RDS PostgreSQL Instance**
- Instance type: db.t3.medium or larger
- Enable automated backups
- Enable Multi-AZ for high availability

3. **Create ElastiCache Redis Cluster**
- Node type: cache.t3.medium
- Number of replicas: 2-3

4. **Deploy ECS Services**
- Use provided `infrastructure/aws/ecs-task-definition.json`
- Configure ALB (Application Load Balancer)
- Set up Auto Scaling

#### Using Kubernetes (EKS)

```bash
# Apply Kubernetes manifests
kubectl apply -f infrastructure/kubernetes/

# Verify deployment
kubectl get pods
kubectl get services
```

### Security Best Practices

1. **SSL/TLS Configuration**
```bash
# Generate SSL certificates
certbot certonly --standalone -d your-domain.com

# Update nginx configuration
cp infrastructure/nginx/nginx-ssl.conf infrastructure/nginx/nginx.conf
```

2. **Environment Variables**
- Never commit `.env` files
- Use AWS Secrets Manager or HashiCorp Vault in production
- Rotate keys regularly

3. **Database Security**
- Enable SSL for PostgreSQL connections
- Use strong passwords
- Implement connection pooling
- Regular backups

4. **Network Security**
- Configure VPC with private subnets
- Use security groups to restrict access
- Enable WAF (Web Application Firewall)

### Monitoring & Logging

1. **Prometheus + Grafana**
- Access Grafana at http://your-domain:3001
- Import dashboards from `infrastructure/monitoring/grafana/dashboards/`
- Set up alerts

2. **Centralized Logging**
```bash
# Configure Elasticsearch + Kibana (ELK Stack)
docker-compose -f docker-compose.elk.yml up -d
```

3. **Application Monitoring**
- Enable Sentry for error tracking
- Configure application performance monitoring (APM)

### Backup & Recovery

1. **Database Backup**
```bash
# Automated daily backups
0 2 * * * docker exec crypto_postgres pg_dump -U crypto_user crypto_platform > /backup/db_$(date +\%Y\%m\%d).sql
```

2. **Restore from Backup**
```bash
docker exec -i crypto_postgres psql -U crypto_user crypto_platform < /backup/db_20231201.sql
```

### Scaling

1. **Horizontal Scaling**
```bash
# Scale backend workers
docker-compose up -d --scale backend=3 --scale celery_worker=5
```

2. **Database Scaling**
- Read replicas for high-traffic scenarios
- Connection pooling with PgBouncer
- TimescaleDB compression for time-series data

3. **Load Balancing**
- Use nginx or AWS ALB
- Configure health checks
- Session affinity if needed

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify connection
docker exec -it crypto_postgres psql -U crypto_user -d crypto_platform
```

2. **High Memory Usage**
```bash
# Monitor resource usage
docker stats

# Adjust memory limits in docker-compose.yml
```

3. **WebSocket Connection Issues**
- Check firewall rules
- Verify CORS settings
- Enable sticky sessions on load balancer

### Performance Tuning

1. **Database Optimization**
```sql
-- Create indexes
CREATE INDEX idx_market_data_symbol_time ON market_data (symbol, time DESC);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM market_data WHERE symbol = 'BTC/USDT';
```

2. **Redis Optimization**
```bash
# Increase max memory
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

3. **Application Tuning**
- Adjust worker processes based on CPU cores
- Configure connection pool sizes
- Enable caching

## Maintenance

### Regular Tasks

1. **Weekly**
- Review logs for errors
- Check disk space
- Monitor API rate limits

2. **Monthly**
- Update dependencies
- Review and rotate secrets
- Optimize database

3. **Quarterly**
- Security audit
- Performance review
- Capacity planning

### Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build

# Rolling update
docker-compose up -d --no-deps --build backend
```

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: [docs/](../docs/)
- Email: support@cryptoplatform.com
