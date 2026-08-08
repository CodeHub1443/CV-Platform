# CV Platform — Final Architecture v1.0

## 1. Authority

This document defines the authoritative high-level architecture of the CV Platform.

It defines:
- Permanent platform boundaries
- Platform responsibilities
- Platform dependency direction
- Architectural laws
- Placement rules for functionality

This document does not define implementation details.

Implementation must conform to this architecture.

---

## 2. Architectural Model

The CV Platform is composed of 13 permanent platforms.

These platforms represent stable domains.

Features must be implemented inside an existing platform whenever the feature belongs to that platform's domain.

Do not create a new top-level platform for a feature unless the feature represents a genuinely new stable domain.

### Permanent Platforms

| # | Platform | Responsibility |
|---|---|---|
| 1 | Configuration Platform | System configuration, projects, deployments |
| 2 | Camera Platform | Camera lifecycle and management |
| 3 | Camera Session Manager | Camera connection lifecycle |
| 4 | Media Platform | Video ingestion, distribution, recording, streaming |
| 5 | AI Runtime Platform | DeepStream, TensorRT, inference execution |
| 6 | Scene / Spatial Platform | Camera geometry and scene understanding |
| 7 | Evidence Platform | Convert AI output into reliable facts |
| 8 | Decision Platform | Business decisions |
| 9 | Event Platform | Event distribution |
| 10 | Workflow Platform | Multi-step business workflows |
| 11 | Service Platform | Alerting, notifications, incidents, GPIO |
| 12 | Storage Platform | Media, metadata, embeddings, evidence |
| 13 | API / Dashboard Platform | UI and external integrations |

---

# 3. System Flow

The primary processing flow is:

Configuration
→ Camera
→ Camera Session
→ Media
→ AI Runtime
→ Scene / Spatial
→ Evidence
→ Decision
→ Domain Event
→ Event
→ Workflow
→ Service

Storage and API/Dashboard provide persistence and external access according to their platform responsibilities.

---

# 4. Platform Responsibilities

## 4.1 Configuration Platform

Owns:

- Projects
- Sites
- Cameras
- AI Applications
- Models
- Rules
- Scene configuration
- Users
- Feature flags
- Deployments

Configuration is exposed to other platforms through the ConfigurationObject contract.

---

## 4.2 Camera Platform

Owns camera lifecycle and management.

Responsibilities:

- Camera discovery
- ONVIF
- SSDP
- ARP
- mDNS
- Vendor detection
- Credential management
- RTSP generation
- Camera registry
- Camera health
- Snapshots

### Architectural boundary

The Camera Platform does not know about AI inference.

---

## 4.3 Camera Session Manager

Owns the lifecycle of active camera connections.

Responsibilities:

- Camera connection
- Session creation
- Session termination
- Reconnection
- Connection state
- Consumer management
- Connection statistics

It produces `StreamSession`.

---

## 4.4 Media Platform

Owns video transport and media processing.

Responsibilities:

- RTSP
- SRT
- WebRTC
- Decode
- Encode
- Recording
- Streaming
- Archive
- Buffering
- Timestamp handling
- Synchronization

The Media Platform produces `EncodedVideo`.

---

## 4.5 AI Runtime Platform

Owns AI inference execution.

Responsibilities:

- DeepStream
- TensorRT
- CUDA
- ONNX
- Torch
- Model execution
- GPU allocation
- DLA
- Batching
- Pipeline execution
- Runtime scheduling

AI Runtime produces `RawMetadata`.

### Explicit exclusions

AI Runtime must NOT own:

- ROI
- Scene geometry
- Business rules
- Authorization
- Alerts
- Notifications

AI Runtime performs inference and produces metadata.

---

## 4.6 Scene / Spatial Platform

Owns static and derived spatial understanding.

Responsibilities:

- ROI
- Lines
- Zones
- Ground plane
- Calibration
- Perspective
- Distance
- Direction
- Entry/exit
- Privacy masks
- Exclusion zones
- Named areas
- Camera pose
- Homography

It consumes `RawMetadata` and produces `SpatialMetadata`.

---

## 4.7 Evidence Platform

Owns AI reliability and temporal validation.

Responsibilities:

- Temporal aggregation
- Voting
- Confidence smoothing
- Track history
- Re-identification
- Face fusion
- OCR fusion
- Sensor fusion
- False-positive suppression
- Cooldown
- Hysteresis
- Identity persistence

The Evidence Platform converts detections into reliable facts.

It produces `ReliableFact`.

### Explicit boundary

Evidence Platform does not send alerts or perform actions.

---

## 4.8 Decision Platform

Owns business decisions.

Responsibilities:

- Business rules
- Authorization
- Schedules
- Policies
- Geofencing
- Customer logic
- Risk scoring

Decision Platform consumes `ReliableFact`.

It produces `DomainEvent`.

### Explicit boundary

Decision Platform does not perform external actions.

It only creates domain events.

---

## 4.9 Event Platform

Owns event distribution.

Responsibilities:

- Publish
- Subscribe
- Routing
- Filtering
- Persistence
- Replay

The default event infrastructure is NATS + JetStream.

---

## 4.10 Workflow Platform

Owns multi-step business workflows.

Responsibilities:

- Incident lifecycle
- Escalation
- Approvals
- Retry
- Human review
- State machines
- Automation

Workflow Platform consumes domain events and produces workflow tasks and service commands.

---

## 4.11 Service Platform

Owns external actions and service integrations.

Responsibilities:

- Alerts
- Notifications
- Incidents
- GPIO
- Webhooks
- REST integrations
- MQTT
- SMS
- Email
- Telegram
- Slack

Services consume events/workflow commands.

Services do not call AI directly.

---

## 4.12 Storage Platform

Owns persistent assets.

Responsibilities:

- Images
- Video
- Metadata
- Embeddings
- Evidence
- Events
- Logs
- Models
- Configuration

Object storage uses the S3-compatible interface.

---

## 4.13 API / Dashboard Platform

Owns external application interfaces.

Responsibilities:

- REST
- GraphQL
- gRPC
- WebSocket
- Dashboard
- SDK
- Web/mobile interfaces

Live video should use WebRTC rather than REST.

---

# 5. Architectural Laws

These laws are mandatory.

### Law 1

Camera Platform never knows AI exists.

### Law 2

AI Runtime never knows business rules.

### Law 3

Evidence Platform never sends alerts.

### Law 4

Decision Platform never performs actions.

Decision Platform only creates Domain Events.

### Law 5

Services never call AI.

Services consume events and commands.

### Law 6

Every platform communicates through well-defined contracts.

Platforms must not exchange internal implementation objects.

### Law 7

Every new feature must belong to exactly one platform.

If functionality cannot be assigned to an existing platform, identify the missing abstraction before implementing it.

---

# 6. Feature Placement Rules

Examples:

| Feature | Platform |
|---|---|
| ROI | Scene / Spatial |
| Line crossing | Scene / Spatial |
| Face recognition temporal fusion | Evidence |
| Unknown person after office hours | Decision |
| Send Telegram | Service |
| Camera offline | Camera |
| Restart RTSP session | Camera Session Manager |
| Save evidence clip | Storage |
| Live dashboard | API / Dashboard |

Do not create feature-specific top-level platforms when the feature belongs to an existing domain.

---

# 7. Implementation Rule

Platform internals may evolve freely as long as:

1. Platform responsibility remains intact.
2. Platform boundaries remain intact.
3. Contracts remain compatible.
4. Architectural laws are not violated.

The implementation may change.

The architecture should remain stable.