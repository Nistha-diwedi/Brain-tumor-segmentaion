# 🧠 BrainSeg AI — Brain Tumor Segmentation

A Django web application that performs **AI-powered brain tumor segmentation** on MRI scans. Users upload an MRI image, a deep-learning **U-Net** model produces a segmentation mask highlighting abnormal regions, and an optional **Gemini**-generated clinical report explains the findings in patient-friendly language.

> ⚠️ **Disclaimer:** This project is for **research and educational purposes only**. It is **not a medical device** and must **not** be used for real diagnosis. Always consult a qualified healthcare professional.

---

## ✨ Features

- **User accounts** — registration, login/logout, and profiles (custom user model with name, DOB, gender, phone, address).
- **MRI upload** — drag-and-drop or click-to-browse, with client-side validation (image type, max 10 MB) and live preview.
- **AI segmentation** — a PyTorch U-Net model generates a binary segmentation mask for each scan.
- **Confidence scoring** — every report shows a model confidence score with color-coded badges.
- **AI clinical report** — a server-side Gemini call generates a detailed, structured explanation of the segmentation findings.
- **Medical history** — all scans stored per user, with search + date/confidence filters and pagination.
- **Report view** — side-by-side original vs. segmentation, downloads, and share/print.
- **Modern UI** — responsive dashboard with a left-sidebar app shell (Bootstrap 5 + custom design system).

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2 (Python 3.12) |
| ML | PyTorch + TorchVision (U-Net segmentation) |
| AI reports | Google Generative AI (Gemini) |
| Frontend | Bootstrap 5, Font Awesome, custom CSS/JS |
| Database | SQLite (development) |
| Image processing | Pillow, NumPy |

---

## 📁 Project Structure

```
BrainTumorSegmentationApp/
├── BrainTumorSegmentationApp/   # Django project (settings, urls, wsgi/asgi)
│   └── settings.py              # Reads secrets from private/.env
├── brain_tumor_app/             # Main app
│   ├── models.py                # User + MRIReport models
│   ├── views.py                 # Pages, upload, AI-report endpoint
│   ├── forms.py                 # Registration + upload forms
│   ├── ml_processing.py         # Loads U-Net, runs segmentation (lazy imports)
│   └── urls.py
├── bts/                         # U-Net model definition + helpers
│   ├── model.py                 # DynamicUNet
│   ├── classifier.py, loss.py, dataset.py, plot.py
├── templates/brain_tumor_app/   # HTML templates
├── static/                      # style.css, upload.js
├── saved_models/                # Trained weights (UNet-[16, 32, 64, 128, 256].pt)
├── media/                       # User uploads (git-ignored)
├── private/                     # Secrets + database (git-ignored)
│   ├── .env
│   └── db.sqlite3
├── .env.example                 # Template for environment variables
├── requirements.txt
└── manage.py
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on 3.12)
- `pip` and (recommended) a virtual environment

### 2. Clone
```bash
git clone https://github.com/Nistha-diwedi/Brain-tumor-segmentaion.git
cd Brain-tumor-segmentaion
```

### 3. Create a virtual environment
```bash
python -m venv venv
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```
> The `torch` / `torchvision` install is large. The website (auth, dashboard, history) runs fine **without** them — they're only needed to actually process a scan.

### 5. Configure environment variables
Secrets are **not** committed. Create `private/.env` from the template:

```bash
mkdir private
cp .env.example private/.env      # Windows: copy .env.example private\.env
```

Then edit `private/.env`:
```ini
DJANGO_SECRET_KEY=your-django-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
GENERATIVE_API_KEY=your-gemini-api-key
```

- Generate a Django secret key:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- Get a Gemini API key at <https://aistudio.google.com/app/apikey>.

### 6. Run migrations
```bash
python manage.py migrate
```
> The database lives at `private/db.sqlite3` (created automatically).

### 7. (Optional) Create an admin user
```bash
python manage.py createsuperuser
```

### 8. Start the server
```bash
python manage.py runserver
```
Open <http://127.0.0.1:8000/>.

---

## 🧪 How It Works

1. **Upload** — the user submits an MRI image (`MRIReport` is created and the file saved under `media/`).
2. **Preprocess** — the image is converted to grayscale and resized to `512×512` (`ml_processing.preprocess_image`).
3. **Segment** — the `DynamicUNet` model (`filters = [16, 32, 64, 128, 256]`) runs inference; the output is thresholded at `0.5` to a binary mask and saved.
4. **Report** — a confidence score is stored, and the user can click **Generate AI Report** to get a Gemini-authored clinical explanation.
5. **Review** — results appear on the dashboard, history, and detailed report pages.

The trained weights are expected at:
```
saved_models/UNet-[16, 32, 64, 128, 256].pt
```

---

## 🔒 Security Notes

- **No secrets in source.** `SECRET_KEY` and `GENERATIVE_API_KEY` are loaded from `private/.env` (git-ignored). `.env.example` documents what's needed.
- **The Gemini key stays server-side.** The browser calls a Django endpoint (`/report/<id>/ai-analysis/`) which proxies the request — the key is never exposed to the client.
- **Local data is not committed.** `private/` (secrets + DB) and `media/` (uploads) are excluded via `.gitignore`.
- **For production**, set `DJANGO_DEBUG=False`, configure `DJANGO_ALLOWED_HOSTS`, use a production database, and serve static/media through a proper web server.

---

## 📋 Requirements

```
Django>=5.2
Pillow
python-dotenv
google-generativeai
torch
torchvision
numpy
```

---

## 📄 License

For educational and research use. Not intended for clinical or diagnostic use.
