# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
OpsPilot Seed Data Script
Populates database with realistic sample data for all features.

Usage:
    python seed_data.py          # Add data (non-destructive)
    python seed_data.py --reset  # Clear and re-seed
"""
import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# Load .env before imports
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup engine same way the app does
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"
if USE_SQLITE:
    DATABASE_URL = "sqlite:///./opspilot.db"
    connect_args = {"check_same_thread": False}
else:
    u = os.getenv("POSTGRES_USER","postgres")
    pw = os.getenv("POSTGRES_PASSWORD","postgres")
    db = os.getenv("POSTGRES_DB","opspilot")
    host = os.getenv("POSTGRES_HOST","localhost")
    port = os.getenv("POSTGRES_PORT","5432")
    DATABASE_URL = f"postgresql://{u}:{pw}@{host}:{port}/{db}"
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

from app.database.models import Base, Service, Log, Incident, Metric
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)
db = Session()

# ── Reset ────────────────────────────────────────────────────────────────────
if "--reset" in sys.argv:
    print("[RESET] Clearing existing data...")
    db.query(Metric).delete()
    db.query(Log).delete()
    db.query(Incident).delete()
    db.query(Service).delete()
    db.commit()
    print("[OK] Cleared.")

# ── Services ─────────────────────────────────────────────────────────────────
SERVICES = [
    ("api-gateway", "Main API entry point", "UP"),
    ("auth-service", "Authentication and authorization", "UP"),
    ("db-sync", "Database synchronization service", "DEGRADED"),
    ("payment-service", "Payment processing", "UP"),
    ("notification-svc", "Email/push notifications", "UP"),
    ("ml-inference", "ML model serving endpoint", "DEGRADED"),
    ("cache-layer", "Redis cache management", "DOWN"),
    ("data-pipeline", "ETL and streaming pipeline", "UP"),
]

services = {}
for name, desc, status in SERVICES:
    existing = db.query(Service).filter(Service.name == name).first()
    if not existing:
        svc = Service(name=name, description=desc, status=status, last_seen=datetime.utcnow())
        db.add(svc)
        db.flush()
        services[name] = svc
        print(f"  [+] Service: {name}")
    else:
        services[name] = existing

db.commit()

# ── Log Templates ─────────────────────────────────────────────────────────────
LOG_TEMPLATES = {
    "api-gateway": [
        ("INFO",    "Request processed successfully in {t}ms [GET /api/v2/users]"),
        ("INFO",    "Health check passed — all upstream services responding"),
        ("WARNING", "Rate limit approaching for client IP 192.168.1.{n} ({r}% of quota used)"),
        ("ERROR",   "Upstream timeout after {t}ms — connection to auth-service failed"),
        ("ERROR",   "502 Bad Gateway — service mesh routing error on /api/checkout"),
        ("INFO",    "TLS certificate renewal successful, valid until 2027-03-{d}"),
    ],
    "auth-service": [
        ("INFO",    "JWT token issued for user_id={n}, expires in 3600s"),
        ("WARNING", "Failed login attempt for email admin@company.com ({r} attempts)"),
        ("ERROR",   "Redis connection timeout — session cache unavailable for {t}ms"),
        ("CRITICAL","OAuth2 provider Google returned 503 — fallback auth activated"),
        ("INFO",    "MFA verification successful for user_id={n}"),
        ("WARNING", "Suspicious login from new geo-location: {ip}"),
    ],
    "db-sync": [
        ("WARNING", "Replication lag detected: {t}ms exceeds 200ms threshold"),
        ("ERROR",   "Write conflict on table `orders` — rollback triggered"),
        ("INFO",    "Checkpoint completed — {n} transactions written to WAL"),
        ("CRITICAL","Primary database unreachable — failover to replica initiated"),
        ("WARNING", "Slow query detected: {t}ms — SELECT * FROM metrics WHERE timestamp > ..."),
        ("ERROR",   "Connection pool exhausted: {n}/{n} connections in use"),
    ],
    "payment-service": [
        ("INFO",    "Payment processed: ${r}.{n} via Stripe [txn_id=ch_{n}{n}]"),
        ("ERROR",   "Stripe webhook signature validation failed — payload rejected"),
        ("WARNING", "Payment retry #{n} for order_{n} — previous attempt declined"),
        ("CRITICAL","PCI compliance check failed — audit log gap detected"),
        ("INFO",    "Refund processed: $50.00 for order_id={n}"),
        ("ERROR",   "Idempotency key collision — duplicate payment request blocked"),
    ],
    "notification-svc": [
        ("INFO",    "Email delivered to user_{n}@domain.com in {t}ms"),
        ("WARNING", "Email bounce rate at {r}% — approaching SendGrid limit"),
        ("ERROR",   "Push notification delivery failed for device_token={n}"),
        ("INFO",    "SMS sent via Twilio: +1-555-{n}{n}{n}-{n}{n}{n}{n}"),
        ("WARNING", "Notification queue depth: {n} messages — processing delayed"),
    ],
    "ml-inference": [
        ("INFO",    "Model prediction completed in {t}ms [confidence: 0.{r}]"),
        ("WARNING", "GPU memory usage at {r}% — may degrade inference speed"),
        ("ERROR",   "CUDA out of memory error — model fallback to CPU inference"),
        ("INFO",    "Model v2.{n}.0 loaded successfully ({t}MB VRAM)"),
        ("WARNING", "Inference latency spike: p99={t}ms exceeds SLA of 200ms"),
    ],
    "cache-layer": [
        ("CRITICAL","Redis primary node unreachable — cluster degraded"),
        ("ERROR",   "Cache miss rate at {r}% — possible cache invalidation storm"),
        ("ERROR",   "Memory eviction policy triggered — {n}k keys evicted (LRU)"),
        ("WARNING", "Redis replication factor dropped to 1 — durability at risk"),
        ("CRITICAL","AOF file corruption detected — initiating emergency backup"),
    ],
    "data-pipeline": [
        ("INFO",    "Batch job completed: {n} records processed in {t}s"),
        ("WARNING", "Kafka consumer lag: {n} messages behind — partition 3"),
        ("ERROR",   "Schema registry mismatch — pipeline stalled on topic events.v2"),
        ("INFO",    "Stream checkpoint saved at offset {n}"),
        ("WARNING", "Dead letter queue depth: {n} failed messages pending review"),
    ],
}

def rnd(template):
    return template.format(
        t=random.randint(50, 2000),
        n=random.randint(100, 9999),
        r=random.randint(1, 99),
        d=random.randint(1, 28),
        ip=f"203.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
    )

# Seed 70 logs over the past 6 hours
now = datetime.utcnow()
if db.query(Log).count() < 20:
    print("\n[LOGS] Seeding logs...")
    count = 0
    for i in range(70):
        svc_name = random.choice(list(LOG_TEMPLATES.keys()))
        level, tmpl = random.choice(LOG_TEMPLATES[svc_name])
        svc = services[svc_name]
        mins_ago = random.randint(0, 360)
        log = Log(
            service_id=svc.id,
            level=level,
            message=rnd(tmpl),
            source="seed",
            timestamp=now - timedelta(minutes=mins_ago),
            severity_score=round(random.uniform(0.1, 0.99), 3),
            processed=True,
        )
        db.add(log)
        count += 1
    db.commit()
    print(f"  [+] {count} logs seeded")
else:
    print("  [=] Logs already exist -- skipping")

# ── Incidents ─────────────────────────────────────────────────────────────────
INCIDENTS = [
    {
        "title": "Cache Layer Complete Outage",
        "description": "Redis primary node is unreachable causing 100% cache miss rate across all services. Auth sessions and API rate limits are affected.",
        "severity": "CRITICAL",
        "status": "OPEN",
        "root_cause": "Redis cluster lost quorum after unexpected memory OOM kill on primary node.",
        "remediation_steps": "1. Promote replica to primary\n2. Increase memory limits to 8GB\n3. Enable Redis Sentinel for automatic failover\n4. Backfill critical session data from PostgreSQL"
    },
    {
        "title": "Database Replication Lag Spike",
        "description": "db-sync service reporting replication lag of 850ms, well above the 200ms SLA threshold.",
        "severity": "HIGH",
        "status": "ACKNOWLEDGED",
        "root_cause": "Bulk INSERT operation on orders table causing WAL write amplification.",
        "remediation_steps": "1. Pause non-critical batch jobs\n2. Tune WAL buffer sizes\n3. Add read replica for analytics queries"
    },
    {
        "title": "ML Inference GPU Memory Exhaustion",
        "description": "GPU memory at 97% — inference service falling back to CPU causing 10x latency increase.",
        "severity": "HIGH",
        "status": "OPEN",
        "root_cause": "Model v2.4.0 has a memory leak in attention layer during concurrent batch requests.",
        "remediation_steps": "1. Roll back to model v2.3.0\n2. Limit concurrent inference requests to 4\n3. Implement proper tensor cleanup\n4. Add GPU memory alerting at 80% threshold"
    },
    {
        "title": "Payment Service Webhook Failures",
        "description": "Stripe webhooks failing signature validation — 34 payment confirmations lost in the last hour.",
        "severity": "CRITICAL",
        "status": "OPEN",
        "root_cause": "Webhook secret key was rotated in Stripe dashboard without updating the service config.",
        "remediation_steps": "1. Update STRIPE_WEBHOOK_SECRET env var to new key\n2. Replay failed webhook events from Stripe dashboard\n3. Add webhook secret rotation monitoring"
    },
    {
        "title": "Auth Service Rate Limit Alerts",
        "description": "Multiple brute force login attempts detected from 3 IP ranges — 847 failed attempts in 10 minutes.",
        "severity": "MEDIUM",
        "status": "RESOLVED",
        "root_cause": "Credential stuffing attack targeting admin accounts.",
        "remediation_steps": "1. Temporarily block offending IP ranges via WAF\n2. Force MFA for all admin accounts\n3. Enable CAPTCHA after 3 failed attempts\n4. Notify affected users"
    },
    {
        "title": "Notification Queue Backlog",
        "description": "Notification service queue depth at 12,483 messages — emails delayed by up to 45 minutes.",
        "severity": "MEDIUM",
        "status": "ACKNOWLEDGED",
        "root_cause": "SendGrid API rate limit hit due to marketing campaign sending spike.",
        "remediation_steps": "1. Pause low-priority notifications\n2. Upgrade SendGrid plan or add secondary SMTP provider\n3. Implement priority-based queue processing"
    },
]

if db.query(Incident).count() < 3:
    print("\n[INCIDENTS] Seeding incidents...")
    for i, inc_data in enumerate(INCIDENTS):
        inc = Incident(
            title=inc_data["title"],
            description=inc_data["description"],
            severity=inc_data["severity"],
            status=inc_data["status"],
            root_cause=inc_data.get("root_cause"),
            remediation_steps=inc_data.get("remediation_steps"),
            created_at=now - timedelta(hours=random.randint(1, 24)),
            updated_at=now - timedelta(minutes=random.randint(5, 120)),
        )
        db.add(inc)
    db.commit()
    print(f"  [+] {len(INCIDENTS)} incidents seeded")
else:
    print("  [=] Incidents already exist -- skipping")

# ── Metrics ───────────────────────────────────────────────────────────────────
METRIC_PROFILES = {
    "api-gateway":       {"cpu": (30, 60),  "mem": (40, 65),  "req": (200, 800), "err": (0.1, 2.0),  "resp": (50, 200)},
    "auth-service":      {"cpu": (20, 45),  "mem": (35, 60),  "req": (50,  200), "err": (0.5, 5.0),  "resp": (80, 300)},
    "db-sync":           {"cpu": (50, 85),  "mem": (60, 90),  "req": (10,  50),  "err": (1.0, 8.0),  "resp": (100,900)},
    "payment-service":   {"cpu": (25, 50),  "mem": (30, 55),  "req": (20,  100), "err": (0.1, 3.0),  "resp": (200,500)},
    "notification-svc":  {"cpu": (15, 35),  "mem": (25, 50),  "req": (100, 500), "err": (0.5, 4.0),  "resp": (60, 200)},
    "ml-inference":      {"cpu": (70, 98),  "mem": (80, 97),  "req": (5,   30),  "err": (1.0, 10.0), "resp": (300,1200)},
    "cache-layer":       {"cpu": (85, 99),  "mem": (90, 99),  "req": (500, 2000),"err": (10.0, 50.0),"resp": (1,  10)},
    "data-pipeline":     {"cpu": (40, 75),  "mem": (55, 80),  "req": (30,  150), "err": (0.5, 3.0),  "resp": (150,600)},
}

if db.query(Metric).count() < 50:
    print("\n[METRICS] Seeding metrics...")
    metric_count = 0
    for svc_name, profile in METRIC_PROFILES.items():
        svc = services.get(svc_name)
        if not svc:
            continue
        for i in range(15):  # 15 data points over past 2 hours
            ts = now - timedelta(minutes=i * 8)
            for metric_name, (lo, hi) in [
                ("cpu_usage",    profile["cpu"]),
                ("memory_usage", profile["mem"]),
                ("request_rate", profile["req"]),
                ("error_rate",   profile["err"]),
                ("response_time",profile["resp"]),
            ]:
                val = round(random.uniform(lo, hi), 2)
                m = Metric(service_id=svc.id, name=metric_name, value=val,
                           unit={"cpu_usage":"%","memory_usage":"%","request_rate":"rps","error_rate":"%","response_time":"ms"}[metric_name],
                           timestamp=ts)
                db.add(m)
                metric_count += 1
    db.commit()
    print(f"  [+] {metric_count} metric data points seeded")
else:
    print("  [=] Metrics already exist -- skipping")

db.close()
print("\n[DONE] Seed complete! Open http://localhost:8000 to see the data.\n")
