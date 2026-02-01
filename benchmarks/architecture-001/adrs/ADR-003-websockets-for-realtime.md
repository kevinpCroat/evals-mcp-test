# ADR-003: WebSockets for Real-time Communication

## Status
Accepted

## Context

We need a real-time communication protocol for:
- Bidirectional communication between clients and server
- Pushing edit operations to connected clients
- Presence indicators (who's viewing/editing)
- Low latency (<100ms P95 for same-region)
- Support for 100,000 concurrent connections

Options for real-time web communication:
- WebSockets
- Server-Sent Events (SSE)
- Long Polling
- WebRTC
- HTTP/2 Server Push (deprecated)

## Decision

We will use **WebSockets** for real-time communication.

### Implementation
- WebSocket server using Socket.io (Node.js)
- Fallback to long polling for environments blocking WebSockets
- Sticky sessions via load balancer
- Redis pub/sub for message distribution across server instances
- Heartbeat/ping-pong for connection health monitoring

## Consequences

### Positive
- **True bidirectional**: Both client and server can initiate messages
- **Low latency**: Persistent connection, no connection overhead per message
- **Efficient**: Less bandwidth overhead than polling or SSE
- **Wide browser support**: All modern browsers support WebSockets
- **Real-time feel**: Instant push of updates to clients
- **Mature ecosystem**: Many libraries and tools (Socket.io, ws, uWebSockets)
- **Automatic reconnection**: Libraries handle connection drops and reconnection
- **Room/namespace support**: Socket.io provides easy grouping of connections

### Negative
- **Stateful connections**: Requires sticky sessions or state coordination
- **Scaling complexity**: Need Redis pub/sub to coordinate across instances
- **Load balancing**: Requires special handling (sticky sessions, WebSocket-aware LB)
- **Connection limits**: Each connection consumes server resources
- **Proxy/firewall issues**: Some corporate networks block WebSocket connections
- **No HTTP/2 multiplexing**: Each WebSocket is a separate TCP connection
- **Memory overhead**: Each connection holds state in memory

## Alternatives Considered

### Alternative 1: Server-Sent Events (SSE)
- **Description**: HTTP-based unidirectional push from server to client
- **Pros**:
  - Simpler than WebSockets (just HTTP)
  - Automatic reconnection built-in
  - Works through most proxies/firewalls
  - HTTP/2 multiplexing support
  - No special load balancer configuration
  - Easier to debug (uses regular HTTP)
- **Cons**:
  - Unidirectional only (server → client)
  - Clients must use separate HTTP requests for server-bound messages
  - Connection limits per domain (browser-dependent)
  - No binary data support (text only)
  - Less efficient than WebSockets for bidirectional use
  - Limited browser support compared to WebSockets
- **Reason for rejection**: Bidirectional communication is important for our use case. While SSE could work (clients send edits via HTTP POST, receive updates via SSE), WebSockets is more natural for our bidirectional needs and has lower latency for client-to-server messages.

### Alternative 2: Long Polling
- **Description**: Client polls server, server holds request open until data available
- **Pros**:
  - Works everywhere (no special protocols)
  - Compatible with all HTTP infrastructure
  - Simple fallback mechanism
  - No connection blocking issues
- **Cons**:
  - Higher latency (connection setup overhead)
  - More server resources (constant connection churn)
  - Inefficient (reconnection overhead)
  - Complex timeout handling
  - Not truly real-time
  - Higher bandwidth usage
- **Reason for rejection**: Too high latency for real-time editing. We need <100ms updates, and long polling typically adds 50-200ms overhead. Only suitable as a fallback for environments where WebSockets are blocked.

### Alternative 3: WebRTC Data Channels
- **Description**: Peer-to-peer data channels using WebRTC
- **Pros**:
  - True peer-to-peer (lower server load)
  - Very low latency potential
  - Can work without server in the middle
  - Supports both reliable and unreliable delivery
- **Cons**:
  - Complex to implement and debug
  - NAT traversal issues (STUN/TURN servers needed)
  - Requires server for initial handshake
  - Not all edits can be peer-to-peer (need server for persistence)
  - Overkill for document editing
  - Browser compatibility issues
  - Difficult to implement access control
- **Reason for rejection**: Unnecessary complexity. We need server in the middle for permissions, persistence, and cross-region sync. WebRTC is designed for media streaming, not document editing. The complexity doesn't justify the benefits.

### Alternative 4: HTTP/2 Server Push (deprecated)
- **Description**: Server pushes resources to client over HTTP/2
- **Pros**:
  - Uses standard HTTP/2
  - Good browser support
  - No special protocols
- **Cons**:
  - Being deprecated by browsers (Chrome removed support)
  - Not designed for bidirectional real-time
  - Limited to resource pushing, not arbitrary data
  - No future support
- **Reason for rejection**: Deprecated technology. Chrome has removed support, other browsers following. Not suitable for our needs.

## Implementation Notes

### Socket.io Configuration
```javascript
const io = require('socket.io')(server, {
  cors: {
    origin: process.env.ALLOWED_ORIGINS,
    credentials: true
  },
  transports: ['websocket', 'polling'], // Fallback to polling
  pingTimeout: 30000,
  pingInterval: 25000
});

// Authentication middleware
io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;
  try {
    const user = await verifyJWT(token);
    socket.user = user;
    next();
  } catch (err) {
    next(new Error('Authentication failed'));
  }
});

// Document room handling
io.on('connection', (socket) => {
  socket.on('join-document', async (documentId) => {
    // Verify user has access to document
    const hasAccess = await checkPermission(socket.user.id, documentId);
    if (!hasAccess) {
      return socket.emit('error', 'Access denied');
    }

    // Join room for this document
    socket.join(`doc:${documentId}`);

    // Broadcast presence
    io.to(`doc:${documentId}`).emit('user-joined', {
      userId: socket.user.id,
      name: socket.user.name
    });
  });

  socket.on('edit-operation', async (data) => {
    const { documentId, operation } = data;

    // Broadcast to all users in document room (except sender)
    socket.to(`doc:${documentId}`).emit('remote-edit', {
      userId: socket.user.id,
      operation
    });

    // Persist operation (async)
    persistOperation(documentId, operation).catch(err => {
      console.error('Failed to persist operation:', err);
    });
  });
});
```

### Redis Pub/Sub for Multi-Instance
```javascript
const Redis = require('ioredis');
const redisAdapter = require('@socket.io/redis-adapter');

const pubClient = new Redis(process.env.REDIS_URL);
const subClient = pubClient.duplicate();

io.adapter(redisAdapter(pubClient, subClient));
```

### Load Balancer Configuration (NGINX)
```nginx
upstream websocket_backend {
  ip_hash;  # Sticky sessions
  server backend1:3000;
  server backend2:3000;
  server backend3:3000;
}

server {
  listen 443 ssl;

  location /socket.io/ {
    proxy_pass http://websocket_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 86400;  # 24 hours
  }
}
```

### Scaling Strategy
- **Phase 1**: 3-5 WebSocket server instances per region
- **Phase 2**: Auto-scale based on connection count (5000 connections per instance)
- **Phase 3**: Dedicated WebSocket clusters per region with cross-region Redis

### Risk Mitigation
- **Connection drops**: Automatic reconnection with exponential backoff
- **Firewall blocking**: Fallback to long polling (Socket.io handles automatically)
- **Memory leaks**: Regular connection cleanup, monitoring
- **DDoS**: Rate limiting, connection limits per IP, authentication required

### Success Metrics
- WebSocket connection success rate >99%
- Message delivery latency P95 <50ms same-region
- Reconnection time <2 seconds
- Support 100,000 concurrent connections
- Memory usage <100MB per 1000 connections
