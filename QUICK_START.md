# Quick Start Guide - Course Downloader (Coursera & edX.org)

## 🚀 Get Started in 3 Steps

### Step 1: Prepare Your Cookies

Export your session cookies from your browser (using extensions like **Cookie-Editor** or Netscape format), and save them:
- For Coursera: `coursera_cookies.txt` (or `.json`)
- For edX: `edx_cookies.json` (or `.txt`)

*(For Edge on Windows, you can also auto-extract Coursera cookies via `python coursera_dl.py --save-edge-cookies coursera_cookies.txt`)*

### Step 2: Download a Course

Using the unified `coursedownloader`:

```bash
# Auto-detect platform from URL:
coursedownloader "https://www.coursera.org/learn/YOUR-COURSE-NAME" -c coursera_cookies.txt
coursedownloader "https://learning.edx.org/course/course-v1:Org+Course+Run/home" --cookies-file edx_cookies.json

# Or explicit subcommands:
coursedownloader coursera -c coursera_cookies.txt YOUR-COURSE-NAME
coursedownloader edx --cookies-file edx_cookies.json course-v1:Org+Course+Run
```

### Step 3: Find Your Downloaded Files

- Coursera courses: `./Downloads/YOUR-COURSE-NAME/`
- edX courses: `./Downloads/edx/YOUR-COURSE-SLUG/`

---

## 📚 Common Commands

### 1. Unified CLI (`coursedownloader`):
```bash
# Dry-run inspect edX course without downloading
coursedownloader edx --cookies-file edx_cookies.json --dry-run course-v1:MITx+15.481x+1T2021

# Download only specific sections with regex filter
coursedownloader edx --cookies-file edx_cookies.json --section-filter "overview" course-v1:MITx+15.481x+1T2021

# Download Coursera course with subtitles
coursedownloader coursera -c coursera_cookies.txt -sl en machine-learning
```

### 2. Standalone Provider CLIs:
```bash
# Direct edX downloader
python edx_dl.py --cookies-file edx_cookies.json --dry-run "https://learning.edx.org/course/course-v1:MITx+15.481x+1T2021/home"

# Direct Coursera downloader
python coursera_dl.py --cookies_file coursera_cookies.txt "https://www.coursera.org/learn/data-analytics-foundations"
```

### 3. Download multiple courses (Python API):
```python
from coursera_dl import download_coursera_course

courses = [
    "https://www.coursera.org/learn/course-1",
    "https://www.coursera.org/learn/course-2",
]

for course in courses:
    download_coursera_course(course, cookies_file="coursera_cookies.txt")
```

---

## ✅ What You Get

Each course download includes:
- 📹 Video lectures (Direct MP4)
- 📝 Subtitles (SRT, VTT) and transcripts (TXT)
- 📊 Course materials (PDFs, Excel datasets, code notebooks)
- 📖 HTML readings and instructions

---

## ❓ Troubleshooting

**Q: Cookies not found?**
```bash
python coursera_dl.py --save-edge-cookies coursera_cookies.txt
```

**Q: 403 Forbidden error?**
- Enroll in the course first
- Re-export your cookies

**Q: No files downloaded?**
- Close Edge browser
- Make sure you're enrolled
- Check cookie file is not empty

**Q: Download appears stuck on one file?**
- The downloader now enforces 30s timeout per file
- It retries once and then skips the file automatically
- Review failed URLs at the end of the run

---

## 📖 Full Documentation

- **Detailed Guide**: See `DOWNLOAD_GUIDE.md`
- **Cookie Help**: See `EDGE_COOKIES_README.md`
- **Main README**: See `README.md`

## 🎓 Example: Download Entire Certificate Program

```python
# download_data_analytics_certificate.py
from coursera_dl import download_coursera_course

# DeepLearning.AI Data Analytics Professional Certificate
courses = [
    "https://www.coursera.org/learn/data-analytics-foundations",
    "https://www.coursera.org/learn/python-for-data-analytics", 
    "https://www.coursera.org/learn/applied-statistics-for-data-analytics",
    "https://www.coursera.org/learn/data-io-and-preprocessing-with-python-and-sql"
]

print("Downloading DeepLearning.AI Data Analytics Certificate...")
for i, course in enumerate(courses, 1):
    print(f"\n[{i}/{len(courses)}] Downloading course...")
    download_coursera_course(course)
    
print("\n✓ All courses downloaded!")
```

Run it:
```bash
python download_data_analytics_certificate.py
```

---

**Happy Learning! 🎓**














































































