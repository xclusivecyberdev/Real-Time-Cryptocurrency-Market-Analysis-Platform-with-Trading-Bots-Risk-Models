#!/bin/bash

# Setup script for Crypto Market Analysis Platform
echo "🚀 Setting up Crypto Market Analysis Platform..."

# Check prerequisites
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ Error: $1 is not installed"
        return 1
    else
        echo "✅ $1 is installed"
        return 0
    fi
}

echo "Checking prerequisites..."
check_command docker || exit 1
check_command docker-compose || exit 1
check_command python3 || exit 1

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env

    echo "🔐 Generating secure keys..."

    # Generate SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i.bak "s|your-secret-key-change-this-in-production|$SECRET_KEY|g" .env

    # Generate ENCRYPTION_KEY
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    sed -i.bak "s|your-32-byte-base64-encoded-encryption-key|$ENCRYPTION_KEY|g" .env

    rm .env.bak

    echo "✅ .env file created with secure keys"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p ml/models/saved
mkdir -p sample_data
mkdir -p infrastructure/nginx/ssl

# Create .gitkeep files
touch ml/models/saved/.gitkeep
touch logs/.gitkeep

# Pull Docker images
echo "🐳 Pulling Docker images..."
docker-compose pull

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose build

# Start services
echo "▶️  Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        echo "✅ Backend is healthy!"
        break
    fi
    echo "Waiting for backend... (attempt $((attempt + 1))/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Backend failed to start. Check logs:"
    echo "   docker-compose logs backend"
    exit 1
fi

# Show service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "✨ Setup complete! ✨"
echo ""
echo "Access the platform at:"
echo "  - Frontend:      http://localhost:3000"
echo "  - API Docs:      http://localhost:8000/docs"
echo "  - Grafana:       http://localhost:3001 (admin/admin)"
echo "  - Flower:        http://localhost:5555"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:8000/docs"
echo "  2. Create an account via /api/auth/register"
echo "  3. Start trading!"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: docker-compose down"
echo ""
