from flask import Flask, request, redirect, send_file
import sqlite3
import random
import string
import qrcode
from io import BytesIO
import os

app = Flask(__name__)

# Create database and tables
def init_db():
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT NOT NULL,
            ip_address TEXT,
            device TEXT,
            browser TEXT,
            clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def generate_short_code():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=6))

def get_device_info(user_agent):
    device = "Unknown"
    browser = "Unknown"
    ua = user_agent.lower() if user_agent else ""
    
    if 'mobile' in ua or 'android' in ua:
        device = "📱 Mobile"
    elif 'iphone' in ua or 'ipad' in ua:
        device = "📱 iOS"
    elif 'windows' in ua or 'mac' in ua or 'linux' in ua:
        device = "💻 Desktop"
    
    if 'chrome' in ua and 'edge' not in ua:
        browser = "🌐 Chrome"
    elif 'firefox' in ua:
        browser = "🌐 Firefox"
    elif 'safari' in ua and 'chrome' not in ua:
        browser = "🌐 Safari"
    elif 'edge' in ua:
        browser = "🌐 Edge"
    
    return device, browser

# Homepage HTML
home_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL Shortener</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            color: #fff;
        }
        
        .container {
            max-width: 700px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .nav {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 3rem;
            padding: 1rem;
        }
        
        .nav a {
            color: #a78bfa;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
        }
        
        .nav a:hover {
            color: #c4b5fd;
        }
        
        .header {
            text-align: center;
            margin-bottom: 3rem;
        }
        
        .header h1 {
            font-size: 3rem;
            background: linear-gradient(135deg, #a78bfa, #818cf8);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            color: #94a3b8;
        }
        
        .card {
            background: rgba(30, 27, 75, 0.6);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 2rem;
            border: 1px solid rgba(167, 139, 250, 0.2);
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .url-input {
            width: 100%;
            padding: 1rem;
            background: rgba(15, 23, 42, 0.8);
            border: 2px solid rgba(167, 139, 250, 0.3);
            border-radius: 16px;
            color: #fff;
            font-size: 1rem;
            transition: all 0.3s;
        }
        
        .url-input:focus {
            outline: none;
            border-color: #a78bfa;
            box-shadow: 0 0 20px rgba(167, 139, 250, 0.2);
        }
        
        .url-input::placeholder {
            color: #475569;
        }
        
        .option-group {
            display: flex;
            gap: 2rem;
            margin: 1.5rem 0;
        }
        
        .option-group label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
            color: #cbd5e1;
        }
        
        .option-group input[type="radio"] {
            accent-color: #a78bfa;
            width: 18px;
            height: 18px;
        }
        
        .custom-input {
            margin-top: 1rem;
            display: none;
        }
        
        .custom-input input {
            width: 100%;
            padding: 0.75rem;
            background: rgba(15, 23, 42, 0.8);
            border: 2px solid rgba(167, 139, 250, 0.3);
            border-radius: 12px;
            color: #fff;
        }
        
        .custom-input small {
            display: block;
            margin-top: 0.5rem;
            color: #64748b;
            font-size: 0.75rem;
        }
        
        .btn {
            width: 100%;
            padding: 1rem;
            background: linear-gradient(135deg, #a78bfa, #818cf8);
            border: none;
            border-radius: 16px;
            color: #fff;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(167, 139, 250, 0.3);
        }
        
        .footer {
            text-align: center;
            margin-top: 2rem;
            color: #475569;
            font-size: 0.875rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/">Home</a>
            <a href="/dashboard">Dashboard</a>
        </div>
        
        <div class="header">
            <h1>🔗 URL Shortener</h1>
            <p>Create short, memorable links in seconds</p>
        </div>
        
        <div class="card">
            <form action="/shorten" method="POST">
                <div class="form-group">
                    <input type="url" name="url" class="url-input" placeholder="https://your-long-url.com/..." required>
                </div>
                
                <div class="option-group">
                    <label>
                        <input type="radio" name="code_type" value="random" checked onclick="toggleCustom(false)"> 🎲 Random
                    </label>
                    <label>
                        <input type="radio" name="code_type" value="custom" onclick="toggleCustom(true)"> ✏️ Custom
                    </label>
                </div>
                
                <div id="customDiv" class="custom-input">
                    <input type="text" name="custom_code" placeholder="your-custom-name">
                    <small>Letters, numbers, underscore only (3-20 characters)</small>
                </div>
                
                <button type="submit" class="btn">✨ Shorten URL</button>
            </form>
        </div>
        
        <div class="footer">
            Free • Fast • Track clicks • QR codes included
        </div>
    </div>
    
    <script>
        function toggleCustom(show) {
            document.getElementById('customDiv').style.display = show ? 'block' : 'none';
        }
    </script>
</body>
</html>
'''
@app.route('/')
def home():
    return home_html
@app.route('/health')
def health():
    return "OK", 200
@app.route('/shorten', methods=['POST'])
def shorten():
    original_url = request.form['url']
    code_type = request.form.get('code_type', 'random')
    
    if code_type == 'custom':
        short_code = request.form.get('custom_code', '').strip()
        if not short_code:
            return "<h1>Error</h1><p>Please enter a custom code</p><a href='/'>Try again</a>", 400
        if not all(c.isalnum() or c == '_' for c in short_code):
            return "<h1>Error</h1><p>Only letters, numbers, and underscore allowed</p><a href='/'>Try again</a>", 400
        if len(short_code) < 3 or len(short_code) > 20:
            return "<h1>Error</h1><p>Custom code must be 3-20 characters</p><a href='/'>Try again</a>", 400
        
        conn = sqlite3.connect('urls.db')
        c = conn.cursor()
        c.execute("SELECT id FROM urls WHERE short_code = ?", (short_code,))
        existing = c.fetchone()
        conn.close()
        
        if existing:
            return f"<h1>Error</h1><p>Short code '{short_code}' is already taken</p><a href='/'>Try again</a>", 400
    else:
        short_code = generate_short_code()
    
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute("INSERT INTO urls (original_url, short_code) VALUES (?, ?)", (original_url, short_code))
    conn.commit()
    conn.close()
    
    short_url = request.host_url + short_code
    
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(short_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    if not os.path.exists('static'):
        os.makedirs('static')
    
    with open(f"static/qr_{short_code}.png", "wb") as f:
        f.write(qr_buffer.getvalue())
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Success!</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                color: #fff;
            }}
            .container {{ text-align: center; padding: 2rem; }}
            .card {{
                background: rgba(30, 27, 75, 0.6);
                backdrop-filter: blur(10px);
                border-radius: 24px;
                padding: 2rem;
                max-width: 500px;
                margin: 0 auto;
                border: 1px solid rgba(167, 139, 250, 0.2);
            }}
            .short-link {{ font-size: 1.2rem; margin: 1.5rem 0; word-break: break-all; }}
            .short-link a {{ color: #a78bfa; text-decoration: none; }}
            .btn {{
                display: inline-block;
                padding: 0.75rem 1.5rem;
                background: linear-gradient(135deg, #a78bfa, #818cf8);
                border: none;
                border-radius: 12px;
                color: #fff;
                text-decoration: none;
                margin: 0.5rem;
                transition: transform 0.2s;
            }}
            .btn:hover {{ transform: translateY(-2px); }}
            .qr-code {{ margin: 1.5rem 0; }}
            h1 {{ background: linear-gradient(135deg, #a78bfa, #818cf8); -webkit-background-clip: text; background-clip: text; color: transparent; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>✨ Success!</h1>
                <div class="short-link">
                    🔗 <a href="{short_url}">{short_url}</a>
                </div>
                <div class="qr-code">
                    <img src="/qr/{short_code}" width="180">
                </div>
                <a href="/qr/{short_code}" download="qrcode_{short_code}.png" class="btn">📥 Download QR</a>
                <br><br>
                <a href="/" class="btn">🔗 Shorten another</a>
                <a href="/dashboard" class="btn">📊 Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/qr/<short_code>')
def get_qr(short_code):
    qr_path = f"static/qr_{short_code}.png"
    if os.path.exists(qr_path):
        return send_file(qr_path, mimetype='image/png')
    return "QR not found", 404

@app.route('/<short_code>')
def redirect_to_url(short_code):
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    
    c.execute("SELECT original_url FROM urls WHERE short_code = ?", (short_code,))
    result = c.fetchone()
    
    if result:
        c.execute("UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", (short_code,))
        ip = request.remote_addr
        device, browser = get_device_info(request.headers.get('User-Agent', ''))
        
        c.execute('INSERT INTO clicks (short_code, ip_address, device, browser) VALUES (?, ?, ?, ?)', 
                  (short_code, ip, device, browser))
        conn.commit()
        conn.close()
        return redirect(result[0])
    else:
        conn.close()
        return "<h1>404</h1><p>Short URL not found</p>", 404

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute("SELECT short_code, original_url, clicks, created_at FROM urls ORDER BY created_at DESC")
    all_urls = c.fetchall()
    conn.close()
    
    rows = ""
    for url in all_urls:
        short_code, original_url, clicks, created_at = url
        short_url = request.host_url + short_code
        rows += f'''
        <tr style="border-bottom: 1px solid rgba(167, 139, 250, 0.2);">
            <td style="padding: 12px;"><a href="{short_url}" style="color:#a78bfa;">{short_code}</a></td>
            <td style="padding: 12px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                <a href="{original_url}" target="_blank" style="color:#94a3b8;">{original_url[:50]}...</a>
            </td>
            <td style="padding: 12px; text-align: center;">{clicks}</td>
            <td style="padding: 12px;">{created_at}</td>
            <td style="padding: 12px;"><a href="/qr/{short_code}" style="color:#a78bfa;">📱 QR</a></td>
            <td style="padding: 12px;"><a href="/analytics/{short_code}" style="color:#a78bfa;">📊 View</a></td>
        </tr>
        '''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
                min-height: 100vh;
                color: #fff;
                padding: 2rem;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .nav {{
                display: flex;
                justify-content: center;
                gap: 2rem;
                margin-bottom: 2rem;
                padding: 1rem;
            }}
            .nav a {{ color: #a78bfa; text-decoration: none; font-weight: 500; }}
            .card {{
                background: rgba(30, 27, 75, 0.6);
                backdrop-filter: blur(10px);
                border-radius: 24px;
                padding: 2rem;
                border: 1px solid rgba(167, 139, 250, 0.2);
            }}
            h1 {{ margin-bottom: 1.5rem; background: linear-gradient(135deg, #a78bfa, #818cf8); -webkit-background-clip: text; background-clip: text; color: transparent; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ text-align: left; padding: 12px; color: #a78bfa; border-bottom: 2px solid rgba(167, 139, 250, 0.3); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav">
                <a href="/">Home</a>
                <a href="/dashboard">Dashboard</a>
            </div>
            <div class="card">
                <h1>📊 All Shortened URLs</h1>
                <table>
                    <thead>
                        <tr><th>Short Code</th><th>Original URL</th><th>Clicks</th><th>Created</th><th>QR</th><th>Analytics</th></tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/analytics/<short_code>')
def analytics(short_code):
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    
    c.execute("SELECT original_url, clicks FROM urls WHERE short_code = ?", (short_code,))
    link = c.fetchone()
    
    if not link:
        conn.close()
        return "Link not found", 404
    
    original_url, total_clicks = link
    
    c.execute('SELECT device, browser, clicked_at FROM clicks WHERE short_code = ? ORDER BY clicked_at DESC', (short_code,))
    clicks_data = c.fetchall()
    conn.close()
    
    device_counts = {}
    browser_counts = {}
    
    for device, browser, _ in clicks_data:
        device_counts[device] = device_counts.get(device, 0) + 1
        browser_counts[browser] = browser_counts.get(browser, 0) + 1
    
    device_rows = "".join([f'<tr><td>{d}</td><td>{cnt}</td></tr>' for d, cnt in sorted(device_counts.items(), key=lambda x: x[1], reverse=True)])
    browser_rows = "".join([f'<tr><td>{b}</td><td>{cnt}</td></tr>' for b, cnt in sorted(browser_counts.items(), key=lambda x: x[1], reverse=True)])
    recent_rows = "".join([f'<tr><td>{t}</td><td>{d}</td><td>{b}</td></tr>' for d, b, t in clicks_data[:20]])
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analytics</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
                min-height: 100vh;
                color: #fff;
                padding: 2rem;
            }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            .nav {{
                display: flex;
                justify-content: center;
                gap: 2rem;
                margin-bottom: 2rem;
            }}
            .nav a {{ color: #a78bfa; text-decoration: none; }}
            .card {{
                background: rgba(30, 27, 75, 0.6);
                backdrop-filter: blur(10px);
                border-radius: 24px;
                padding: 2rem;
                margin-bottom: 1.5rem;
                border: 1px solid rgba(167, 139, 250, 0.2);
            }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin: 1.5rem 0; }}
            h1, h2 {{ background: linear-gradient(135deg, #a78bfa, #818cf8); -webkit-background-clip: text; background-clip: text; color: transparent; }}
            .total {{ font-size: 3rem; font-weight: bold; color: #a78bfa; text-align: center; margin: 1rem 0; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid rgba(167, 139, 250, 0.2); }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav"><a href="/">Home</a> <a href="/dashboard">Dashboard</a></div>
            <div class="card">
                <h1>📈 Analytics: {short_code}</h1>
                <p>Original: <a href="{original_url}" target="_blank" style="color:#a78bfa;">{original_url[:80]}</a></p>
                <div class="total">{total_clicks} total clicks</div>
                
                <div class="grid">
                    <div>
                        <h2>📱 Devices</h2>
                        <table>{"".join(device_rows) if device_rows else '<tr><td>No data yet</td></tr>'}</table>
                    </div>
                    <div>
                        <h2>🌐 Browsers</h2>
                        <table>{"".join(browser_rows) if browser_rows else '<tr><td>No data yet</td></tr>'}</table>
                    </div>
                </div>
                
                <h2>🕐 Recent Clicks</h2>
                <table>
                    <tr><th>Time</th><th>Device</th><th>Browser</th></tr>
                    {recent_rows if recent_rows else '<tr><td colspan="3">No clicks yet</td></tr>'}
                </table>
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    init_db()
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True, host='0.0.0.0')
