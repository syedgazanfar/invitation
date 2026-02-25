@echo off
echo Creating Admin User for InviteMe Platform
echo ==========================================
echo.

REM Default admin credentials
set ADMIN_PHONE=+919999999999
set ADMIN_USER=admin
set ADMIN_PASS=Admin@123

REM Run Django createsuperuser command
docker-compose exec backend python src/manage.py shell -c "
from apps.accounts.models import User
import os

phone = '%ADMIN_PHONE%'
username = '%ADMIN_USER%'
password = '%ADMIN_PASS%'

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
"

echo.
echo Admin user setup complete!
pause
