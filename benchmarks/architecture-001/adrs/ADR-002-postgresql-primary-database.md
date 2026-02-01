# ADR-002: PostgreSQL as Primary Database

## Status
Accepted

## Context

We need to select a primary database for storing:
- Document content and metadata (50KB average, 10MB max)
- User and organization data
- Permissions and access control
- Version history (all historical versions retained)
- CRDT state for documents

Requirements:
- Handle 1M+ documents at launch, 10M+ within 2 years
- Support complex queries for permissions and search
- ACID compliance for critical operations (permissions changes, billing)
- Multi-region replication
- Flexible schema for evolving document structure
- Strong consistency for user-facing operations

## Decision

We will use **PostgreSQL with JSONB** as our primary database.

### Configuration
- PostgreSQL 15+ for latest features
- JSONB column for document content
- Traditional relational schema for users, orgs, permissions
- Partitioning by organization_id for large tables
- Read replicas for read-heavy operations
- PgBouncer for connection pooling

## Consequences

### Positive
- **ACID guarantees**: Strong consistency for critical operations (permissions, billing)
- **Flexible schema**: JSONB allows document structure to evolve without migrations
- **Powerful queries**: Can query inside JSONB with GIN indexes for performance
- **Mature ecosystem**: Excellent tooling, monitoring, backup solutions
- **Battle-tested**: Used at massive scale by many companies
- **Cost-effective**: Open source with good cloud-managed options
- **Multi-region**: Built-in replication (async and sync options)
- **JSON + Relational**: Best of both worlds - structured data in tables, flexible data in JSONB
- **GIN indexing**: Efficient queries on JSONB content
- **Full-text search**: Built-in capabilities (can defer to Elasticsearch later)

### Negative
- **Vertical scaling limits**: Single-instance write bottleneck (mitigated with read replicas)
- **JSONB overhead**: Slightly larger storage than binary formats
- **Operational complexity**: Requires PostgreSQL expertise for tuning and optimization
- **Replication lag**: Read replicas may be behind primary (eventual consistency for reads)
- **Sharding complexity**: Manual sharding if we outgrow single instance
- **JSONB performance**: Slower than native columns for frequently accessed fields

## Alternatives Considered

### Alternative 1: MongoDB
- **Description**: Document-oriented NoSQL database with native JSON support
- **Pros**:
  - Native document model matches our use case
  - Horizontal sharding built-in
  - Flexible schema by default
  - Good performance for read-heavy workloads
  - Easy to scale horizontally
- **Cons**:
  - Weaker consistency guarantees (default is eventual consistency)
  - Less mature transaction support than PostgreSQL
  - Complex permission queries harder to express
  - Less familiar to team (steeper learning curve)
  - Can be expensive at scale
  - Historical issues with data durability (improved, but risk perception remains)
- **Reason for rejection**: The lack of strong ACID guarantees for permissions and billing operations is a dealbreaker. Permissions bugs could allow unauthorized access - unacceptable for SOC 2 compliance. PostgreSQL's relational model is better for complex permission queries.

### Alternative 2: DynamoDB (or other key-value store)
- **Description**: Fully managed key-value store with high scalability
- **Pros**:
  - Massive scalability (millions of requests/second)
  - Fully managed (no ops burden)
  - Predictable performance at any scale
  - Multi-region replication built-in
  - Cost-effective for read-heavy workloads
- **Cons**:
  - Limited query capabilities (requires careful data modeling)
  - No joins (need to denormalize or make multiple queries)
  - Complex permission queries very difficult
  - No transactions across multiple items (limited transaction support)
  - Vendor lock-in (AWS-specific)
  - Schema design is critical and hard to change
- **Reason for rejection**: The lack of flexible querying makes complex permission checks and user management very difficult. We'd need to denormalize heavily and maintain multiple indexes, increasing complexity and risk of inconsistency. Better for simple key-value access patterns, not our use case.

### Alternative 3: Hybrid (PostgreSQL + MongoDB)
- **Description**: Use PostgreSQL for structured data (users, permissions) and MongoDB for document content
- **Pros**:
  - Optimized for each data type
  - PostgreSQL for relational, MongoDB for documents
  - Can scale each independently
- **Cons**:
  - Operational complexity of running two databases
  - Data consistency across databases is difficult
  - Transactions across databases not supported
  - Increased development complexity
  - Higher ops burden (monitoring, backups, upgrades × 2)
  - More expensive (two database clusters)
- **Reason for rejection**: Unnecessary complexity for MVP. PostgreSQL with JSONB handles both use cases well enough. If we hit scaling limits, we can introduce MongoDB later, but starting with two databases would slow development and increase operational risk.

### Alternative 4: MySQL with JSON
- **Description**: Similar to PostgreSQL approach but with MySQL
- **Pros**:
  - Very similar to PostgreSQL option
  - Slightly simpler replication setup
  - Some team members more familiar with MySQL
- **Cons**:
  - JSON support less mature than PostgreSQL JSONB
  - Fewer advanced features (PostgreSQL has better JSON operators)
  - Less performant JSON queries
  - Historically weaker on data integrity features
- **Reason for rejection**: PostgreSQL's JSONB implementation is superior to MySQL's JSON. Better indexing (GIN), better query performance, and more powerful JSON operators. Since we're not locked into MySQL, PostgreSQL is the better choice.

## Implementation Notes

### Schema Design
```sql
-- Core tables
CREATE TABLE organizations (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  org_id UUID REFERENCES organizations(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE documents (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES organizations(id),
  title TEXT NOT NULL,
  content JSONB NOT NULL,
  crdt_state JSONB,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- GIN index for fast JSONB queries
CREATE INDEX idx_documents_content ON documents USING GIN (content);

-- Partition by org_id for very large tables
CREATE TABLE documents_partitioned (
  LIKE documents INCLUDING ALL
) PARTITION BY HASH (org_id);
```

### Scaling Strategy
1. **Phase 1** (0-10k orgs): Single instance with read replicas
2. **Phase 2** (10k-50k orgs): Add more read replicas, tune queries
3. **Phase 3** (50k+ orgs): Implement sharding by org_id if needed

### Risk Mitigation
- **Write bottleneck**: Monitor write load, implement caching for frequently updated documents
- **Storage growth**: Implement document archival, compression for old versions
- **Query performance**: Regular EXPLAIN ANALYZE, query optimization, proper indexing
- **Operational expertise**: Hire PostgreSQL DBA consultant for initial setup and training

### Success Metrics
- Query latency P95 <50ms for document reads
- Transaction latency P95 <100ms for permission updates
- Database availability >99.9%
- Replication lag <1 second for read replicas
