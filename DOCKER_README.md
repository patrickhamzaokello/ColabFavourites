# MW Music Recommender - Docker Setup

Complete Docker configuration for the MW Music Recommender API with MySQL database, Redis cache, and optional Nginx reverse proxy.

## Quick Start

### 1. Clone and Setup Environment

```bash
git clone <repository>
cd ColabFavourites

# Copy environment configuration
cp .env.docker .env

# Edit .env with your settings (optional)
nano .env
```

### 2. Build and Run with Docker Compose

```bash
# Production setup (with MySQL + Redis + API)
docker-compose up -d

# Development setup (with hot reload)
docker-compose -f docker-compose.dev.yml up -d

# With Nginx reverse proxy
docker-compose --profile production up -d
```

### 3. Access the API

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **With Nginx**: http://localhost (port 80)

## Docker Services

### Core Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| **api** | mw_recommender_api | 8000 | FastAPI application |
| **mysql** | mw_recommender_db | 3306 | MySQL database |
| **redis** | mw_recommender_redis | 6379 | Redis cache |
| **nginx** | mw_recommender_nginx | 80/443 | Reverse proxy (optional) |

### Development Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| **api** | mw_recommender_api_dev | 8001 | API with hot reload |
| **mysql** | mw_recommender_db_dev | 3307 | Dev database |
| **redis** | mw_recommender_redis_dev | 6380 | Dev cache |

## Configuration Files

### Environment Files
- `.env.docker` - Production environment template
- `.env` - Your actual environment (copy from .env.docker)

### Docker Files
- `Dockerfile` - Production API container
- `Dockerfile.dev` - Development API container with hot reload
- `docker-compose.yml` - Production stack
- `docker-compose.dev.yml` - Development stack
- `.dockerignore` - Build context optimization

### Database
- `init.sql` - Database initialization script
- Creates tables, indexes, views, and stored procedures

### Nginx
- `nginx/nginx.conf` - Reverse proxy configuration
- Includes rate limiting, gzip, security headers

## Environment Variables

### Database Configuration
```bash
DB_HOST=mysql                    # Database host
DB_USER=mwonya_user             # Database user
DB_PASSWORD=mwonya_password     # Database password
DB_NAME=mwonya                  # Database name
MYSQL_ROOT_PASSWORD=rootpassword # MySQL root password
```

### API Configuration
```bash
DEBUG=false                     # Debug mode
API_PORT=8000                   # API port
LOG_LEVEL=INFO                  # Logging level
ENVIRONMENT=production          # Environment
```

### Performance
```bash
REDIS_URL=redis://redis:6379/0  # Redis connection
CACHE_TTL=3600                  # Cache TTL seconds
SVD_COMPONENTS=20               # Matrix factorization components
```

## Commands

### Production Deployment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Scale API instances
docker-compose up -d --scale api=3

# Stop services
docker-compose down

# Rebuild and restart
docker-compose down && docker-compose up -d --build
```

### Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View API logs with hot reload
docker-compose -f docker-compose.dev.yml logs -f api

# Restart just the API
docker-compose -f docker-compose.dev.yml restart api

# Stop development environment
docker-compose -f docker-compose.dev.yml down
```

### Database Management
```bash
# Access MySQL shell
docker exec -it mw_recommender_db mysql -u root -p

# Import existing data
docker exec -i mw_recommender_db mysql -u root -p mwonya < your_data.sql

# Backup database
docker exec mw_recommender_db mysqldump -u root -p mwonya > backup.sql

# View database logs
docker-compose logs mysql
```

### Monitoring and Debugging
```bash
# Check service health
docker-compose ps

# View all logs
docker-compose logs

# Execute commands in API container
docker exec -it mw_recommender_api bash

# Check resource usage
docker stats

# Inspect container configuration
docker inspect mw_recommender_api
```

## Data Persistence

### Volumes
- `mysql_data` - MySQL database files
- `redis_data` - Redis persistence
- `./logs` - Application logs (mounted)

### Backup Strategy
```bash
# Backup MySQL data volume
docker run --rm -v mw_recommender_mysql_data:/source -v $(pwd):/backup alpine tar czf /backup/mysql_backup.tar.gz -C /source .

# Restore MySQL data volume
docker run --rm -v mw_recommender_mysql_data:/target -v $(pwd):/backup alpine tar xzf /backup/mysql_backup.tar.gz -C /target
```

## Security Considerations

### Production Security
1. **Change default passwords** in .env file
2. **Use secrets management** for production
3. **Enable SSL/TLS** in Nginx configuration
4. **Configure firewall** rules
5. **Update API_KEY** in environment

### SSL Setup
```bash
# Generate self-signed certificate (development)
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# Uncomment SSL server block in nginx.conf
```

## Performance Tuning

### Production Optimizations
```bash
# Increase MySQL performance
docker-compose exec mysql mysql -u root -p -e "
SET GLOBAL innodb_buffer_pool_size = 1073741824;
SET GLOBAL max_connections = 200;
"

# Monitor Redis memory usage
docker-compose exec redis redis-cli info memory
```

### Scaling
```bash
# Scale API horizontally
docker-compose up -d --scale api=3

# Use external load balancer
# Configure nginx upstream with multiple API instances
```

## Troubleshooting

### Common Issues

1. **API won't start**
   ```bash
   # Check database connection
   docker-compose logs mysql
   docker-compose logs api
   ```

2. **Database connection failed**
   ```bash
   # Verify MySQL is ready
   docker-compose exec mysql mysqladmin ping -h localhost
   ```

3. **Port conflicts**
   ```bash
   # Change ports in .env file
   API_PORT=8001
   DB_PORT=3307
   ```

4. **Permission issues**
   ```bash
   # Fix volume permissions
   sudo chown -R $USER:$USER logs/
   ```

### Health Checks
```bash
# Check all service health
curl http://localhost:8000/health

# Check database connectivity
docker-compose exec api curl http://localhost:8000/health

# Check Nginx proxy
curl http://localhost/health
```

## Development Workflow

### Hot Reload Development
```bash
# Start development stack
docker-compose -f docker-compose.dev.yml up -d

# Code changes automatically reload the API
# Database persists between restarts
# Redis cache available for testing
```

### Testing
```bash
# Run tests in container
docker-compose exec api pytest tests/

# Test API endpoints
curl -X POST "http://localhost:8000/recommendations/similar-songs" \
  -H "Content-Type: application/json" \
  -d '{"song_id": 1787, "k": 5}'
```

## Migration from Jupyter Notebook

The Docker setup automatically:
1. Recreates the database schema
2. Loads existing data if available
3. Initializes recommendation engine
4. Provides REST API endpoints

Your existing Jupyter notebook functionality is now available as REST endpoints:
- Collaborative filtering → `/recommendations/similar-songs`
- Content-based → `/recommendations/content-based`
- Popular songs → `/recommendations/popular`

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify health: `curl localhost:8000/health`
3. Review configuration in `.env`
4. Check Docker resource limits