# Laporan Event Aggregator System

**Nama:** Farizi Fattah  
**NIM:** 11221009  
**Kelas:** B

---

## 1. Pendahuluan

Pada era sistem terdistribusi, data sering dikirim dalam bentuk *event* dari berbagai sumber secara terus-menerus. Salah satu permasalahan utama dalam pengolahan *event* adalah duplikasi data, yang dapat menyebabkan perhitungan tidak akurat dan pemborosan sumber daya.

Oleh karena itu, pada tugas UAS ini dikembangkan sebuah **Event Aggregator System**, yaitu sistem backend yang bertugas menerima event, melakukan pencatatan, mendeteksi event duplikat, serta menyajikan statistik agregasi secara *real-time*. Sistem ini dirancang untuk berjalan dalam lingkungan terisolasi menggunakan **Docker**, sehingga mudah dijalankan, diuji, dan direproduksi.

### Tujuan Sistem

Sistem ini bertujuan untuk:

* Menerima event melalui REST API
* Mendeteksi dan menolak event duplikat
* Mencatat event yang valid ke dalam database
* Menghitung statistik jumlah event yang diterima, unik, dan duplikat
* Menyediakan endpoint untuk melihat hasil agregasi

---

## T1 (Bab 1) – Karakteristik Sistem Terdistribusi dan *Trade-off* Desain Publish–Subscribe Aggregator

Sistem terdistribusi dicirikan oleh komponen yang berjalan secara independen, berkomunikasi melalui jaringan, serta tidak memiliki *shared memory* maupun *global clock* (Tanenbaum & Van Steen, 2017). **Event Aggregator System** termasuk dalam kategori ini karena aggregator dan database berjalan pada container terpisah dan berkomunikasi melalui jaringan Docker Compose lokal.

Pemilihan pola **publish–subscribe (pub-sub)** memberikan keuntungan berupa *loose coupling* antara produsen event (*publisher/client*) dan konsumen (aggregator). Client tidak perlu mengetahui detail penyimpanan atau agregasi, cukup mengirim event ke endpoint *ingest*.

Trade-off utama dari pendekatan ini adalah meningkatnya kompleksitas dalam menjaga konsistensi data, terutama terkait duplikasi event dan *ordering*.

Dalam sistem ini, trade-off tersebut diatasi dengan pendekatan **deduplikasi berbasis `event_id` unik dan *idempotent processing***. Sistem tidak berusaha menjamin *exactly-once delivery* secara penuh, melainkan mengandalkan *at-least-once delivery* yang dikombinasikan dengan mekanisme deduplikasi di sisi konsumen. Pendekatan ini sejalan dengan praktik umum sistem terdistribusi yang lebih mengutamakan *availability* dan *scalability* dibanding konsistensi ketat (*CAP trade-off*).

---

## T2 (Bab 2) – Kapan Memilih Publish–Subscribe dibanding Client–Server

Arsitektur **publish–subscribe** lebih tepat digunakan ketika produsen data dan konsumen tidak ingin terikat secara langsung, baik dari sisi waktu maupun struktur sistem (Tanenbaum & Van Steen, 2017).

Pada **Event Aggregator System**, client hanya bertindak sebagai *publisher event*, sedangkan aggregator sebagai *subscriber logis* yang memproses dan menyimpan data.

Jika pendekatan *client–server* digunakan secara ketat, client akan bergantung pada status internal server, termasuk apakah event sebelumnya sudah diproses atau belum. Hal ini meningkatkan *coupling* dan memperbesar risiko kegagalan berantai.

Dengan pub-sub, event diperlakukan sebagai pesan independen yang dapat diterima ulang tanpa menimbulkan efek samping berbahaya. Dengan desain *idempotent consumer* pada aggregator, sistem tetap menghasilkan *state* yang konsisten meskipun terjadi pengiriman ulang.

Oleh karena itu, pub-sub dipilih karena lebih resilien terhadap *failure* dan lebih selaras dengan karakteristik sistem terdistribusi berskala besar.

---

## T3 (Bab 3) – At-least-once vs Exactly-once Delivery dan Peran Idempotent Consumer

* **At-least-once delivery** menjamin bahwa setiap event akan dikirim minimal satu kali, namun memungkinkan terjadinya duplikasi.
* **Exactly-once delivery** menjamin event diproses tepat satu kali, tetapi membutuhkan mekanisme koordinasi dan *state management* yang kompleks (Tanenbaum & Van Steen, 2017).

Event Aggregator System ini secara eksplisit memilih *at-least-once delivery* karena kesederhanaan desain dan ketahanan terhadap kegagalan.

Duplikasi event ditangani di sisi konsumen melalui *idempotent processing*, yaitu memastikan bahwa pemrosesan event yang sama tidak mengubah *state* sistem lebih dari satu kali.

Idempotensi dicapai dengan penggunaan `event_id` unik dan constraint **UNIQUE** pada database. Jika event yang sama dikirim ulang, database akan menolak penyimpanan ulang tanpa mengubah data yang sudah ada. Dengan demikian, meskipun delivery bersifat *at-least-once*, efek akhirnya bersifat *exactly-once* secara semantik.

---

## T4 (Bab 4) – Skema Penamaan Topic dan `event_id` untuk Deduplication

Penamaan merupakan aspek penting dalam sistem terdistribusi karena menjadi dasar identifikasi dan koordinasi antar komponen.

* **Topic** digunakan untuk mengelompokkan event berdasarkan domain atau jenis data.
* **`event_id`** berfungsi sebagai identitas unik setiap event.

Skema `event_id` harus bersifat *collision-resistant*. Implementasi yang disarankan adalah penggunaan **UUID v4** atau kombinasi *timestamp*, *source identifier*, dan *counter* lokal.

Constraint **UNIQUE** pada kolom `event_id` di tabel `processed_events` memastikan database menjadi *single source of truth* dalam mendeteksi duplikasi, bahkan dalam kondisi *concurrent writes* dan *crash recovery*.

---

## T5 (Bab 5) – Ordering Praktis: Timestamp dan Monotonic Counter

Karena tidak adanya *global clock*, sistem ini tidak memaksakan *strict ordering*. Sebagai gantinya, digunakan *ordering praktis* berbasis `received_at`.

Timestamp ini mencerminkan urutan pemrosesan lokal di aggregator, bukan urutan kejadian global. Untuk meningkatkan ketertelusuran, timestamp dapat dikombinasikan dengan *monotonic counter* internal.

Meskipun memungkinkan terjadinya *out-of-order processing*, pendekatan ini dapat diterima karena sistem berfokus pada agregasi statistik, bukan rekonstruksi urutan kejadian absolut.

---

## T6 (Bab 6) – Failure Modes dan Strategi Mitigasi

Event Aggregator System dirancang dengan asumsi bahwa kegagalan adalah hal yang normal (*failure as a norm*).

Strategi mitigasi:

* Duplikasi event akibat retry ditangani dengan deduplikasi berbasis `event_id`.
* Crash aggregator tidak menyebabkan kehilangan data karena state disimpan di PostgreSQL menggunakan Docker volume.
* Retry dengan *backoff* dapat diterapkan di sisi client tanpa risiko *double counting* karena consumer bersifat idempotent.

---

## T7 (Bab 7) – Eventual Consistency dan Peran Idempotency

Sistem ini menerapkan **eventual consistency**, di mana statistik agregasi akan mencapai kondisi konsisten setelah seluruh event diproses.

Idempotency dan deduplication memastikan bahwa meskipun event dikirim berulang kali, *state* akhir sistem tetap sama. Pendekatan ini sesuai untuk sistem agregasi yang tidak memerlukan *strong consistency*.

---

## T8 (Bab 8) – Desain Transaksi: ACID, Isolation, dan Lost Update

Transaksi dalam sistem mematuhi prinsip **ACID**:

* *Atomicity* dan *durability* dijamin oleh PostgreSQL
* *Consistency* dijaga melalui constraint
* *Isolation* cukup menggunakan level **READ COMMITTED**

Lost update dicegah dengan membiarkan database menangani konflik penulisan melalui constraint.

---

## T9 (Bab 9) – Kontrol Konkurensi: Unique Constraint dan Idempotent Write

Constraint **UNIQUE** pada `event_id` berfungsi sebagai mekanisme kontrol konkurensi implisit.

Jika dua worker mencoba menyimpan event yang sama secara bersamaan, hanya satu transaksi yang berhasil. Pola ini dikenal sebagai **idempotent write pattern** dan lebih andal dibanding *explicit locking* di level aplikasi.

---

## T10 (Bab 10–13) – Orkestrasi, Keamanan, Persistensi, dan Observability

* **Docker Compose** digunakan untuk orkestrasi service dalam jaringan lokal terisolasi
* **Docker Volume** menjamin persistensi data PostgreSQL
* **Observability** disediakan melalui logging dan endpoint `GET /stats`

---

## 2. Arsitektur Sistem

Sistem menggunakan arsitektur *service-based* dengan Docker Compose.

### Komponen Utama

#### Aggregator Service

* Dibangun menggunakan **FastAPI**
* Endpoint:

  * `POST /ingest`
  * `GET /stats`
* Bertugas melakukan validasi, deduplikasi, dan pembaruan statistik

#### Database Service (PostgreSQL)

* Menyimpan data event dan statistik agregasi
* Menjamin konsistensi melalui constraint

### Alur Sistem

1. Client mengirim event ke `POST /ingest`
2. Aggregator mencatat event masuk
3. Event disimpan atau ditolak berdasarkan deduplikasi
4. Statistik disimpan terpusat
5. Client mengambil statistik melalui `GET /stats`

---

## 3. Desain Database

### Tabel `processed_events`

| Kolom        | Tipe Data   | Keterangan     |
| ------------ | ----------- | -------------- |
| id           | bigint      | Primary key    |
| event_id     | text        | ID unik event  |
| topic        | text        | Topik event    |
| source       | text        | Sumber event   |
| payload      | jsonb       | Data event     |
| received_at  | timestamptz | Waktu diterima |
| processed_at | timestamptz | Waktu diproses |
| status       | text        | Status event   |

📌 `event_id` memiliki constraint **UNIQUE**.

### Tabel `agg_stats`

| Kolom             | Tipe Data   | Keterangan           |
| ----------------- | ----------- | -------------------- |
| id                | bigint      | Primary key          |
| received          | integer     | Total event diterima |
| unique_processed  | integer     | Event unik           |
| duplicate_dropped | integer     | Event duplikat       |
| uptime_start      | timestamptz | Waktu sistem mulai   |

---

## 4. Alur Proses Sistem

1. Client mengirim event JSON ke `POST /ingest`
2. Sistem mencatat event masuk
3. Database melakukan deduplikasi
4. Statistik diperbarui
5. Client mengambil data melalui `GET /stats`

---

## 5. Pengujian dan Hasil

### Skenario 1 – Event Baru

* Response: `accepted`
* `received` ↑
* `unique_processed` ↑

### Skenario 2 – Event Duplikat

* Response: `duplicate event`
* `received` ↑
* `duplicate_dropped` ↑

### Skenario 3 – Pemeriksaan Statistik

```json
{
  "received": 2,
  "unique_processed": 1,
  "duplicate_dropped": 1
}
```

---

## 6. Kesimpulan

Event Aggregator System berhasil:

* Menerima event melalui REST API
* Mendeteksi dan menolak event duplikat
* Menghitung statistik agregasi secara akurat
* Menyajikan data statistik melalui endpoint khusus



---

## Informasi Pengumpulan

- Link GitHub: https://github.com/Far-Reed/Sister-UAS  
- Link Video Demo (YouTube): https://youtu.be/XXXXXXXXXXX  
- Link 
---

