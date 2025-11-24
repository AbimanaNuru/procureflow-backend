#!/bin/bash

# ProcureFlow Backend - Quick Test Script

echo "🧪 Testing ProcureFlow Backend..."
echo ""

# Test 1: Check if containers are running
echo "1️⃣ Checking Docker containers..."
docker-compose ps

echo ""
echo "2️⃣ Testing API endpoint..."
curl -s http://localhost:8000/admin/ | grep -q "Django" && echo "✅ Django admin is accessible" || echo "❌ Admin not accessible"

echo ""
echo "3️⃣ Testing database connection..."
docker-compose exec -T web python manage.py showmigrations | head -5

echo ""
echo "4️⃣ Checking logs for errors..."
docker-compose logs web --tail=10

echo ""
echo "✅ Setup complete! Access the application at:"
echo "   - API: http://localhost:8000"
echo "   - Admin: http://localhost:8000/admin"
echo "   - Login: admin / admin123"
echo ""
echo "📚 Next steps:"
echo "   1. Login to admin panel"
echo "   2. Create roles (staff, manager, finance)"
echo "   3. Create permissions (create_request, approve_request, view_request)"
echo "   4. Assign permissions to roles"
echo "   5. Create users with roles"
echo ""
