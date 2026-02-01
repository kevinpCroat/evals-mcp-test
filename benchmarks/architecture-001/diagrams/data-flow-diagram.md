# Data Flow Diagrams

## 1. Real-time Document Edit Flow

```mermaid
sequenceDiagram
    participant UserA as User A (Browser)
    participant UserB as User B (Browser)
    participant LB as Load Balancer
    participant WS as WebSocket Service
    participant Redis as Redis Pub/Sub
    participant DB as PostgreSQL

    Note over UserA,UserB: Both users connected to same document

    UserA->>LB: Edit: Insert "Hello"
    LB->>WS: Forward to instance 1
    WS->>WS: Apply CRDT operation locally
    WS->>Redis: Publish edit to channel "doc:123"
    Redis-->>WS: Broadcast to all instances
    WS->>UserB: Push edit via WebSocket
    UserB->>UserB: Apply CRDT operation locally
    UserB->>UserB: Render updated document

    WS->>DB: Persist CRDT state (async, batched)
    Note over WS,DB: Batch writes every 2 seconds or 100 operations

    UserB->>LB: Edit: Insert "World"
    LB->>WS: Forward to instance 2
    WS->>WS: Apply CRDT operation locally
    WS->>Redis: Publish edit to channel "doc:123"
    Redis-->>WS: Broadcast to all instances
    WS->>UserA: Push edit via WebSocket
    UserA->>UserA: Apply CRDT operation locally
    UserA->>UserA: Render updated document

    Note over UserA,UserB: Both users see "Hello World" with no conflicts
```

## 2. Document Load Flow

```mermaid
sequenceDiagram
    participant Client as Client Browser
    participant Gateway as API Gateway
    participant Auth as Auth Service
    participant App as App Service
    participant Cache as Redis Cache
    participant DB as PostgreSQL DB
    participant WS as WebSocket Service

    Client->>Gateway: GET /api/documents/123
    Gateway->>Auth: Validate JWT token
    Auth-->>Gateway: Token valid, user_id=456

    Gateway->>App: GET /documents/123?user=456
    App->>App: Check permission (user 456, doc 123)

    App->>Cache: GET doc:123
    alt Cache Hit
        Cache-->>App: Document data
        Note over App: Fast path (50ms)
    else Cache Miss
        App->>DB: SELECT * FROM documents WHERE id=123
        DB-->>App: Document data
        App->>Cache: SET doc:123 (expire 5min)
        Note over App: Slow path (200ms)
    end

    App-->>Gateway: Document JSON
    Gateway-->>Client: HTTP 200 + Document

    Note over Client: Client renders document

    Client->>WS: WebSocket connect /realtime
    WS->>Auth: Validate token
    Auth-->>WS: Valid user

    Client->>WS: JOIN doc:123
    WS->>DB: Check permission (user 456, doc 123)
    DB-->>WS: Permission granted
    WS->>Redis: PUBLISH presence:123 {user:456, action:joined}
    WS->>WS: Add user to room "doc:123"
    WS->>Client: JOINED doc:123
    WS->>Client: PRESENCE {users: [user1, user2, user456]}

    Note over Client,WS: Client now receives real-time updates
```

## 3. Document Search Flow

```mermaid
sequenceDiagram
    participant Client as Client Browser
    participant Gateway as API Gateway
    participant App as App Service
    participant ES as Elasticsearch
    participant DB as PostgreSQL
    participant Cache as Redis

    Client->>Gateway: GET /api/search?q="collaboration"
    Gateway->>App: Search query

    App->>Cache: GET search:"collaboration":user456
    alt Cache Hit (recent search)
        Cache-->>App: Cached results
        App-->>Client: Search results (fast)
    else Cache Miss
        App->>ES: Search query with user filter
        Note over ES: Query: match on content<br/>Filter: accessible by user 456
        ES-->>App: Document IDs + snippets

        App->>DB: SELECT metadata for doc IDs
        DB-->>App: Document metadata (title, author, etc)

        App->>App: Merge ES results + DB metadata
        App->>Cache: SET search results (expire 2min)
        App-->>Client: Search results with snippets
    end

    Client->>Client: Display search results
    Note over Client: Click on result
    Client->>Gateway: GET /api/documents/789
    Note over Client,DB: Triggers document load flow
```

## 4. Document Export Flow (Async)

```mermaid
sequenceDiagram
    participant Client as Client Browser
    participant App as App Service
    participant Queue as RabbitMQ
    participant Worker as Export Worker
    participant DB as PostgreSQL
    participant S3 as S3 Storage
    participant Email as Email Service

    Client->>App: POST /api/documents/123/export {format: "pdf"}
    App->>DB: Check permission + Get document
    DB-->>App: Document data

    App->>Queue: Publish export job
    Note over Queue: Job: {doc_id: 123, format: pdf, user: 456}
    App-->>Client: HTTP 202 Accepted {job_id: "abc"}

    Client->>Client: Poll for completion
    loop Every 2 seconds
        Client->>App: GET /api/jobs/abc
        App-->>Client: Status: "processing"
    end

    Queue-->>Worker: Export job
    Worker->>DB: Fetch document 123
    DB-->>Worker: Document content

    Worker->>Worker: Convert to PDF
    Note over Worker: Use headless Chrome / Pandoc

    Worker->>S3: Upload PDF
    S3-->>Worker: URL: s3://exports/123.pdf

    Worker->>DB: UPDATE jobs SET status=complete, url=...
    Worker->>Email: Send notification email
    Email-->>Client: Email with download link

    Client->>App: GET /api/jobs/abc
    App->>DB: Get job status
    DB-->>App: Status: complete, download_url
    App-->>Client: HTTP 200 {status: "complete", url: "..."}

    Client->>S3: Download PDF (signed URL)
    S3-->>Client: PDF file
```

## 5. New User Registration Flow

```mermaid
sequenceDiagram
    participant Client as Client Browser
    participant App as App Service
    participant Auth as Auth Service
    participant DB as PostgreSQL
    participant Email as Email Service
    participant Queue as RabbitMQ

    Client->>App: POST /api/auth/register<br/>{email, password, org}
    App->>App: Validate input
    App->>DB: Check if email exists
    DB-->>App: Email not found

    App->>App: Hash password (bcrypt)
    App->>DB: BEGIN TRANSACTION
    App->>DB: INSERT INTO organizations
    DB-->>App: org_id=123
    App->>DB: INSERT INTO users
    DB-->>App: user_id=456
    App->>DB: COMMIT

    App->>Auth: Generate JWT tokens
    Auth-->>App: access_token + refresh_token

    App->>Queue: Publish welcome_email job
    Queue-->>Email: Send welcome email
    Email-->Client: Welcome email sent

    App-->>Client: HTTP 201 Created<br/>{user, tokens}

    Client->>Client: Store tokens in localStorage
    Client->>App: GET /api/documents (with token)
    Note over Client,App: User is now authenticated
```

## 6. Cross-Region Sync Flow

```mermaid
sequenceDiagram
    participant UserUS as User (US-East)
    participant WSUS as WebSocket Service (US)
    participant DBUS as PostgreSQL (US)
    participant DBEU as PostgreSQL (EU)
    participant UserEU as User (EU-West)
    participant WSEU as WebSocket Service (EU)

    Note over UserUS,UserEU: Document replicated in both regions

    UserUS->>WSUS: Edit document
    WSUS->>WSUS: Apply CRDT operation
    WSUS->>UserUS: Confirm edit (10ms)

    WSUS->>DBUS: Write CRDT state (batched)
    Note over DBUS,DBEU: Async replication (~100-300ms lag)

    DBUS-->>DBEU: Replicate changes
    DBEU->>DBEU: Apply changes locally

    UserEU->>WSEU: Open document
    WSEU->>DBEU: Load document
    DBEU-->>WSEU: Document with US edits
    Note over WSEU: CRDT ensures consistency
    WSEU-->>UserEU: Document displayed

    UserEU->>WSEU: Edit document
    WSEU->>WSEU: Apply CRDT operation
    WSEU->>UserEU: Confirm edit (10ms)
    WSEU->>DBEU: Write CRDT state

    DBEU-->>DBUS: Replicate changes
    Note over DBUS,DBEU: Bi-directional replication

    DBUS->>DBUS: Apply changes
    Note over DBUS: CRDT merges US + EU edits

    Note over UserUS,UserEU: Both regions eventually consistent<br/>No conflicts due to CRDT
```

## Data Flow Summary

### Synchronous Paths (User-facing)
- **Document load**: Client → Gateway → App → Cache/DB → Response (50-200ms)
- **Real-time edit**: Client → WebSocket → Redis → Other clients (10-50ms)
- **Search**: Client → App → ES → DB → Response (100-500ms)

### Asynchronous Paths (Background)
- **CRDT persistence**: WebSocket → DB (batched, 2s delay)
- **Search indexing**: DB → Queue → Worker → Elasticsearch (5-10s delay)
- **Document export**: App → Queue → Worker → S3 → Email (30-60s)
- **Cross-region sync**: DB → Replication → Remote DB (100-300ms)

### Critical Paths (Performance Focus)
1. **Real-time edit propagation**: <100ms P95 (same region)
2. **Document load**: <2s for 1MB documents
3. **Search results**: <500ms
4. **WebSocket connection**: <1s

### Failure Modes

| Path | Failure | Fallback |
|------|---------|----------|
| Real-time edit | WebSocket down | Long polling |
| Cache miss | Redis unavailable | Read from DB |
| Database write | Primary down | Failover to replica |
| Search | Elasticsearch down | Degraded mode (no search) |
| Export | Worker failure | Retry from queue |

All paths designed with graceful degradation - core functionality remains even if components fail.
