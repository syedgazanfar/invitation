#!/bin/bash

echo "Creating Admin User for InviteMe Platform"
echo "=========================================="
echo ""

# Default admin credentials
ADMIN_PHONE="+919999999999"
ADMIN_USER="admin"
ADMIN_PASS="Admin@123"

# Run Django shell command
docker-compose exec backend python src/manage.py shell << EOF
from apps.accounts.models import User

phone = "$ADMIN_PHONE"
username = "$ADMIN_USER"
password = "$ADMIN_PASS"

if not User.objects.filter(phone=phone).exists():
    User.objects.create_superuser(
        phone=phone,
        username=username,
        email='admin@inviteme.in',
        full_name='System Administrator',
        password=password
    )
    print('Admin user created successfully!')
else:
    user = User.objects.get(phone=phone)
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print('Admin user updated successfully!')

print('')
print('=== ADMIN LOGIN DETAILS ===')
print('Phone: ' + phone)
print('Username: ' + username)
print('Password: ' + password)
print('===========================')
EOF

echo ""
echo "Admin user setup complete!"
