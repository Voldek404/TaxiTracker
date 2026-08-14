<div align="center">

<img src="screenshots/hero.svg"
     alt="TaxiTracker"
     width="100%">

</div>

<div align="center">

# TaxiTracker

### Fleet Management & Real-Time Monitoring Platform

<p>
  Django · PostgreSQL/PostGIS · Kafka · Redis · Prometheus · Grafana
</p>

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)](...)
[![Django](https://img.shields.io/badge/Django-5.2.5-092E20?style=flat-square&logo=django&logoColor=white)](...)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](...)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-event%20streaming-231F20?style=flat-square&logo=apachekafka&logoColor=white)](...)
[![Docker](https://img.shields.io/badge/Docker-containerized-2496ED?style=flat-square&logo=docker&logoColor=white)](...)

</div>

The system acts as an aggregator of taxi fleets and provides managers with controlled access to the vehicles assigned to their area of responsibility. The platform combines a web interface, REST API, Telegram notifications, reporting, geospatial trip visualization, data export/import, monitoring, and several supporting microservices.

The project was designed with a strong focus on **modular architecture, separation of responsibilities, observability, performance, and deployment automation**.

**Repository:** https://github.com/Voldek404/TaxiTracker


## Table of Contents

- [Features](#features)
  - [Fleet Management](#fleet-management)
  - [Vehicle and Trip Tracking](#vehicle-and-trip-tracking)
  - [REST API](#rest-api)
  - [Telegram Bot](#telegram-bot)
- [Product Preview](#product-preview)
- [Architecture](#architecture)
  - [Onion Architecture](#onion-architecture)
  - [Microservices](#microservices)
    - [Notification Service](#notification-service)
    - [Track Generator Service](#track-generator-service)
  - [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
  - [Backend](#backend)
  - [Caching and Performance](#caching-and-performance)
  - [Messaging](#messaging)
  - [Monitoring and Observability](#monitoring-and-observability)
  - [Performance Testing](#performance-testing)
- [Monitoring](#monitoring)
- [Data Import and Export](#data-import-and-export)
- [Access Control](#access-control)
- [Deployment](#deployment)
  - [Initial Deployment](#initial-deployment)
  - [Updating an Existing Deployment](#updating-an-existing-deployment)
- [Local Development](#local-development)
- [Engineering Highlights](#engineering-highlights)
- [Project Status](#project-status)
- [Repository](#repository)

---

## Features

### Fleet Management

Managers can access the taxi fleets within their assigned scope through both the web interface and API.

<div align="center">

<table>
<tr>
<td width="50%" valign="top" align="center">

### 🚕 Fleet Management

Fleet and vehicle management  
Scope-based access control  
Vehicle filtering  
CSV / JSON export

</td>
<td width="50%" valign="top" align="center">

### 🗺️ Trip Tracking

GPS tracks  
GPX import  
PostGIS  
Geospatial visualization

</td>
</tr>

<tr>
<td width="50%" valign="top" align="center">

### ⚡ Event-Driven

Apache Kafka  
Asynchronous services  
Event-based communication

</td>
<td width="50%" valign="top" align="center">

### 📊 Observability

Prometheus  
Grafana  
Alertmanager  
Telegram alerts

</td>
</tr>
</table>

</div>

## Architecture

TaxiTracker follows a modular microservice architecture built around Django,
Apache Kafka, PostgreSQL/PostGIS, and an observability stack.

<div align="center">

<img src="screenshots/architecture.svg"
     alt="TaxiTracker Architecture"
     width="900">

</div>

**Fleet dashboard**

![Fleet dashboard](/screenshots/fleet-dashboard.png)

**Car dashboard**

![Car dashboard](/screenshots/car-dashboard.png)

---

### Vehicle and Trip Tracking

Each vehicle has a detailed view containing its associated trips.

The trip interface provides:

- Trip history for a specific vehicle
- Sorting and filtering of trip data
- Geospatial visualization of trips on a map
- GPX file import
- Storage of imported tracks in the database

GPX imports can be used to add additional trip records to the system.

**Imported trip**

![Vehicle trip with GPS track](/screenshots/trip-map.png)

---

### REST API

The API provides a controlled subset of the functionality available through the web interface.

It is primarily focused on retrieving fleet and vehicle information and exposing operational data to external systems.

Examples include:

- Vehicle details
- Fleet information
- Vehicles available to a manager
- Trip coordinates
- Trip data

Example API responses:

**Trip coordinates API**

![Trip coordinates API](/screenshots/api-coordinates.png)

**Vehicle details API**

![Vehicle details API](/screenshots/api-vehicle.png)

**Manager vehicles API**

![Manager vehicles API](/screenshots/api-vehicles.png)

**Vehicle trip API**

![Manager vehicles API](/screenshots/api-trip.png)

Access to API resources is restricted according to the manager's assigned fleet scope.

---

## Telegram Bot

TaxiTracker also includes a Telegram bot for manager notifications and reporting.

The bot provides:

- Notifications about new vehicle trips within the manager's area of responsibility
- Fleet-specific notifications
- Vehicle-specific reports
- Mileage reports for configurable time periods

This allows managers to receive operational information without constantly monitoring the web application.

**TG-bot reports**

![Telegram Bot](/screenshots/tg-bot.png)

---


### Microservices

The project contains two supporting microservices.

#### Notification Service

Responsible for notifying authenticated managers through Telegram about CRUD operations occurring within their assigned scope.

#### Track Generator Service

Responsible for generating trip tracks used by the main application.

Both services communicate with the main system and each other through **Apache Kafka**, providing asynchronous communication between components.

<div align="center">

<img src="screenshots/workflow.svg"
     alt="TaxiTracker Data Flow"
     width="900">

</div>

---

## Technology Stack

<div align="center">

<img src="screenshots/engineering.svg"
     alt="TaxiTracker Engineering Stack"
     width="900">

</div>

### Backend

- Python
- Django
- Django REST Framework
- PostgreSQL
- PostGIS

### Caching and performance

- Redis
- Cachalot
- Django ORM query optimization
- `select_related`
- `prefetch_related`

The application was optimized to eliminate common **N+1 query problems** by using appropriate ORM prefetching strategies.

### Messaging

- Apache Kafka

Kafka is used for asynchronous communication between the main application and supporting microservices.

### Monitoring and observability

- Prometheus
- Grafana
- OpenTelemetry
- Logstash
- Kibana
- GoAccess

Prometheus and Grafana are used for application and infrastructure monitoring.

The project also includes Prometheus alerting rules and custom Grafana dashboards.

Additional observability tools such as Logstash, Kibana, and GoAccess were evaluated during development.

### Performance testing

The application was tested under load using **Locust** and multiple Nginx workers to evaluate application behavior under concurrent requests.

---

## Monitoring

<div align="center">

<img src="screenshots/monitoring.svg"
     alt="TaxiTracker Observability"
     width="900">

</div>

The project exposes application metrics through `django-prometheus`.

Prometheus collects the metrics and Grafana provides dashboards for visualization and monitoring.

Prometheus metrics:

http://localhost:8000/prometheus/metrics

The monitoring stack allows tracking of:

- HTTP request metrics
- Database activity
- Application errors
- Request latency
- Database query performance
- Python runtime metrics
- Django application metrics

Example Grafana dashboard:

**Grafana dashboard**

![Grafana dashboard](/screenshots/grafana-dashboard.png)

Prometheus alerting rules are generated as part of the project's monitoring configuration.

---

## Data Import and Export

TaxiTracker supports data exchange with external fleet management systems.

Fleet data can be exported in:

- CSV
- JSON

The exported datasets contain the fleet and related entities required for further processing or importing into other systems.

GPX files can also be imported to add additional trip tracks to the database.

---

## Access Control

Manager access is scoped to the fleets assigned to them.

The same access restrictions are applied to both:

- Web UI
- REST API (JWT)

This prevents managers from accessing vehicles, trips, or fleet data outside their assigned area of responsibility.

---

## Deployment

The project includes scripts for automated deployment and updates.

### Initial deployment

```bash
./deploy.sh
```

Deployment script:

https://github.com/Voldek404/TaxiTracker/blob/main/TaxiTracker/deploy.sh

### Updating an existing deployment

```bash
./deploy_update.sh
```

Update script:

https://github.com/Voldek404/TaxiTracker/blob/main/TaxiTracker/deploy_update.sh

---

## Local Development

Clone the repository:

```bash
git clone https://github.com/Voldek404/TaxiTracker.git
cd TaxiTracker

cp .env.example .env

docker compose up --build
```

Install the required dependencies and configure the environment variables according to the project configuration.

The project can then be started locally using the provided deployment/development configuration.

For the complete setup, see the repository:

https://github.com/Voldek404/TaxiTracker

---

## Engineering Highlights

The project demonstrates practical implementation of several backend engineering concepts:

- Onion Architecture
- REST API design
- Role- and scope-based access control
- PostgreSQL/PostGIS
- Redis caching
- ORM query optimization
- N+1 query elimination
- Asynchronous communication with Kafka
- Microservice architecture
- Prometheus and Grafana monitoring
- Application observability
- Load testing with Locust
- Nginx-based deployment
- Automated deployment and update scripts
- Geospatial data processing
- CSV/JSON data exchange
- GPX track processing

---

## Project Status

TaxiTracker is a working backend-oriented project combining fleet management, geospatial tracking, reporting, asynchronous processing, monitoring, and deployment automation.

The project is primarily intended to demonstrate backend engineering, architecture, and infrastructure skills in a practical production-oriented application.


