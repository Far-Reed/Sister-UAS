# Event Aggregator Service

Event Aggregator adalah layanan backend sederhana berbasis **FastAPI** dan **PostgreSQL** yang berfungsi untuk menerima event, melakukan deduplikasi berdasarkan `event_id`, serta menampilkan statistik agregasi event.

---

## 📦 Teknologi yang Digunakan

* Python 3.11
* FastAPI
* PostgreSQL
* asyncpg
* Docker & Docker Compose

---

## 🚀 Cara Build & Menjalankan Aplikasi

### 1. Pastikan Prasyarat

* Docker
* Docker Compose

### 2. Jalankan Semua Service

Dari root project:

```bash
docker compose up --build
```

Service yang akan berjalan:

* **aggregator** → API FastAPI (`http://localhost:8080`)
* **storage** → PostgreSQL
* **broker** → Redis (jika digunakan)

---

## 🏗️ Arsitektur Sistem (Singkat)

Sistem terdiri dari beberapa komponen utama:

* **Client**

  * Mengirim event menggunakan HTTP (curl / Postman)
* **Aggregator Service (FastAPI)**

  * Menerima event
  * Melakukan deduplikasi
  * Memperbarui statistik agregasi
* **PostgreSQL**

  * Menyimpan event (`processed_events`)
  * Menyimpan statistik (`agg_stats`)

Alur singkat:

```
Client → /ingest → Aggregator → PostgreSQL
Client → /stats  → Aggregator → PostgreSQL
```

---

## 🗄️ Desain Database (Ringkas)

### Tabel `processed_events`

Menyimpan semua event unik.

Kolom utama:

* `event_id` (unique)
* `topic`
* `source`
* `payload` (JSONB)
* `status`
* `received_at`

### Tabel `agg_stats`

Menyimpan statistik agregasi global.

Kolom:

* `received`
* `unique_processed`
* `duplicate_dropped`

---

## 🔌 Endpoint API

### 1️⃣ POST `/ingest`

Digunakan untuk mengirim event.

**Request Body:**

```json
{
  "topic": "test",
  "event_id": "evt-001",
  "source": "cli",
  "payload": {
    "value": 123
  }
}
```

**Response (event baru):**

```json
{
  "status": "accepted",
  "event_id": "evt-001"
}
```

**Response (event duplikat):**

```json
{
  "detail": "duplicate event"
}
```

---

### 2️⃣ GET `/stats`

Menampilkan statistik agregasi event.

**Response:**

```json
{
  "received": 2,
  "unique_processed": 1,
  "duplicate_dropped": 1
}
```

---

## 🧪 Cara Menjalankan Test

Pengujian dilakukan secara manual menggunakan `curl`.

### Test 1 – Event Baru

```bash
curl -H "Content-Type: application/json" \
http://localhost:8080/ingest \
-d "{\"topic\":\"test\",\"event_id\":\"evt-TEST-001\",\"source\":\"cli\",\"payload\":{\"value\":1}}"
```

**Hasil:** `accepted`

---

### Test 2 – Event Duplikat

```bash
curl -H "Content-Type: application/json" \
http://localhost:8080/ingest \
-d "{\"topic\":\"test\",\"event_id\":\"evt-TEST-001\",\"source\":\"cli\",\"payload\":{\"value\":1}}"
```

**Hasil:** `duplicate event`

---

### Test 3 – Cek Statistik

```bash
curl http://localhost:8080/stats
```

**Hasil yang Diharapkan:**

```json
{
  "received": 2,
  "unique_processed": 1,
  "duplicate_dropped": 1
}
```

---
