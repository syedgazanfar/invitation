"""
Load Testing with Locust
Run: locust -f locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between
import random


class PublicUser(HttpUser):
    """Simulates a guest viewing an invitation"""
    wait_time = between(1, 5)
    
    def on_start(self):
        # List of sample invitation slugs
        self.invitation_slugs = [
            'abc123def4',
            'xyz789ghi0',
            'test123456',
        ]
    
    @task(3)
    def view_invitation(self):
        """View an invitation"""
        slug = random.choice(self.invitation_slugs)
        self.client.get(f"/api/invite/{slug}/")
    
    @task(1)
    def register_guest(self):
        """Register as a guest"""
        slug = random.choice(self.invitation_slugs)
        fingerprint = f"test_fp_{self.user_id}_{random.randint(1000, 9999)}"
        
        self.client.post(
            f"/api/invite/{slug}/register/",
            json={
                "name": f"Guest {random.randint(1, 1000)}",
                "fingerprint": fingerprint,
                "screen_resolution": "1920x1080",
                "timezone_offset": "-330",
                "languages": "en-IN",
            }
        )


class AuthenticatedUser(HttpUser):
    """Simulates a logged-in user"""
    wait_time = between(5, 15)
    
    def on_start(self):
        self.login()
    
    def login(self):
        """Login and get token"""
        response = self.client.post("/api/v1/auth/login/", json={
            "phone": "+919876543210",
            "password": "testpass123"
        })
        
        if response.status_code == 200:
            self.token = response.json().get("data", {}).get("access")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(5)
    def get_dashboard(self):
        """Load dashboard data"""
        self.client.get("/api/v1/invitations/orders/", headers=self.headers)
        self.client.get("/api/v1/invitations/", headers=self.headers)
    
    @task(2)
    def get_plans(self):
        """Browse plans"""
        self.client.get("/api/v1/plans/")
    
    @task(2)
    def get_templates(self):
        """Browse templates"""
        self.client.get("/api/v1/plans/templates/all")
    
    @task(1)
    def create_order(self):
        """Create an order"""
        self.client.post(
            "/api/v1/invitations/orders/create/",
            headers=self.headers,
            json={
                "plan_code": "BASIC",
                "event_type": "WEDDING",
                "event_type_name": "Wedding"
            }
        )


class AdminUser(HttpUser):
    """Simulates an admin user"""
    wait_time = between(10, 30)
    weight = 1  # Less frequent than regular users
    
    def on_start(self):
        self.login()
    
    def login(self):
        response = self.client.post("/api/v1/auth/login/", json={
            "phone": "+919999999999",
            "password": "adminpass123"
        })
        
        if response.status_code == 200:
            self.token = response.json().get("data", {}).get("access")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(5)
    def get_dashboard_stats(self):
        """Get admin dashboard stats"""
        self.client.get("/api/v1/admin-dashboard/dashboard/", headers=self.headers)
    
    @task(3)
    def get_orders(self):
        """List orders"""
        self.client.get("/api/v1/admin-dashboard/orders/", headers=self.headers)
    
    @task(2)
    def get_users(self):
        """List users"""
        self.client.get("/api/v1/admin-dashboard/users/", headers=self.headers)


# Configuration for different load patterns
class SteadyLoad(PublicUser):
    """Steady load - typical usage"""
    weight = 10


class SpikeLoad(PublicUser):
    """High load - for spike testing"""
    wait_time = between(0.1, 0.5)
    weight = 2
