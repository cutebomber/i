"""
Fragment Bot — Admin Web Panel
Run: python admin_panel.py
Access: http://YOUR_VPS_IP:8080
"""

from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, flash
import sqlite3, os, functools
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(32)

DB_PATH        = os.path.join(os.path.dirname(__file__), "bot_data.db")
PANEL_PASSWORD = "admin123"   # ← CHANGE THIS
PANEL_PORT     = 8081

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def q(sql, args=(), one=False):
    con = get_db()
    cur = con.execute(sql, args)
    rv  = cur.fetchone() if one else cur.fetchall()
    con.commit()
    con.close()
    return rv

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

CSS = """
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#0d0d0f;--surface:#141418;--card:#1a1a20;--border:#2a2a35;--accent:#5b6aff;--accent2:#00e5a0;--danger:#ff4d6a;--warning:#ffb347;--text:#e8e8f0;--muted:#6b6b80;--radius:12px}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh}
a{color:var(--accent);text-decoration:none}a:hover{color:var(--accent2)}
.layout{display:flex;min-height:100vh}
.sidebar{width:220px;min-height:100vh;background:var(--surface);border-right:1px solid var(--border);padding:24px 0;position:fixed;top:0;left:0;z-index:100;display:flex;flex-direction:column}
.logo{padding:0 20px 24px;border-bottom:1px solid var(--border);font-size:18px;font-weight:800}
.logo span{color:var(--accent)}.logo small{display:block;font-size:11px;color:var(--muted);font-weight:400;margin-top:2px}
.nav{padding:16px 0;flex:1}
.nav a{display:flex;align-items:center;gap:10px;padding:10px 20px;color:var(--muted);font-size:14px;transition:all .15s;border-left:3px solid transparent}
.nav a:hover,.nav a.active{color:var(--text);background:rgba(91,106,255,.08);border-left-color:var(--accent)}
.sfooter{padding:16px 20px;border-top:1px solid var(--border)}.sfooter a{color:var(--danger);font-size:13px}
.main{margin-left:220px;flex:1;padding:32px}
.ph{margin-bottom:28px;display:flex;align-items:center;justify-content:space-between}
.ph-left h1{font-size:26px;font-weight:800;letter-spacing:-.5px}.ph-left p{color:var(--muted);font-size:14px;margin-top:4px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px;margin-bottom:28px}
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:20px}
.card-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.card-value{font-size:28px;font-weight:800;font-family:'Space Mono',monospace}
.green{color:var(--accent2)}.blue{color:var(--accent)}.orange{color:var(--warning)}.red{color:var(--danger)}
.tw{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden}
.th{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.th h2{font-size:15px;font-weight:700}
table{width:100%;border-collapse:collapse}
th{padding:10px 16px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);border-bottom:1px solid var(--border);font-weight:600}
td{padding:12px 16px;font-size:13px;border-bottom:1px solid rgba(42,42,53,.5);vertical-align:middle}
tr:last-child td{border-bottom:none}tr:hover td{background:rgba(91,106,255,.04)}
.mono{font-family:'Space Mono',monospace;font-size:12px}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:.5px}
.bg{background:rgba(0,229,160,.15);color:var(--accent2)}.bb{background:rgba(91,106,255,.15);color:var(--accent)}
.br{background:rgba(255,77,106,.15);color:var(--danger)}.bo{background:rgba(255,179,71,.15);color:var(--warning)}
.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;border:none;font-family:'Syne',sans-serif;transition:all .15s;text-decoration:none}
.bp{background:var(--accent);color:#fff}.bp:hover{background:#4a59ee;color:#fff}
.bd{background:rgba(255,77,106,.15);color:var(--danger);border:1px solid rgba(255,77,106,.3)}.bd:hover{background:var(--danger);color:#fff}
.bg2{background:rgba(0,229,160,.15);color:var(--accent2);border:1px solid rgba(0,229,160,.3)}.bg2:hover{background:var(--accent2);color:#000}
.bgh{background:transparent;color:var(--muted);border:1px solid var(--border)}.bgh:hover{color:var(--text);border-color:var(--accent)}
.fg{margin-bottom:16px}.fg label{display:block;font-size:12px;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px}
.fg input,.fg select{width:100%;padding:10px 14px;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);font-family:'Space Mono',monospace;font-size:13px;transition:border-color .15s}
.fg input:focus,.fg select:focus{outline:none;border-color:var(--accent)}
.mo{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:200;align-items:center;justify-content:center}
.mo.open{display:flex}.mbox{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:28px;width:100%;max-width:480px}
.mbox h2{font-size:18px;font-weight:800;margin-bottom:20px}.mf{display:flex;gap:10px;justify-content:flex-end;margin-top:20px}
.alert{padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:20px}
.alert-success{background:rgba(0,229,160,.1);border:1px solid rgba(0,229,160,.3);color:var(--accent2)}
.alert-error{background:rgba(255,77,106,.1);border:1px solid rgba(255,77,106,.3);color:var(--danger)}
.lw{min-height:100vh;display:flex;align-items:center;justify-content:center}
.lb{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:40px;width:100%;max-width:380px}
.lb h1{font-size:24px;font-weight:800;margin-bottom:6px}.lb p{color:var(--muted);font-size:13px;margin-bottom:28px}
.trunc{max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
</style>
"""

def layout(content, page):
    nav_items = [
        ("dashboard", "📊", "Dashboard"),
        ("stock",     "📦", "Stock"),
        ("users",     "👥", "Users"),
        ("orders",    "📋", "Orders"),
        ("settings",  "⚙️",  "Settings"),
    ]
    nav_html = "".join(
        '<a href="/{}" class="{}"><span>{}</span> {}</a>'.format(p, "active" if p==page else "", icon, label)
        for p, icon, label in nav_items
    )
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fragment Admin</title>{CSS}</head><body>
<div class="layout">
<aside class="sidebar">
  <div class="logo">💎 Fragment<span>Admin</span><small>Bot Control Panel</small></div>
  <nav class="nav">{nav_html}</nav>
  <div class="sfooter"><a href="/logout">🚪 Logout</a></div>
</aside>
<main class="main">{content}</main>
</div></body></html>"""

def flash_html():
    msgs = []
    for cat, msg in (session.pop("_flashes", None) or []):
        msgs.append(f'<div class="alert alert-{cat}">{msg}</div>')
    return "".join(msgs)

def add_flash(cat, msg):
    if "_flashes" not in session:
        session["_flashes"] = []
    session["_flashes"].append((cat, msg))

@app.route("/", methods=["GET","POST"])
def login():
    error = ""
    if request.method == "POST":
        if request.form.get("password") == PANEL_PASSWORD:
            session["admin"] = True
            return redirect("/dashboard")
        error = '<div class="alert alert-error">Wrong password.</div>'
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Login</title>{CSS}</head><body>
<div class="lw"><div class="lb">
<h1>💎 Fragment<span style="color:var(--accent)">Admin</span></h1>
<p>Enter your admin password to continue.</p>
{error}
<form method="POST">
<div class="fg"><label>Password</label><input type="password" name="password" autofocus placeholder="••••••••"></div>
<button class="btn bp" style="width:100%;justify-content:center;padding:12px" type="submit">Login →</button>
</form></div></div></body></html>"""

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
@login_required
def dashboard():
    total_users   = q("SELECT COUNT(*) as c FROM users", one=True)["c"]
    total_stock   = q("SELECT COUNT(*) as c FROM accounts WHERE status='available'", one=True)["c"]
    total_sold    = q("SELECT COUNT(*) as c FROM accounts WHERE status='sold'", one=True)["c"]
    rev_row       = q("SELECT SUM(amount_ton) as s FROM transactions WHERE type='purchase'", one=True)
    total_rev     = float(rev_row["s"] or 0)
    price_row     = q("SELECT value FROM settings WHERE key='price_usdt'", one=True)
    price_usdt    = float(price_row["value"]) if price_row else 5.0
    recent_orders = q("""SELECT t.*,u.username FROM transactions t
        LEFT JOIN users u ON t.user_id=u.telegram_id
        WHERE t.type='purchase' ORDER BY t.created_at DESC LIMIT 10""")
    rows = "".join(f"""<tr>
        <td>{"@"+r["username"] if r["username"] else r["user_id"]}</td>
        <td class="mono">{float(r["amount_ton"] or 0):.4f} TON</td>
        <td class="mono" style="color:var(--muted);font-size:11px">{r["created_at"] or "—"}</td>
        <td><span class="badge bg">Completed</span></td>
    </tr>""" for r in recent_orders) or '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:24px">No orders yet</td></tr>'
    content = f"""{flash_html()}
    <div class="ph"><div class="ph-left"><h1>Dashboard</h1><p>Welcome back.</p></div></div>
    <div class="cards">
      <div class="card"><div class="card-label">Available Stock</div><div class="card-value blue">{total_stock}</div></div>
      <div class="card"><div class="card-label">Total Sold</div><div class="card-value green">{total_sold}</div></div>
      <div class="card"><div class="card-label">Total Users</div><div class="card-value">{total_users}</div></div>
      <div class="card"><div class="card-label">Revenue (TON)</div><div class="card-value orange">{total_rev:.2f}</div></div>
      <div class="card"><div class="card-label">Account Price</div><div class="card-value green">${price_usdt:.2f}</div></div>
    </div>
    <div class="tw"><div class="th"><h2>Recent Orders</h2></div>
    <table><tr><th>User</th><th>Amount</th><th>Date</th><th>Status</th></tr>{rows}</table></div>"""
    return layout(content, "dashboard")

@app.route("/stock")
@login_required
def stock():
    accounts = q("SELECT * FROM accounts ORDER BY added_at DESC")
    avail = sum(1 for a in accounts if a["status"]=="available")
    sold  = sum(1 for a in accounts if a["status"]=="sold")
    rows = "".join(f"""<tr>
        <td class="mono" style="color:var(--muted)">{a["id"]}</td>
        <td class="mono trunc">{a["phone"]}</td>
        <td><span class="badge {"bo" if a["password_2fa"] else "bb"}">{"✓ 2FA" if a["password_2fa"] else "No 2FA"}</span></td>
        <td><span class="badge {"bg" if a["status"]=="available" else "br"}">{a["status"].title()}</span></td>
        <td class="mono" style="color:var(--muted);font-size:11px">{a["added_at"] or "—"}</td>
        <td><form method="POST" action="/stock/delete/{a["id"]}" onsubmit="return confirm('Delete?')" style="display:inline">
          <button class="btn bd" style="padding:5px 10px;font-size:11px">Delete</button></form></td>
    </tr>""" for a in accounts) or '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:24px">No accounts in stock</td></tr>'
    content = f"""{flash_html()}
    <div class="ph">
      <div class="ph-left"><h1>Stock</h1><p>Available: <b style="color:var(--accent2)">{avail}</b> &nbsp; Sold: <b style="color:var(--muted)">{sold}</b></p></div>
      <button class="btn bp" onclick="document.getElementById('addM').classList.add('open')">+ Add Account</button>
    </div>
    <div class="tw"><table>
      <tr><th>#</th><th>Phone / ID</th><th>2FA</th><th>Status</th><th>Added</th><th>Action</th></tr>
      {rows}
    </table></div>
    <div class="mo" id="addM"><div class="mbox">
      <h2>Add Account</h2>
      <form method="POST" action="/stock/add">
        <div class="fg"><label>Phone Number</label><input type="text" name="phone" placeholder="+14155552671" required></div>
        <div class="fg"><label>Session String</label><input type="text" name="session_string" placeholder="1BVtsOA3n..." required></div>
        <div class="fg"><label>2FA Password (optional)</label><input type="text" name="password_2fa" placeholder="Leave blank if none"></div>
        <div class="mf">
          <button type="button" class="btn bgh" onclick="document.getElementById('addM').classList.remove('open')">Cancel</button>
          <button type="submit" class="btn bp">Save Account</button>
        </div>
      </form>
    </div></div>"""
    return layout(content, "stock")

@app.route("/stock/add", methods=["POST"])
@login_required
def stock_add():
    phone = request.form.get("phone","").strip()
    sess  = request.form.get("session_string","").strip()
    pw    = request.form.get("password_2fa","").strip()
    if not phone or not sess:
        add_flash("error", "Phone and session string are required.")
        return redirect("/stock")
    try:
        con = get_db()
        con.execute("""INSERT INTO accounts(phone,password_2fa,session_string,status,added_at)
            VALUES(?,?,?,'available',?) ON CONFLICT(phone) DO UPDATE SET
            password_2fa=excluded.password_2fa,session_string=excluded.session_string,
            status='available',added_at=excluded.added_at""",
            (phone, pw, sess, datetime.now().strftime("%Y-%m-%d %H:%M")))
        con.commit(); con.close()
        add_flash("success", "Account added successfully.")
    except Exception as e:
        add_flash("error", str(e))
    return redirect("/stock")

@app.route("/stock/delete/<int:aid>", methods=["POST"])
@login_required
def stock_delete(aid):
    try:
        con = get_db(); con.execute("DELETE FROM accounts WHERE id=?", (aid,)); con.commit(); con.close()
        add_flash("success", "Account deleted.")
    except Exception as e:
        add_flash("error", str(e))
    return redirect("/stock")

@app.route("/users")
@login_required
def users():
    all_users = q("""SELECT u.*,COUNT(t.id) as pc FROM users u
        LEFT JOIN transactions t ON t.user_id=u.telegram_id AND t.type='purchase'
        GROUP BY u.telegram_id ORDER BY u.created_at DESC""")
    rows = "".join(f"""<tr>
        <td class="mono">{u["telegram_id"]}</td>
        <td>{"@"+u["username"] if u["username"] else '<span style="color:var(--muted)">—</span>'}</td>
        <td class="mono green">{float(u["balance_ton"] or 0):.4f}</td>
        <td><span class="badge bb">{u["pc"]}</span></td>
        <td class="mono" style="font-size:11px;color:var(--muted)">{u["created_at"] or "—"}</td>
        <td><button class="btn bg2" style="padding:5px 10px;font-size:11px"
          onclick="openCredit({u['telegram_id']}, '{"@"+u["username"] if u["username"] else u["telegram_id"]}')">+ Credit</button></td>
    </tr>""" for u in all_users) or '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:24px">No users yet</td></tr>'
    content = f"""{flash_html()}
    <div class="ph"><div class="ph-left"><h1>Users</h1><p>{len(all_users)} registered users.</p></div></div>
    <div class="tw"><table>
      <tr><th>Telegram ID</th><th>Username</th><th>Balance (TON)</th><th>Purchases</th><th>Joined</th><th>Action</th></tr>
      {rows}
    </table></div>
    <div class="mo" id="creditM"><div class="mbox">
      <h2>Credit Balance</h2>
      <p id="cUser" style="color:var(--muted);margin-bottom:16px;font-size:13px"></p>
      <form method="POST" action="/users/credit">
        <input type="hidden" name="telegram_id" id="cId">
        <div class="fg"><label>Amount (TON)</label><input type="number" name="amount" step="0.01" min="0.01" placeholder="e.g. 3.5" required></div>
        <div class="mf">
          <button type="button" class="btn bgh" onclick="document.getElementById('creditM').classList.remove('open')">Cancel</button>
          <button type="submit" class="btn bg2">Add Balance</button>
        </div>
      </form>
    </div></div>
    <script>
    function openCredit(id,name){{
      document.getElementById('cId').value=id;
      document.getElementById('cUser').textContent='User: '+name+' (ID: '+id+')';
      document.getElementById('creditM').classList.add('open');
    }}
    </script>"""
    return layout(content, "users")

@app.route("/users/credit", methods=["POST"])
@login_required
def users_credit():
    tid = int(request.form.get("telegram_id"))
    amt = float(request.form.get("amount", 0))
    if amt <= 0:
        add_flash("error", "Amount must be positive.")
        return redirect("/users")
    try:
        con = get_db()
        con.execute("UPDATE users SET balance_ton=balance_ton+? WHERE telegram_id=?", (amt, tid))
        con.commit(); con.close()
        add_flash("success", f"Added {amt} TON to user {tid}.")
    except Exception as e:
        add_flash("error", str(e))
    return redirect("/users")

@app.route("/orders")
@login_required
def orders():
    all_orders = q("""SELECT t.*,u.username FROM transactions t
        LEFT JOIN users u ON t.user_id=u.telegram_id ORDER BY t.created_at DESC LIMIT 200""")
    rows = "".join(f"""<tr>
        <td class="mono" style="color:var(--muted)">{o["id"]}</td>
        <td>{"@"+o["username"] if o["username"] else o["user_id"]}</td>
        <td><span class="badge {"br" if o["type"]=="purchase" else "bg"}">{o["type"].title()}</span></td>
        <td class="mono" style="color:{"var(--danger)" if o["type"]=="purchase" else "var(--accent2)"}">
          {"−" if o["type"]=="purchase" else "+"}{float(o["amount_ton"] or 0):.4f} TON</td>
        <td class="mono" style="font-size:11px;color:var(--muted)">{o["created_at"] or "—"}</td>
    </tr>""" for o in all_orders) or '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:24px">No transactions yet</td></tr>'
    content = f"""{flash_html()}
    <div class="ph"><div class="ph-left"><h1>Orders</h1><p>All transactions and purchase history.</p></div></div>
    <div class="tw"><table>
      <tr><th>#</th><th>User</th><th>Type</th><th>Amount</th><th>Date</th></tr>
      {rows}
    </table></div>"""
    return layout(content, "orders")

@app.route("/settings", methods=["GET","POST"])
@login_required
def settings():
    global PANEL_PASSWORD
    if request.method == "POST":
        action = request.form.get("action")
        if action == "price":
            price = float(request.form.get("price_usdt", 5))
            con = get_db()
            con.execute("INSERT INTO settings(key,value) VALUES('price_usdt',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(price),))
            con.commit(); con.close()
            add_flash("success", f"Price updated to ${price:.2f} USDT.")
        elif action == "pw":
            new_pw = request.form.get("new_password","").strip()
            if new_pw:
                PANEL_PASSWORD = new_pw
                add_flash("success", "Panel password updated.")
            else:
                add_flash("error", "Password cannot be empty.")
        return redirect("/settings")

    price_row  = q("SELECT value FROM settings WHERE key='price_usdt'", one=True)
    price_usdt = float(price_row["value"]) if price_row else 5.0
    wallet_row = q("SELECT value FROM settings WHERE key='bot_wallet'", one=True)
    wallet     = wallet_row["value"] if wallet_row else "—"

    content = f"""{flash_html()}
    <div class="ph"><div class="ph-left"><h1>Settings</h1><p>Configure bot parameters.</p></div></div>
    <div class="grid2">
      <div class="card">
        <h2 style="font-size:15px;margin-bottom:16px">💲 Account Price</h2>
        <form method="POST">
          <input type="hidden" name="action" value="price">
          <div class="fg"><label>Price (USDT)</label>
            <input type="number" name="price_usdt" step="0.01" min="0.1" value="{price_usdt:.2f}" required>
          </div>
          <button class="btn bp" type="submit">Update Price</button>
        </form>
      </div>
      <div class="card">
        <h2 style="font-size:15px;margin-bottom:16px">🔒 Panel Password</h2>
        <form method="POST">
          <input type="hidden" name="action" value="pw">
          <div class="fg"><label>New Password</label>
            <input type="password" name="new_password" placeholder="Enter new password">
          </div>
          <button class="btn bp" type="submit">Update Password</button>
        </form>
      </div>
      <div class="card" style="grid-column:1/-1">
        <h2 style="font-size:15px;margin-bottom:12px">ℹ️ Bot Info</h2>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;font-size:13px">
          <div><div style="color:var(--muted);font-size:11px;margin-bottom:4px">DATABASE</div><div class="mono" style="font-size:11px">{DB_PATH}</div></div>
          <div><div style="color:var(--muted);font-size:11px;margin-bottom:4px">BOT WALLET</div><div class="mono" style="font-size:11px">{wallet}</div></div>
          <div><div style="color:var(--muted);font-size:11px;margin-bottom:4px">PANEL PORT</div><div class="mono" style="font-size:11px">{PANEL_PORT}</div></div>
        </div>
      </div>
    </div>"""
    return layout(content, "settings")

if __name__ == "__main__":
    print(f"\n💎 Fragment Admin Panel")
    print(f"   URL:      http://0.0.0.0:{PANEL_PORT}")
    print(f"   Password: {PANEL_PASSWORD}")
    print(f"   DB:       {DB_PATH}\n")
    app.run(host="0.0.0.0", port=PANEL_PORT, debug=False)
