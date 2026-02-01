# ADR-001: Use CRDTs for Real-time Collaboration

## Status
Accepted

## Context

The platform requires real-time collaborative editing where multiple users can simultaneously edit the same document. We need a conflict resolution strategy that provides:
- Low latency (<100ms for same-region edits)
- Automatic conflict resolution without user intervention
- Eventual consistency guarantees
- Offline editing capability with later synchronization

The two primary approaches are Operational Transformation (OT) and Conflict-free Replicated Data Types (CRDTs).

### Key Constraints
- Must scale to 100+ concurrent editors per document
- Must work across multiple server instances and regions
- Must support offline editing with sync on reconnection
- Development timeline: 6 months to MVP

## Decision

We will use **CRDTs (specifically the Yjs library)** for real-time collaborative editing.

### Implementation Details
- Use Yjs library (mature, battle-tested CRDT implementation)
- Store CRDT state updates in PostgreSQL
- Synchronize via WebSockets for real-time updates
- Use awareness protocol for presence indicators

## Consequences

### Positive
- **No central authority needed**: Each client can operate independently, reducing server complexity
- **Built-in conflict resolution**: Mathematically guaranteed eventual consistency without manual conflict resolution
- **Better offline support**: CRDTs naturally support offline editing with automatic sync
- **Simpler reasoning**: Operations are commutative and idempotent, easier to reason about correctness
- **Proven library**: Yjs is mature, well-tested, and used in production by multiple companies
- **Multi-region friendly**: No need for central coordination across regions
- **Undo/redo support**: CRDTs make it easier to implement undo/redo functionality

### Negative
- **Larger data structures**: CRDTs can have larger memory footprint than plain text with OT
- **Learning curve**: Team needs to learn CRDT concepts and Yjs API
- **Storage overhead**: CRDT metadata must be stored alongside document content
- **Limited ecosystem**: Fewer resources/tools compared to OT implementations
- **Potential for zombie edits**: Deleted content can reappear if not handled carefully (need tombstones)
- **No custom merge logic**: Automatic resolution means we can't implement business-specific merge rules

## Alternatives Considered

### Alternative 1: Operational Transformation (OT)
- **Description**: Transform operations against concurrent operations to maintain consistency. Used by Google Docs (though they've moved to more complex hybrid approaches).
- **Pros**:
  - Smaller data structures than CRDTs
  - More control over merge behavior
  - Established pattern (Google Docs historically used OT)
  - Potentially lower storage overhead
- **Cons**:
  - Complex to implement correctly (many edge cases)
  - Requires central server to order operations
  - Difficult to get right with multiple servers/regions
  - Poor offline support (needs to replay operations in order)
  - Higher latency across regions (need to coordinate)
  - Proven to be extremely difficult to implement bug-free
- **Reason for rejection**: Implementation complexity and risk. OT is notoriously difficult to implement correctly, with subtle bugs that can appear in edge cases. Given our 6-month timeline and the need for multi-region support, the risk is too high. Google's implementation took years to mature.

### Alternative 2: Last-Write-Wins (LWW) with Locking
- **Description**: Simple approach where the last edit wins, potentially with document-level or section-level locking to prevent conflicts.
- **Pros**:
  - Simplest to implement
  - Minimal overhead
  - Easy to understand
  - Low storage requirements
- **Cons**:
  - Poor user experience (users lose work)
  - Document locking reduces collaboration
  - Doesn't meet real-time collaborative editing requirement
  - No offline support
  - Not suitable for true simultaneous editing
- **Reason for rejection**: Doesn't meet core requirement of simultaneous multi-user editing. Would result in poor UX and lost work, which is unacceptable for a collaborative editing platform.

### Alternative 3: Hybrid OT + CRDT
- **Description**: Use CRDTs for most operations but OT for specific complex scenarios requiring custom merge logic.
- **Pros**:
  - Flexibility to handle edge cases
  - Can optimize for specific use cases
  - Potentially best of both worlds
- **Cons**:
  - Significantly increased complexity
  - Difficult to maintain two systems
  - Higher risk of bugs at the intersection
  - Longer development time
  - Team needs expertise in both approaches
- **Reason for rejection**: Unnecessary complexity for MVP. If we find CRDT limitations in production, we can add selective OT later. Starting with both would delay launch and increase bug risk.

## Implementation Notes

### Risk Mitigation
- **Storage overhead**: Monitor document sizes in production, implement compression if needed
- **Learning curve**: Allocate 2 weeks for team training on Yjs and CRDT concepts
- **Zombie edits**: Implement proper tombstone handling and document compaction
- **Performance**: Benchmark with 100+ concurrent users during development

### Success Metrics
- P95 latency <100ms for same-region edits
- Zero data loss in conflict scenarios
- Successful merge of 100+ concurrent edits
- Offline edit sync success rate >99%

### Future Considerations
- If CRDT storage overhead becomes problematic, consider periodic compaction or hybrid approach
- Monitor Yjs library updates and contribute back to open source if we find issues
- Consider custom CRDT implementation only if Yjs proves insufficient (unlikely)
