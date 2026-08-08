# CV Platform — Technology Stack & Infrastructure Standards v1.0

## 1. Purpose

This document defines the default technology stack and infrastructure standards for the CV Platform.

These are the default choices for all CV Platform projects unless a specific technical requirement justifies a deviation.

---

## 2. Event Bus

### Standard

**NATS + JetStream**

### Reasons

- Native pub/sub + persistence
- Reliable delivery
- Request/reply support
- Scales from Jetson to multi-server deployments
- Suitable for distributed CV systems

### Usage

NATS JetStream is the default event bus for platform communication and durable events.

### ZeroMQ

Use **ZeroMQ only for ultra-low-latency internal components** where persistence and durability are not required.

ZeroMQ is not the default platform event bus.

### Decision

**NATS + JetStream**

---

## 3. Database Stack

The following database technologies are standardized across CV Platform projects.

| Purpose | Technology | Decision |
|---|---|---|
| Relational | PostgreSQL | Standard |
| Time-series | TimescaleDB | Standard |
| Cache / State | Redis | Standard |
| Object Storage | S3-compatible | Standard |
| Vector Database | Qdrant | Standard |

### 3.1 PostgreSQL

Primary relational database.

### 3.2 TimescaleDB

PostgreSQL extension for time-series data.

### 3.3 Redis

Used for cache and runtime state.

### 3.4 Object Storage

Use an S3-compatible interface.

- Local / on-premise: **MinIO**
- Cloud: **Amazon S3 or compatible S3 storage**

### 3.5 Qdrant

Standard vector database for embeddings and vector search.

---

## 4. Backend and Frontend

### Backend Deployment Targets

The backend may run on:

- NVIDIA Jetson
- RTX PC
- GPU Server

### Frontend Targets

The frontend may run on:

- Browser
- Mobile
- Remote PC

---

## 5. Communication Standards

| Requirement | Technology |
|---|---|
| Configuration | REST API |
| CRUD | REST API |
| Live events | WebSocket |
| Health | WebSocket |
| Live metadata | WebSocket |
| Live video | WebRTC |
| Video fallback | HLS |
| Snapshots | S3 / Object Storage |
| Recordings | S3 / Object Storage |

### REST

Use REST for configuration and CRUD operations.

Do not use REST for live video streaming.

### WebSocket

Use WebSocket for:

- Live events
- Health information
- Live metadata

### WebRTC

WebRTC is the preferred live-video transport.

### HLS

HLS may be used as a fallback when WebRTC is not suitable or available.

### Object Storage

Snapshots and recordings are stored through the S3-compatible object-storage layer.

---

# 6. Fixed Default Stack

The default CV Platform stack is:

```text
Event Bus
    NATS + JetStream

Low-Latency Internal Messaging
    ZeroMQ (only when persistence/durability is not required)

Relational Database
    PostgreSQL

Time-Series Database
    TimescaleDB

Cache / Runtime State
    Redis

Object Storage
    S3-compatible
    ├── MinIO (local/on-premise)
    └── S3 (cloud)

Vector Database
    Qdrant

API
    REST

Live Events / Health / Metadata
    WebSocket

Live Video
    WebRTC

Live Video Fallback
    HLS