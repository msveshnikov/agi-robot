# Docker Compose Deployment Guide - robot.mvpgen.com

This guide covers deploying the AGI Robot web application using Docker Compose to your VPS at robot.mvpgen.com.

## Prerequisites

### VPS Requirements
- Ubuntu 20.04+ or Debian 11+
- Docker 20.10+ installed
- Docker Compose V2 installed
- SSH access configured
- Domain pointing to VPS: robot.mvpgen.com

### GitHub Secrets

Configure these secrets in your GitHub repository (Settings → Secrets and Variables → Actions):

- `VPS_HOST`: robot.mvpgen.com
- `VPS_USERNAME`: Your SSH username
- `VPS_SSH_KEY`: Private SSH key for authentication

## Initial VPS Setup

### 1. Install Docker & Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose V2 (if not included)
sudo apt install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

### 2. Create Application Directory

```bash
sudo mkdir -p /var/www/agi-robot
sudo chown -R $USER:$USER /var/www/agi-robot
cd /var/www/agi-robot
```

### 3. Initial Configuration

The `docker-compose.yml` and Dockerfiles will be deployed automatically via GitHub Actions.

## Docker Compose Architecture

### Services

**1. MongoDB** (`mongodb`)
- Image: `mongo:6.0`
- Port: Internal 27017 (not exposed)
- Volume: `mongodb_data` for persistence
- Health check: MongoDB ping

**2. Backend** (`backend`)
- Built from `web/backend/Dockerfile`
- Port: 3000 (exposed)
- Environment: Production settings
- Depends on: MongoDB (healthy)
- Health check: `/api/health` endpoint

**3. Frontend** (`frontend`)
- Built from `web/Dockerfile` (multi-stage with Nginx)
- Port: 80 (exposed)
- Serves: React static build
- Depends on: Backend

### Network

All services communicate via `agi-robot-network` bridge network.

### Volumes

- `mongodb_data`: Persistent MongoDB storage

## Deployment

### Automated Deployment (GitHub Actions)

Push changes to the `main` branch:

```bash
git add .
git commit -m "Update application"
git push origin main
```

The GitHub Actions workflow will:
1. Copy files to VPS via SCP
2. Build Docker images on VPS
3. Stop old containers
4. Start new containers with `docker-compose up -d`
5. Verify deployment health

### Manual Deployment

If you prefer manual deployment:

```bash
# On local machine - commit and push
git add .
git commit -m "Deploy updates"
git push origin main

# Or manually copy files
scp -r web user@robot.mvpgen.com:/var/www/agi-robot/

# On VPS
cd /var/www/agi-robot
docker-compose build
docker-compose up -d
```

## Managing Services

### Start All Services

```bash
cd /var/www/agi-robot
docker-compose up -d
```

### Stop All Services

```bash
docker-compose down
```

### Restart Services

```bash
docker-compose restart
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### Check Status

```bash
docker-compose ps
```

### Rebuild Containers

```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Rebuild all
docker-compose build --no-cache
docker-compose up -d
```

## Environment Variables

Environment variables are configured in `docker-compose.yml`:

```yaml
environment:
  - NODE_ENV=production
  - MONGODB_URI=mongodb://mongodb:27017/agi-robot
  - PORT=3000
  - CORS_ORIGIN=https://robot.mvpgen.com
  - PYTHON_MEDIA_SERVICE_URL=http://host.docker.internal:5000
```

To use a separate `.env` file:

```bash
cd /var/www/agi-robot/backend
cp .env.production .env
# Edit as needed
```

Then update `docker-compose.yml`:
```yaml
backend:
  env_file:
    - ./backend/.env
```

## Reverse Proxy (Optional - NGINX on Host)

If you want HTTPS and better routing, install NGINX on the host:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Create `/etc/nginx/sites-available/agi-robot`:

```nginx
server {
    listen 80;
    server_name robot.mvpgen.com;

    # Frontend (Docker container on port 8080)
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API (Docker container on port 8300)
    location /api {
        proxy_pass http://localhost:8300;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Socket.IO WebSocket
    location /socket.io {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable and get SSL:
```bash
sudo ln -s /etc/nginx/sites-available/agi-robot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d robot.mvpgen.com
```

## Monitoring & Maintenance

### View Container Stats

```bash
docker stats
```

### Clean Up Unused Resources

```bash
# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Remove everything unused
docker system prune -af
```

### Backup MongoDB

```bash
# Create backup directory
mkdir -p /backup/mongodb

# Backup MongoDB from container
docker-compose exec mongodb mongodump --out /data/backup/$(date +%Y%m%d)

# Copy from container to host
docker cp agi-robot-mongodb:/data/backup /backup/mongodb/
```

### Restore MongoDB

```bash
# Copy backup to container
docker cp /backup/mongodb/20260206 agi-robot-mongodb:/data/restore/

# Restore
docker-compose exec mongodb mongorestore /data/restore/20260206
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Check if port is already in use
sudo lsof -i :3000
sudo lsof -i :80

# Rebuild without cache
docker-compose build --no-cache
docker-compose up -d
```

### MongoDB Connection Issues

```bash
# Check if MongoDB is healthy
docker-compose ps

# Access MongoDB shell
docker-compose exec mongodb mongosh

# Check backend can reach MongoDB
docker-compose exec backend ping mongodb
```

### Frontend Not Loading

```bash
# Check Nginx logs in container
docker-compose logs frontend

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Update Application Code

```bash
cd /var/www/agi-robot
git pull origin main  # If using git
docker-compose build
docker-compose up -d
```

## Security Recommendations

1. **Firewall**: Use `ufw` to restrict ports
   ```bash
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable
   ```

2. **Don't expose MongoDB port**: Keep it internal to Docker network

3. **Use SSL**: Install Let's Encrypt certificate with Certbot

4. **Regular Updates**: Keep Docker and images updated
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

5. **Secrets Management**: Never commit `.env` files to Git

## Production Checklist

- [ ] Docker & Docker Compose installed on VPS
- [ ] Application deployed to `/var/www/agi-robot`
- [ ] GitHub secrets configured (VPS_HOST, VPS_USERNAME, VPS_SSH_KEY)
- [ ] DNS A record for robot.mvpgen.com pointing to VPS IP
- [ ] Docker containers running (`docker-compose ps`)
- [ ] Backend health check passing (`curl http://localhost:3000/api/health`)
- [ ] Frontend accessible via browser
- [ ] (Optional) NGINX reverse proxy configured for HTTPS
- [ ] (Optional) SSL certificate installed via Certbot
- [ ] Firewall configured (ufw)
- [ ] MongoDB backups scheduled

## Quick Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart backend

# Rebuild and restart
docker-compose build && docker-compose up -d

# Check health
docker-compose ps
curl http://localhost:3000/api/health

# Clean up
docker system prune -af

# Backup MongoDB
docker-compose exec mongodb mongodump --out /data/backup/$(date +%Y%m%d)
```

## Verification

After deployment, verify:

1. **Containers Running**: `docker-compose ps` shows all 3 services as "Up"
2. **Backend Health**: `curl http://localhost:3000/api/health` returns `{"status":"ok"}`
3. **Frontend**: Visit http://robot.mvpgen.com (or https:// if SSL configured)
4. **WebSocket**: Check browser console for Socket.IO connection
5. **MongoDB**: `docker-compose exec mongodb mongosh` → `use agi-robot` → `db.robotstates.findOne()`

## Support

For issues:
- Check container logs: `docker-compose logs <service>`
- Check container health: `docker-compose ps`
- Inspect container: `docker-compose exec <service> sh`
- View Docker events: `docker events`
