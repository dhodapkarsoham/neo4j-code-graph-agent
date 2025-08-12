# Deployment Guide

This guide covers different deployment options for the MCP Code Graph Agent.

## 🐳 Docker Deployment

### Option 1: Using Docker Compose (Recommended)

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8000
   
   CMD ["python", "main.py"]
   ```

2. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     mcp-agent:
       build: .
       ports:
         - "8000:8000"
       environment:
         - NEO4J_URI=${NEO4J_URI}
         - NEO4J_USER=${NEO4J_USER}
         - NEO4J_PASSWORD=${NEO4J_PASSWORD}
         - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
         - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
         - AZURE_OPENAI_DEPLOYMENT_NAME=${AZURE_OPENAI_DEPLOYMENT_NAME}
       volumes:
         - ./tools.json:/app/tools.json
       restart: unless-stopped
   ```

3. **Deploy**
   ```bash
   docker-compose up -d
   ```

### Option 2: Direct Docker

```bash
# Build image
docker build -t mcp-code-graph-agent .

# Run container
docker run -d \
  --name mcp-agent \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/tools.json:/app/tools.json \
  mcp-code-graph-agent
```

## ☁️ Cloud Deployment

### Azure App Service

1. **Create Azure App Service**
   ```bash
   az group create --name mcp-agent-rg --location eastus
   az appservice plan create --name mcp-agent-plan --resource-group mcp-agent-rg --sku B1
   az webapp create --name mcp-agent --resource-group mcp-agent-rg --plan mcp-agent-plan --runtime "PYTHON|3.11"
   ```

2. **Configure Environment Variables**
   ```bash
   az webapp config appsettings set --name mcp-agent --resource-group mcp-agent-rg --settings \
     NEO4J_URI="your-neo4j-uri" \
     NEO4J_USER="your-neo4j-user" \
     NEO4J_PASSWORD="your-neo4j-password" \
     AZURE_OPENAI_API_KEY="your-api-key" \
     AZURE_OPENAI_ENDPOINT="your-endpoint" \
     AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment"
   ```

3. **Deploy**
   ```bash
   az webapp deployment source config-zip --resource-group mcp-agent-rg --name mcp-agent --src app.zip
   ```

### AWS Elastic Beanstalk

1. **Create requirements.txt** (already exists)
2. **Create Procfile**
   ```
   web: python main.py
   ```

3. **Deploy using EB CLI**
   ```bash
   eb init mcp-agent --platform python-3.11
   eb create mcp-agent-env
   eb deploy
   ```

### Google Cloud Run

1. **Create Dockerfile** (see above)
2. **Deploy**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/mcp-agent
   gcloud run deploy mcp-agent \
     --image gcr.io/PROJECT_ID/mcp-agent \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

## 🏠 Local Production Setup

### Using Systemd (Linux)

1. **Create service file** `/etc/systemd/system/mcp-agent.service`
   ```ini
   [Unit]
   Description=MCP Code Graph Agent
   After=network.target
   
   [Service]
   Type=simple
   User=mcp-agent
   WorkingDirectory=/opt/mcp-agent
   Environment=PATH=/opt/mcp-agent/venv/bin
   ExecStart=/opt/mcp-agent/venv/bin/python main.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and start service**
   ```bash
   sudo systemctl enable mcp-agent
   sudo systemctl start mcp-agent
   ```

### Using PM2 (Node.js Process Manager)

1. **Install PM2**
   ```bash
   npm install -g pm2
   ```

2. **Create ecosystem.config.js**
   ```javascript
   module.exports = {
     apps: [{
       name: 'mcp-agent',
       script: 'main.py',
       interpreter: './venv/bin/python',
       instances: 1,
       autorestart: true,
       watch: false,
       max_memory_restart: '1G',
       env: {
         NODE_ENV: 'production'
       }
     }]
   }
   ```

3. **Start with PM2**
   ```bash
   pm2 start ecosystem.config.js
   pm2 save
   pm2 startup
   ```

## 🔒 Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use secure secret management services
- Rotate API keys regularly

### Network Security
- Use HTTPS in production
- Configure firewall rules
- Implement rate limiting

### Database Security
- Use strong Neo4j passwords
- Enable SSL/TLS connections
- Restrict database access

## 📊 Monitoring

### Health Checks
```bash
# Check application health
curl http://localhost:8000/api/health

# Monitor logs
tail -f /var/log/mcp-agent.log
```

### Metrics
Consider adding monitoring with:
- Prometheus + Grafana
- Azure Application Insights
- AWS CloudWatch
- Google Cloud Monitoring

## 🔄 Updates and Maintenance

### Rolling Updates
```bash
# Stop service
sudo systemctl stop mcp-agent

# Backup tools.json
cp tools.json tools.json.backup

# Update code
git pull origin main

# Restart service
sudo systemctl start mcp-agent
```

### Backup Strategy
- Backup `tools.json` regularly
- Export Neo4j data periodically
- Store configuration securely

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. **Permission denied**
   ```bash
   chmod +x start.py
   chown -R user:group /path/to/app
   ```

3. **Memory issues**
   - Increase system memory
   - Optimize Neo4j queries
   - Add caching layer

### Log Analysis
```bash
# View application logs
journalctl -u mcp-agent -f

# Check system resources
htop
df -h
free -h
```

## 📞 Support

For deployment issues:
1. Check the troubleshooting section
2. Review application logs
3. Verify environment configuration
4. Create an issue in the repository
