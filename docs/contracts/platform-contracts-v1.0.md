# CV Platform — Platform Contracts v1.0

## 1. Authority

This document defines the immutable interfaces between CV Platform domains.

Platforms may change their internal implementation.

They must communicate with other platforms through these contracts.

A platform must never bypass a contract by depending on another platform's internal objects or libraries.

---

# 2. Contract Principles

## Principle 1 — Domain Ownership

Each platform owns its domain.

Examples:

- Camera Platform owns cameras.
- AI Runtime owns inference.
- Decision Platform owns business decisions.

---

## Principle 2 — Data, Not Implementation

Platforms expose contract data, not implementation objects.

Incorrect:

`DeepStreamObject`

Correct:

`RawMetadata`

---

## Principle 3 — Contract Stability

Contracts are stable interfaces.

Internal implementations may change without requiring downstream platforms to change.

Breaking contract changes require versioning.

---

## Principle 4 — Contract-Only Dependencies

Downstream platforms depend only on contracts.

They must not depend on internal implementation libraries of upstream platforms.

---

# 3. Contract Chain

The immutable primary data flow is:

CameraDescriptor
→ StreamSession
→ EncodedVideo
→ RawMetadata
→ SpatialMetadata
→ ReliableFact
→ DomainEvent
→ WorkflowTask
→ ServiceCommand

This sequence must not be bypassed.

---

# 4. Contract Definitions

## 4.1 CameraDescriptor

### Producer

Camera Platform

### Consumer

Camera Session Manager

### Purpose

Represents a registered camera.

### Data

- Camera ID
- Name
- Vendor
- RTSP URL
- Credentials
- Capabilities
- Resolution
- FPS
- Codec
- Location
- Health Status

---

## 4.2 StreamSession

### Producer

Camera Session Manager

### Consumer

Media Platform

### Purpose

Represents one active camera connection.

### Data

- Session ID
- Camera ID
- Connection State
- Reconnect Policy
- Consumers
- Statistics

---

## 4.3 EncodedVideo

### Producer

Media Platform

### Consumers

- Live Streaming
- Recording
- AI Runtime

### Purpose

Represents compressed video.

### Data

- Camera ID
- Timestamp
- Codec
- Bitstream
- Frame Number
- Key Frame Flag

### Constraint

`EncodedVideo` contains no decoded pixels.

---

## 4.4 RawMetadata

### Producer

AI Runtime

### Consumer

Scene / Spatial Platform

### Purpose

Represents raw AI inference output.

### Data

- Camera ID
- Timestamp
- Frame Number
- Application ID
- Model ID
- Track ID
- Bounding Box
- Class
- Confidence
- Segmentation
- Keypoints
- Embedding
- OCR
- Attributes

### Constraint

RawMetadata has no business meaning.

---

## 4.5 SpatialMetadata

### Producer

Scene / Spatial Platform

### Consumer

Evidence Platform

### Purpose

Represents AI metadata enriched with scene understanding.

### Data

RawMetadata plus:

- ROI
- Zone
- Ground Position
- Distance
- Direction
- Speed
- Line Crossing
- Perspective
- Camera Coordinates
- World Coordinates

---

## 4.6 ReliableFact

### Producer

Evidence Platform

### Consumer

Decision Platform

### Purpose

Represents AI output validated over time.

A ReliableFact is not a raw detection.

### Data

- Fact ID
- Fact Type
- Identity
- Confidence
- Evidence Score
- Track Lifetime
- History
- Supporting Models
- Supporting Frames
- Final State

### Examples

- Person Confirmed
- Vehicle Confirmed
- Fire Confirmed
- Unknown Face Confirmed
- Helmet Missing Confirmed

---

## 4.7 DomainEvent

### Producer

Decision Platform

### Consumers

Everything downstream that requires the event.

### Purpose

Represents something that happened.

### Data

- Event ID
- Event Type
- Severity
- Camera
- Site
- Timestamp
- Related Facts
- Payload

### Examples

- UnknownPersonDetected
- FireAlarm
- RestrictedAreaEntered
- PPEViolation
- VehicleExited
- AttendanceConfirmed

### Constraint

DomainEvent contains no implementation details.

---

## 4.8 WorkflowTask

### Producer

Workflow Platform

### Consumer

Service Platform

### Purpose

Represents an executable workflow step.

### Data

- Task ID
- Workflow ID
- Current State
- Action
- Timeout
- Retry Policy
- Dependencies

---

## 4.9 ServiceCommand

### Producer

Workflow Platform

### Consumer

Individual Services

### Purpose

Represents one external action.

### Data

- Command ID
- Command Type
- Priority
- Payload
- Retry Policy

### Examples

- Send Email
- Create Incident
- Capture Snapshot
- Open Barrier
- Activate Relay
- Call REST API
- Send MQTT
- Push WebSocket

---

## 4.10 StorageObject

### Producer

Any platform

### Consumer

Storage Platform

### Purpose

Represents a persistent asset.

### Data

- Object ID
- Object Type
- Owner
- Reference
- Retention
- Checksum
- Metadata

### Examples

- Snapshot
- Video Clip
- Evidence Image
- Model
- Embedding
- Log

---

## 4.11 ConfigurationObject

### Producer

Configuration Platform

### Consumers

All platforms

### Purpose

Represents runtime configuration.

### Data

- Object Type
- Version
- Owner
- Parameters
- Validation
- Effective Date

### Examples

- ROI
- Camera
- Rule
- Model
- Project
- Schedule
- Threshold
- User

---

## 4.12 HealthStatus

### Producer

Every platform

### Consumer

Health Platform / Dashboard

### Purpose

Represents platform/component health.

### Data

- Component
- State
- Severity
- Last Seen
- Metrics
- Message

### Examples

- Camera Offline
- GPU Hot
- Model Failed
- Storage Full
- High Latency
- Event Bus Healthy

---

# 5. Dependency Rules

The primary platform dependency chain is:

Camera
→ Media
→ AI Runtime
→ Scene / Spatial
→ Evidence
→ Decision
→ Workflow
→ Services

Illegal examples:

```text
DeepStream → Telegram
Camera → Database
Evidence → GPIO