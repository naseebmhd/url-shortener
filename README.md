# 🔗 URL Shortener

A professional URL shortener like bit.ly, built with Python Flask.

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-2.0-green)
![SQLite](https://img.shields.io/badge/SQLite-3.0-orange)

## ✨ Features

- 🔗 Shorten long URLs
- ✏️ Custom short codes (choose your own)
- 📱 QR code generation for each link
- 📊 Click analytics dashboard
- 💻 Device tracking (Desktop/Mobile/iOS)
- 🌐 Browser tracking (Chrome/Firefox/Safari/Edge)
- 🎨 Modern dark theme UI
- 💾 Persistent SQLite database

## 🚀 Live Demo

## 🚀 Live Demo

Try it here: https://url-shortener-tw1m.onrender.com/

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask |
| Database | SQLite |
| QR Codes | qrcode library |
| Frontend | HTML, CSS (Dark theme) |

## 📦 Local Setup

```bash
# Clone the repository
git clone https://github.com/naseebmhd/url-shortener.git

# Go to project folder
cd url-shortener

# Install dependencies
pip install flask qrcode[pil]

# Run the app
python app.py
