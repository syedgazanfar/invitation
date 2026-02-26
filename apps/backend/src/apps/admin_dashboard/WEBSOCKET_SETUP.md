# WebSocket Setup for Real-time Admin Dashboard

This document describes the WebSocket setup for real-time updates in the admin dashboard.

## Architecture Overview

```
┌─────────────────┐     WebSocket      ┌──────────────────┐
│  React Frontend │ ◄────────────────► │ Django Channels  │
│  (useWebSocket) │                    │  (Consumers)     │
└─────────────────┘                    └──────────────────┘
                                              │
                                              ▼
                                       ┌──────────────────┐
                                       │  Redis Channel   │
                                       │     Layer        │
                                       └──────────────────┘
                                              │
                                              ▼
                                       ┌──────────────────┐
                                       │  Django Signals  │
                                       │  (post_save)     │
                                       └──────────────────┘
```

## Components

### 1. Django Channels Consumer (`consumers.py`)

The `AdminDashboardConsumer` handles WebSocket connections:
- Authenticates users via JWT token in query string
- Manages admin group membership
- Broadcasts updates to all connected admins
- Handles heartbeat/ping-pong for connection health

### 2. Django Signals (`signals.py`)

Signals trigger WebSocket broadcasts when:
- New user registers (`User` model post_save)
- User approval status changes
- Order status changes
- New admin notifications created

### 3. React Hook (`useWebSocket.ts`)

Provides WebSocket functionality:
- Automatic connection management
- Reconnection with exponential backoff
- Heartbeat/ping-pong
- Type-safe message handling
- Connection state tracking

### 4. React Component (`RealTimeDashboard.tsx`)

Real-time dashboard UI:
- Live pending approval count
- Pending users list with approve/reject actions
- Recent activity feed
- Notification badges
- Connection status indicator

## Setup Instructions

### 1. Install Dependencies

```bash
pip install channels>=4.0.0 channels-redis>=4.1.0 daphne>=4.0.0
```

### 2. Configure Django Settings

Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ...
    'daphne',
    'channels',
    # ...
]
```

Configure channel layers:
```python
ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('localhost', 6379)],
        },
    },
}
```

### 3. Run with ASGI Server

Use Daphne or Uvicorn to run the ASGI application:

```bash
# Using Daphne
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Using Uvicorn
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
```

Or with Docker:

```bash
docker-compose up -d
```

## API Endpoints

### WebSocket Endpoint

```
ws://localhost:8000/ws/admin/dashboard/?token=<JWT_ACCESS_TOKEN>
```

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin-dashboard/dashboard/` | GET | Get dashboard statistics |
| `/api/v1/admin-dashboard/approvals/pending/` | GET | Get pending approvals list |
| `/api/v1/admin-dashboard/approvals/recent/` | GET | Get recent approval actions |
| `/api/v1/admin-dashboard/users/<id>/approve/` | POST | Approve a user |
| `/api/v1/admin-dashboard/users/<id>/reject/` | POST | Reject a user |
| `/api/v1/admin-dashboard/notifications/` | GET | Get admin notifications |

## WebSocket Message Types

### From Server to Client

| Type | Description |
|------|-------------|
| `connection_established` | Initial connection confirmation |
| `approval_update` | User approved/rejected |
| `pending_count_update` | Pending count changed |
| `new_user` | New user registered |
| `order_update` | Order status changed |
| `admin_joined` | Another admin connected |
| `admin_left` | Admin disconnected |
| `pong` | Heartbeat response |

### From Client to Server

| Type | Description |
|------|-------------|
| `ping` | Keepalive ping |
| `get_stats` | Request dashboard stats |
| `get_pending_count` | Request pending count |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `USE_INMEMORY_CHANNELS` | Use in-memory channels (dev only) | `False` |

## Testing WebSocket Connection

### Using Browser Console

```javascript
// Connect to WebSocket
const token = localStorage.getItem('accessToken');
const ws = new WebSocket(`ws://localhost:8000/ws/admin/dashboard/?token=${token}`);

// Listen for messages
ws.onmessage = (event) => {
    console.log('Message:', JSON.parse(event.data));
};

// Send ping
ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
```

### Using wscat

```bash
npm install -g wscat
wscat -c "ws://localhost:8000/ws/admin/dashboard/?token=<JWT_TOKEN>"
> {"type": "ping", "timestamp": 1234567890}
```

## Troubleshooting

### Connection Refused

1. Ensure Redis is running:
   ```bash
   redis-cli ping
   ```

2. Check ASGI server is running on correct port

3. Verify CORS settings allow WebSocket origins

### Authentication Failed

1. Check JWT token is valid and not expired
2. Ensure user has `is_staff=True`
3. Verify token is passed correctly in query string

### Messages Not Broadcasting

1. Check Redis connection in settings
2. Verify consumer is added to admin group
3. Check signal handlers are imported in `apps.py`

## Security Considerations

1. **Authentication**: WebSocket connections require valid JWT token
2. **Authorization**: Only staff users can connect to admin dashboard
3. **Origin Validation**: AllowedHostsOriginValidator restricts connections
4. **Rate Limiting**: Consider adding rate limiting for WebSocket messages
5. **Input Validation**: All messages are validated before processing

## Performance Optimization

1. Use Redis for channel layer in production
2. Implement message batching for high-frequency updates
3. Add pagination for large pending user lists
4. Use selective broadcasting when possible
