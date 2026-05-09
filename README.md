# Kalender Indonesia

Aplikasi kalender web responsif untuk menampilkan hari libur nasional dan cuti bersama Indonesia. Aplikasi ini berjalan dengan Python standard library, HTML, CSS, dan JavaScript tanpa dependency eksternal Python.

## Fitur

- Kalender bulanan responsif dengan navigasi bulan dan tombol kembali ke hari ini.
- Filter bulan dan tahun.
- Penanda Sabtu, Minggu, libur nasional, dan cuti bersama.
- Panel agenda bulanan dan ringkasan jumlah libur nasional/cuti bersama per tahun.
- Tema light dan dark dengan preferensi tersimpan di browser.
- Cache data hari libur di file JSON lokal untuk mode server lokal.
- Sinkronisasi data otomatis saat cache kosong atau sudah usang.
- Sinkronisasi background saat server lokal berjalan.
- Endpoint serverless dan cron sync untuk deployment Vercel.
- Script sync manual untuk memperbarui data tahun tertentu.

## Struktur Project

```text
.
|-- app/
|   |-- main.py                     # HTTP server lokal dan routing API lokal
|   |-- config.py                   # Konfigurasi path, provider, host, port, dan sync
|   |-- models.py                   # Model data hari libur
|   |-- vercel_adapter.py           # Helper API untuk runtime Vercel
|   |-- providers/
|   |   |-- tanggal_merah.py        # Client provider Tanggal Merah API
|   |-- services/
|   |   |-- holiday_service.py      # Logika cache, refresh, dan fallback
|   |-- storage/
|   |   |-- json_store.py           # Baca/tulis cache JSON lokal
|-- api/
|   |-- holidays.py                 # Endpoint Vercel: /api/holidays
|   |-- sync.py                     # Endpoint Vercel cron: /api/sync
|-- public/
|   |-- index.html                  # UI kalender
|   |-- static/
|   |   |-- css/styles.css
|   |   |-- js/app.js
|-- data/
|   |-- holidays/                   # Seed/cache data libur per tahun
|-- scripts/
|   |-- sync_holidays.py            # Script sync manual
|-- tests/
|   |-- test_holiday_service.py
|-- run.py
|-- requirements.txt
|-- vercel.json
```

## Menjalankan Aplikasi Lokal

Jalankan server lokal:

```powershell
python run.py
```

Buka:

```text
http://localhost:8000
```

Jika port 8000 sedang dipakai:

```powershell
python run.py --port 8080
```

Lalu buka:

```text
http://localhost:8080
```

## Flow Proses Aplikasi

Alur utama saat aplikasi dibuka:

```text
Browser
  -> memuat public/index.html, styles.css, dan app.js
  -> JavaScript menentukan bulan/tahun aktif
  -> JavaScript request GET /api/holidays?year=YYYY
  -> Backend mengambil data libur/cuti untuk tahun tersebut
  -> Backend mengirim JSON berisi items dan meta
  -> JavaScript merender kalender, agenda, ringkasan, dan status data
```

Alur backend saat berjalan lokal dengan `python run.py`:

```text
GET /api/holidays?year=YYYY
  -> validasi query year
  -> HolidayService membaca data/holidays/YYYY.json
  -> jika cache ada dan belum usang, data dikirim dengan cache_status=cached
  -> jika cache kosong/usang, provider Tanggal Merah API dipanggil
  -> jika provider berhasil, data disimpan ke data/holidays/YYYY.json dan dikirim dengan cache_status=fresh
  -> jika provider gagal tetapi cache lama tersedia, cache lama dikirim dengan cache_status=stale
  -> jika provider gagal dan cache tidak tersedia, API mengembalikan error 502
```

Alur sinkronisasi background lokal:

```text
Server start
  -> start_auto_sync berjalan jika KALENDER_AUTO_SYNC_ENABLED aktif
  -> setiap KALENDER_AUTO_SYNC_INTERVAL_HOURS jam
  -> sync tahun berjalan sampai KALENDER_AUTO_SYNC_YEARS_AHEAD tahun ke depan
  -> hasil sync disimpan sebagai file JSON lokal
```

Alur saat deployment Vercel:

```text
Browser
  -> memuat file statis dari public/
  -> request GET /api/holidays?year=YYYY
  -> api/holidays.py mencoba mengambil data terbaru dari provider
  -> jika provider gagal, runtime memakai seed data/holidays/YYYY.json bila tersedia
  -> Vercel cron memanggil GET /api/sync sesuai jadwal di vercel.json
```

Perbedaan penting:

- Mode lokal dapat menulis cache baru ke `data/holidays/`.
- Mode Vercel tidak mengandalkan penulisan cache lokal permanen; `data/holidays/` dipakai sebagai seed/fallback yang ikut dibundel saat deploy.
- Frontend tetap memakai endpoint yang sama, yaitu `/api/holidays?year=YYYY`.

## Endpoint

Endpoint lokal dari `app/main.py`:

```text
/                 Halaman kalender
/api/health       Cek server hidup
/api/years        Daftar tahun yang tersedia di cache lokal
/api/holidays     Data libur/cuti berdasarkan tahun
```

Endpoint Vercel dari folder `api/`:

```text
/api/holidays     Data libur/cuti berdasarkan tahun
/api/sync         Sync beberapa tahun untuk cron/manual trigger
```

Contoh:

```text
http://localhost:8000/api/holidays?year=2026
```

## Sinkronisasi Data

Provider default menggunakan Tanggal Merah API:

```text
https://tanggalmerah.upset.dev/api/holidays?year=YYYY
```

Backend lokal akan mengambil data dari provider saat data untuk sebuah tahun belum ada atau cache sudah melewati umur maksimum.

Konfigurasi sync otomatis di PowerShell:

```powershell
$env:KALENDER_AUTO_SYNC_ENABLED="1"
$env:KALENDER_AUTO_SYNC_INTERVAL_HOURS="24"
$env:KALENDER_AUTO_SYNC_YEARS_AHEAD="2"
```

Sync manual satu tahun:

```powershell
python scripts/sync_holidays.py --year 2027
```

Sync beberapa tahun:

```powershell
python scripts/sync_holidays.py --from-year 2026 --to-year 2028
```

## Konfigurasi

Konfigurasi dapat diubah lewat environment variable:

```text
KALENDER_HOST                    Host server lokal, default 127.0.0.1
KALENDER_PORT                    Port server lokal, default 8000
KALENDER_STATIC_DIR              Direktori file statis, default public/
KALENDER_DATA_DIR                Direktori cache JSON, default data/holidays/
KALENDER_PROVIDER_BASE_URL       Base URL provider data libur
KALENDER_SYNC_MAX_AGE_HOURS      Umur cache sebelum refresh, default 168
KALENDER_HTTP_TIMEOUT_SECONDS    Timeout request provider, default 12
KALENDER_AUTO_SYNC_ENABLED       Aktif/nonaktif auto sync lokal, default 1
KALENDER_AUTO_SYNC_INTERVAL_HOURS Interval auto sync lokal, default 24
KALENDER_AUTO_SYNC_YEARS_AHEAD   Jumlah tahun ke depan untuk auto sync, default 2
CRON_SECRET                      Token Bearer opsional untuk /api/sync di Vercel
```

## Format Data

Setiap file `data/holidays/YYYY.json` menyimpan:

```json
{
  "year": 2026,
  "items": [
    {
      "date": "2026-01-01",
      "name": "Tahun Baru 2026 Masehi",
      "type": "libur_nasional",
      "day": "Kamis",
      "source": "Tanggal Merah API",
      "source_url": "https://tanggalmerah.upset.dev/api/holidays?year=2026"
    }
  ],
  "meta": {
    "source": "Tanggal Merah API",
    "source_url": "https://tanggalmerah.upset.dev/api/holidays?year=2026",
    "synced_at": "2026-05-08T15:54:00.907634+00:00",
    "item_count": 25,
    "cache_status": "fresh"
  }
}
```

Nilai `type` yang dipakai aplikasi:

```text
libur_nasional
cuti_bersama
```

Catatan: cuti bersama Indonesia ditetapkan pemerintah setiap tahun. Data tahun masa depan baru akurat setelah jadwal resmi dirilis dan provider memperbaruinya.

## Deployment Vercel

Konfigurasi Vercel ada di `vercel.json`.

- File statis disajikan dari `public/`.
- Endpoint serverless ada di `api/holidays.py` dan `api/sync.py`.
- File `data/holidays/**` ikut dibundel melalui `includeFiles`.
- Cron berjalan pada path `/api/sync` sesuai jadwal `0 17 * * *`.
- Jika `CRON_SECRET` diisi, request ke `/api/sync` harus memakai header `Authorization: Bearer <CRON_SECRET>`.

## Testing

Jalankan unit test:

```powershell
python -m unittest discover -s tests
```

Cek sintaks Python:

```powershell
python -m compileall app api scripts tests
```
