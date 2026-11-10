# Smart People Analytics — AI Chat Analyst

Sistem analitik cerdas pergerakan orang dan estimasi okupansi ruangan berbasis **AI Chat Analyst** dan Computer Vision untuk proyek perkuliahan / Tugas Akhir (TA) **Fajar**.

Sistem ini memisahkan tiga tanggung jawab utama:
1. **Database (SQLite)**: Menyimpan rekaman kejadian line crossing (`IN` dan `OUT`).
2. **Backend (Python + Flask)**: Menghitung statistik numerik yang benar dan tervalidasi tanpa risiko halusinasi.
3. **AI Chat Analyst**: Menjelaskan temuan analitik kepada pengguna menggunakan bahasa Indonesia melalui pola *Tool Calling / Function Calling*.

---

## 🚀 Fitur Utama

### 1. Dashboard Analitik (`/dashboard` atau `/`)
- **Kartu Metrik Kunci**:
  - Total orang masuk (**IN**)
  - Total orang keluar (**OUT**)
  - Arus bersih (**Net Flow**)
  - Estimasi okupansi orang di dalam area
  - Jam paling ramai (**Peak Hour**) & jumlah orangnya
  - Indikator tren perbandingan terhadap hari sebelumnya
- **Grafik Interaktif (Chart.js)**:
  - Grafik distribusi pergerakan per jam (24 jam)
  - Kurva akumulasi okupansi ruangan
  - Tren mingguan (7 hari terakhir)
- **Live Event Simulation Strip**:
  - Tombol instan untuk simulasi 1 orang masuk (`+1 IN`) atau 1 orang keluar (`+1 OUT`).

### 2. AI Chat Analyst (`/chat`)
- Percakapan interaktif dalam bahasa Indonesia.
- **Pola Tool Calling / Function Calling**:
  - `get_summary`: Rekap kejadian IN/OUT dan arus bersih.
  - `get_hourly_counts`: Rekap 24 jam per jam.
  - `compare_periods`: Perbandingan dua periode dan persentase perubahan $\left(\frac{N_{baru} - N_{lama}}{N_{lama}} \times 100\%\right)$.
  - `get_peak_period`: Pencarian jam tersibuk/teramai.
  - `get_occupancy_estimate`: Estimasi jumlah orang yang masih berada di dalam area.
- **Bukti Analitik (Evidence Card)**:
  - Setiap respons AI dilengkapi kartu bukti yang dapat diperluas (*accordion*), menampilkan fungsi yang dipanggil, argumen, dan hasil kalkulasi SQLite riil bertanda `Tervalidasi Database`.
- **Dukungan Multi-Engine**:
  - **Built-in Deterministic Analyst**: Bekerja 100% offline, cepat, tanpa biaya/kuota API.
  - **Google Gemini & OpenAI**: Didukung penuh bila pengguna memasukkan API key di `.env` atau menu modal Pengaturan AI.
- **Tombol Pertanyaan Contoh (Prompt Chips)**:
  - *"Berapa jumlah orang yang masuk hari ini?"*
  - *"Jam berapa paling ramai hari ini?"*
  - *"Bandingkan jumlah IN hari ini dan kemarin."*
  - *"Berapa selisih jumlah orang masuk dan keluar?"*
  - *"Berapa persen perubahan jumlah pengunjung dibanding kemarin?"*
  - *"Berapa estimasi orang di dalam area saat ini?"*

### 3. Riwayat Data (`/history`)
- Tabel audit log kejadian line-crossing lengkap:
  - ID kejadian
  - Waktu kejadian (`occurred_at`)
  - Arah pergerakan (`IN` / `OUT`) dengan badge visual
  - Track ID (`TRK-xxxx`)
  - Confidence score model
  - Label sumber data (`SIMULATED` vs `YOLO`)
  - ID Kamera (`CAM-01`)
- Filter berdasarkan rentang tanggal, arah, dan sumber data.
- **Ekspor CSV**: Mengunduh dataset terfilter langsung ke file CSV.

---

## 📂 Struktur Direktori Proyek

```
KapitaSelekta/
│
├── app.py                      # Inisialisasi Flask, auto-seed database & routing
├── config.py                   # Konfigurasi aplikasi & environment
├── models.py                   # Skema SQLite, indexing, & fungsi data access
├── requirements.txt            # Dependensi Python
├── .env                        # Konfigurasi environment lokal
├── .env.example                # Template variabel environment
├── .gitignore                  # Berkas yang dikecualikan dari Git
├── README.md                   # Dokumentasi lengkap proyek
│
├── services/
│   ├── __init__.py
│   ├── analytics_service.py    # Logika perhitungan statistik (rekap, peak, compare, okupansi)
│   ├── ai_service.py           # Engine AI Analyst, Tool Calling, & intent matching
│   └── simulator.py            # Generator data simulasi 14 hari & live event injection
│
├── routes/
│   ├── __init__.py
│   ├── dashboard.py            # Route halaman & API dashboard (/api/dashboard/summary, dll)
│   ├── events.py               # Route riwayat data & ekspor CSV (/api/events/export, dll)
│   └── chat.py                 # Route halaman & API percakapan AI (/api/chat, dll)
│
├── templates/
│   ├── base.html               # Layout dasar glassmorphism, sidebar nav, modal simulasi & setting
│   ├── dashboard.html          # Halaman Dashboard analitik & chart
│   ├── chat.html               # Halaman AI Chat Analyst
│   └── history.html            # Halaman Riwayat Data kejadian & filter
│
├── static/
│   ├── css/
│   │   └── style.css           # Desain modern dark glassmorphism computer vision
│   └── js/
│       ├── dashboard.js        # Logika visualisasi Chart.js & counter animasi
│       ├── chat.js             # Logika percakapan chat, chips prompt, & bukti analitik
│       └── history.js          # Logika tabel riwayat data, paginasi, & ekspor CSV
│
├── tests/
│   ├── __init__.py
│   └── test_analytics.py       # Pengujian otomatis pytest (10 skenario pengujian)
│
└── instance/
    └── people_analytics.db     # Berkas database SQLite lokal
```

---

## 🛠️ Panduan Menjalankan Aplikasi

### 1. Prasyarat
- Python 3.10+ (atau gunakan launcher `py`)

### 2. Instalasi Dependensi
```bash
py -m pip install -r requirements.txt
```

### 3. Menjalankan Aplikasi
```bash
py app.py
```
Aplikasi akan aktif pada URL:
👉 **http://127.0.0.1:5000**

> **Catatan Seeding Otomatis:**
> Saat pertama kali dijalankan, sistem secara otomatis mendeteksi jika database kosong dan mengisinya dengan dataset simulasi selama 14 hari (mengikuti kurva aktivitas harian realistis gedung kampus).

### 4. Menjalankan Pengujian Otomatis (Pytest)
```bash
py -m pytest tests/
```
Seluruh 10 skenario pengujian mencakup:
- Rekapitulasi jumlah IN, OUT, dan okupansi
- Pengelompokan per jam 24 jam
- Deteksi jam puncak (Peak Hour)
- Perbandingan periode dan persentase perubahan
- Penanganan matematis khusus bila pembagi bernilai nol ($N_{lama} = 0$)
- Deteksi anomali okupansi negatif
- Pengujian inferensi AI Chat Analyst untuk tiap intent pertanyaan
- Penolakan pertanyaan di luar cakupan (*out-of-scope*)
- Penanganan tanggal tanpa data

---

## 🔌 API Endpoints Reference

| Endpoint | Metode | Deskripsi |
|---|---|---|
| `/api/health` | GET | Status kesiapan sistem dan total data tersimpan |
| `/api/dashboard/summary` | GET | Ringkasan metrik utama, peak hour, dan perbandingan hari |
| `/api/analytics/hourly` | GET | Data 24 jam untuk grafik aktivitas per jam |
| `/api/analytics/daily` | GET | Rekapitulasi tren mingguan |
| `/api/events` | GET | Data riwayat kejadian dengan paginasi dan filter |
| `/api/events/export` | GET | Unduh data kejadian dalam format `.csv` |
| `/api/events/simulate` | POST | Menyuntikkan event instan (`action: 'single'`) atau bulk (`action: 'generate'`) |
| `/api/chat` | POST | Memproses pesan chat pengguna dan mengembalikan jawaban AI + evidence |
| `/api/chat/sessions` | GET / POST | Mengelola daftar sesi percakapan |
| `/api/chat/sessions/<id>` | GET / DELETE | Mengambil riwayat percakapan sesi atau menghapus sesi |

---

## 🎓 Kesiapan Integrasi ke Tugas Akhir (YOLO / IoT)

Saat modul YOLO dan object tracking line crossing pada TA selesai dibangun, backend ini dapat langsung menerima data dengan memanggil endpoint internal atau fungsi:
```python
from models import insert_event

insert_event(
    occurred_at=waktu_kejadian,
    direction="IN",       # atau "OUT"
    track_id="TRK-0012",
    confidence=0.94,
    source="YOLO",        # Penanda data riil kamera
    camera_id="CAM-01"
)
```
Seluruh logika analitik, dashboard, dan AI Chat Analyst akan langsung memproses data kamera tersebut tanpa perlu mengubah arsitektur sistem.
