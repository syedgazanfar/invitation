# Admin Guide - InviteMe Platform

## Admin Login Details

**Default Admin Account:**
- **Phone**: +919999999999
- **Username**: admin
- **Password**: Admin@123
- **Email**: admin@inviteme.in

**Admin Panel URL**: http://localhost:8000/admin

---

## How to Create Additional Admin Users

### Method 1: Using the Script (Windows)
```cmd
create-admin.bat
```

### Method 2: Using the Script (Mac/Linux)
```bash
chmod +x create-admin.sh
./create-admin.sh
```

### Method 3: Manual Creation
```bash
docker-compose exec backend python src/manage.py createsuperuser
```

---

## Admin Panel Navigation

### 1. Dashboard
- View all system statistics
- Quick links to manage users, orders, and invitations

### 2. Managing Users (ACCOUNTS > Users)
**What you can do:**
- View all registered users
- Block/Unblock users
- Verify user phone numbers
- View user activity logs

**Important Actions:**
- **Block User**: If a user is violating terms
- **Unblock User**: Restore access to blocked users

### 3. Managing Plans (PLANS > Plans)
**Default Plans:**
| Plan | Price | Regular Links | Test Links |
|------|-------|---------------|------------|
| Basic | ₹150 | 100 | 5 |
| Premium | ₹350 | 150 | 5 |
| Luxury | ₹500 | 200 | 5 |

**What you can do:**
- Edit plan prices
- Change link limits
- Update plan features

### 4. Managing Templates (PLANS > Templates)
**What you can do:**
- Add new invitation templates
- Edit template descriptions
- Change template categories
- Update animation types

### 5. Managing Orders (INVITATIONS > Orders)
**Order Status Flow:**
```
DRAFT → PENDING_PAYMENT → PENDING_APPROVAL → APPROVED → ACTIVE
```

**What you can do:**
- View all orders
- Approve/Reject orders
- Update payment status
- Grant additional links
- Add admin notes

**How to Approve an Order:**
1. Go to INVITATIONS > Orders
2. Click on the order
3. Change "Status" to "APPROVED"
4. Set "Payment status" to "RECEIVED"
5. Save the changes

**How to Grant Additional Links:**
1. Open the order
2. Update "Granted regular links" or "Granted test links"
3. Add a note explaining why
4. Save

### 6. Managing Invitations (INVITATIONS > Invitations)
**What you can do:**
- View all created invitations
- Activate/Deactivate invitations
- Extend link validity
- View invitation statistics

**How to Extend Link Validity:**
1. Open the invitation
2. Update "Link expires at" date
3. Check "Is active"
4. Save

### 7. Managing Guests (INVITATIONS > Guests)
**What you can do:**
- View all registered guests
- See device information
- Track guest activity

### 8. Viewing Statistics
**Available Reports:**
- User registrations
- Order statistics
- Revenue reports
- Invitation views
- Guest registrations

---

## Common Admin Workflows

### Workflow 1: Processing a New Order

1. **User creates an order** → Status: PENDING_PAYMENT
2. **User makes payment** (via Razorpay or manual)
3. **Admin receives notification** (check orders list)
4. **Admin verifies payment**:
   - Open the order
   - Set Payment status: RECEIVED
   - Set Status: APPROVED
   - Add admin notes if needed
   - Save
5. **User can now create invitation**

### Workflow 2: Handling a Demo Request

1. User asks for demo links
2. Admin finds user's order
3. Grant 2-3 test links:
   - Open order
   - Update "Granted test links" (+3)
   - Add note: "Demo links granted"
   - Save
4. User can test the platform

### Workflow 3: Blocking a Fraudulent User

1. Go to ACCOUNTS > Users
2. Find the user
3. Check "Is blocked"
4. Add block reason in notes
5. Save
6. User can no longer login

---

## Admin API Endpoints

As an admin, you can also use these API endpoints:

### Get Dashboard Stats
```
GET http://localhost:8000/api/v1/admin-dashboard/dashboard/
Headers: Authorization: Bearer <your-token>
```

### List All Orders
```
GET http://localhost:8000/api/v1/admin-dashboard/orders/
Headers: Authorization: Bearer <your-token>
```

### Approve Order
```
POST http://localhost:8000/api/v1/admin-dashboard/orders/<id>/approve/
Headers: Authorization: Bearer <your-token>
Body: { "notes": "Payment verified" }
```

### Grant Additional Links
```
POST http://localhost:8000/api/v1/admin-dashboard/orders/<id>/grant-links/
Headers: Authorization: Bearer <your-token>
Body: { "regular_links": 5, "test_links": 2 }
```

---

## How to Get Admin Access Token

1. Login via API:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919999999999", "password": "Admin@123"}'
```

2. Response will contain:
```json
{
  "success": true,
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": { ... }
  }
}
```

3. Use the `access` token in Authorization header:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Admin Panel Customization

### Changing Company Details
Edit in Django Admin:
- **Admin Settings** > Admin Company Name
- **Admin Settings** > Support Email

### Payment Methods
Supported methods:
- Razorpay (automatic)
- UPI (manual verification)
- Bank Transfer (manual verification)
- Cash (manual verification)

---

## Troubleshooting

### Can't Access Admin Panel
1. Check if backend is running:
   ```bash
   docker-compose ps
   ```
2. Try creating admin again:
   ```bash
   docker-compose exec backend python src/manage.py createsuperuser
   ```

### Forgot Admin Password
1. Reset via command:
   ```bash
   docker-compose exec backend python src/manage.py shell -c "
   from apps.accounts.models import User
   u = User.objects.get(phone='+919999999999')
   u.set_password('NewPassword123')
   u.save()
   print('Password updated!')
   "
   ```

### Database Issues
1. Reset database:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

---

## Security Best Practices

1. **Change Default Password**: Update admin password immediately
2. **Regular Backups**: Backup database daily
3. **Monitor Logs**: Check logs for suspicious activity
4. **Limit Access**: Only give admin access to trusted users
5. **Update Regularly**: Keep Django and dependencies updated

---

## Contact & Support

**Platform**: InviteMe Digital Invitation Platform
**Support Email**: admin@inviteme.in
**Documentation**: See PROJECT_COMPLETION_SUMMARY.md

---

**Your Admin Dashboard is Ready!**
Access: http://localhost:8000/admin
