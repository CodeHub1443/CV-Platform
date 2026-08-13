# Specification for Proposal: CVP-001-arch

## Architecture
The Configuration Platform is the authoritative source of all system configuration in the CV Platform. It is structured as a four-layer service. Layer 1 — REST API Layer: exposes CRUD endpoints for all owned entities using api-core; every response is serialized as a ConfigurationObject. Layer 2 — Service Layer: validates configuration changes, enforces versioning rules, manages entity lifecycle, and coordinates relationships between owned entities. Layer 3 — Repository Layer: one repository per configuration entity, all using db-core; no raw database drivers. Layer 4 — Database: PostgreSQL as the standard relational database per Technology Stack v1.0. Entity hierarchy: Project is the root entity. A Project contains Sites, Users, Feature Flags, AI Applications, and Deployments. A Site contains Camera Configuration records and Scene Configuration records. An AI Application contains Models and Rules. A Deployment links an AI Application to a camera Site and captures a versioned snapshot of configuration at deploy time. Ownership boundary: Configuration Platform owns static camera configuration records (RTSP URL, credentials, capabilities, resolution, codec). Camera Platform reads these records via ConfigurationObject and owns runtime lifecycle, health, and session state. ConfigurationObject contract compliance: all configuration exposed to other platforms is wrapped in the standard contract with fields object_type, version, owner, parameters, validation, and effective_date. No internal implementation objects are ever exposed across platform boundaries. Configuration propagation model for baseline: REST pull. Consumers fetch ConfigurationObject by ID or query. Version field allows consumers to detect staleness. NATS JetStream push notifications for configuration changes are deferred to a future iteration. Reusable modules api-core and db-core are the only shared infrastructure required. No new infrastructure modules are introduced.

## Reusable Modules
- {'module': 'api-core', 'purpose': 'REST API routing, request parsing, response serialization, and error handling'}
- {'module': 'db-core', 'purpose': 'PostgreSQL connection management, query execution, transaction support, and repository base classes'}

## Dependencies
- {'module': 'api-core', 'reason': 'REST API routing and response handling for all configuration endpoints', 'version': 'stable'}
- {'module': 'db-core', 'reason': 'PostgreSQL persistence layer and repository base classes', 'version': 'stable'}
- {'reason': 'Authoritative relational database standard per Technology Stack v1.0', 'technology': 'PostgreSQL', 'version': 'standard'}

## Risks
- {'description': 'Camera configuration ownership ambiguity: Configuration Platform owns camera configuration records while Camera Platform owns camera lifecycle. If the boundary is not explicitly enforced, Camera Platform may write configuration directly to its own store, creating two sources of truth.', 'id': 'R-001', 'mitigation': 'Define at schema design time (CVP-002) that camera configuration records live exclusively in the Configuration Platform database. Camera Platform reads camera configuration only via ConfigurationObject through the REST API. Camera Platform must not maintain its own relational camera configuration table.'}
- {'description': 'Configuration change propagation latency: REST pull model means downstream platforms may operate on stale configuration if they cache ConfigurationObject without checking the version field.', 'id': 'R-002', 'mitigation': 'ConfigurationObject version field is mandatory in the baseline. Consumers must compare version before using cached configuration. NATS JetStream push notifications are the recommended long-term solution and are deferred to a post-baseline task.'}
- {'description': 'Authorization enforcement scope: Configuration Platform owns User records and Feature Flags, but authorization enforcement is a cross-cutting concern that spans all platforms. Conflating user record ownership with authorization enforcement risks embedding authorization logic inside Configuration Platform.', 'id': 'R-003', 'mitigation': 'Configuration Platform owns User records as configuration data only. It does not enforce authorization across other platforms. A dedicated authorization task must be defined separately and placed in the correct platform boundary.'}

## Unresolved Decisions
- {'id': 'UD-001', 'question': 'Should Configuration Platform publish configuration-change events to NATS JetStream when entities are created, updated, or deleted, as part of the baseline, or is REST pull with version comparison sufficient?', 'recommendation': 'REST pull is sufficient for the baseline. NATS JetStream push events for configuration changes should be added as a follow-on task once the REST API is stable and consumers are identified.'}
- {'id': 'UD-002', 'question': 'Should Deployment store a full versioned snapshot of the configuration at deploy time, or should it store live references that reflect the current state of each configuration entity?', 'recommendation': 'Deployment must store a versioned snapshot. A live reference would cause active deployments to silently change behavior when upstream configuration is updated, which is unsafe in a production CV system.'}

## Acceptance Criteria
- Configuration Platform owns exactly: Projects, Sites, Camera Configuration records, AI Applications, Models, Rules, Scene Configuration, Users, Feature Flags, Deployments
- Camera runtime lifecycle, health, and session state are NOT owned by Configuration Platform — those belong to Camera Platform and Camera Session Manager respectively
- All configuration exposed to other platforms is wrapped in ConfigurationObject {object_type, version, owner, parameters, validation, effective_date}
- No other platform's internal objects or libraries are imported by Configuration Platform
- PostgreSQL is the only relational database used — no alternative relational database is introduced
- REST is used for all configuration CRUD operations per Technology Stack v1.0
- api-core and db-core are the only shared modules used — no new infrastructure modules are introduced
- No implementation code is produced in task CVP-001
