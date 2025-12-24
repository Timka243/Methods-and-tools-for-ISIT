from flask import Flask, render_template_string, request, redirect, url_for, flash
import psycopg2
from datetime import date as dt_date
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
from flask import session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "dev"

_SCHEMA_READY = False

CSS = """
<style>
  :root{
    --bg1:#0b1220;
    --bg2:#0f172a;
    --card:#0b1220cc;
    --stroke:#1f2a44;
    --text:#e5e7eb;
    --muted:#9ca3af;
    --accent:#22c55e;
    --accent2:#38bdf8;
    --warn:#f59e0b;
    --danger:#ef4444;
    --btn:#111827;
    --shadow: 0 18px 40px rgba(0,0,0,.35);
  }
  *{ box-sizing:border-box; }
  body{
    margin:0;
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
    color:var(--text);
    background:
      radial-gradient(1100px 500px at 10% 0%, rgba(56,189,248,.18), transparent 60%),
      radial-gradient(900px 500px at 90% 10%, rgba(34,197,94,.16), transparent 55%),
      linear-gradient(180deg, var(--bg1), var(--bg2));
    min-height:100vh;
  }
  .wrap{ max-width: 1100px; margin: 0 auto; padding: 26px 18px 40px; }
  h1{ margin:0 0 10px 0; letter-spacing:.2px; }
  h2{ margin:0; }
  .muted{ color:var(--muted); font-size:14px; }
  .top{
    display:flex; align-items:flex-end; justify-content:space-between;
    gap:12px; flex-wrap:wrap; margin-bottom: 14px;
  }
  .actions{ display:flex; gap:10px; flex-wrap:wrap; }
  a.btn, button.btn{
    display:inline-flex; align-items:center; gap:8px;
    padding:10px 12px; border-radius:14px;
    border:1px solid var(--stroke); text-decoration:none;
    color:var(--text); background: rgba(255,255,255,.04);
    cursor:pointer;
  }
  a.btn:hover, button.btn:hover{ background: rgba(255,255,255,.07); }
  .btn.primary{ background: rgba(56,189,248,.14); border-color: rgba(56,189,248,.35); }
  .btn.primary:hover{ background: rgba(56,189,248,.20); }
  .btn.success{ background: rgba(34,197,94,.14); border-color: rgba(34,197,94,.38); }
  .btn.success:hover{ background: rgba(34,197,94,.20); }
  .btn.danger{ background: rgba(239,68,68,.14); border-color: rgba(239,68,68,.35); }
  .btn.danger:hover{ background: rgba(239,68,68,.20); }
  .btn.ghost{ background: transparent; }

  .grid{ display:flex; flex-wrap:wrap; gap:14px; }
  .card{
    width: 360px; max-width: 100%;
    border:1px solid var(--stroke);
    border-radius: 18px;
    padding: 14px;
    background: rgba(5,10,20,.45);
    box-shadow: var(--shadow);
    backdrop-filter: blur(8px);
  }
  .title{ font-size: 18px; font-weight: 800; margin: 0 0 6px 0; }
  .badge{
    display:inline-flex; align-items:center; gap:6px;
    padding: 6px 10px; border-radius: 999px;
    font-size: 13px; color: var(--text);
    border: 1px solid var(--stroke);
    background: rgba(255,255,255,.04);
  }
  .badge .dot{
    width:8px; height:8px; border-radius:999px; background: var(--accent2);
    box-shadow: 0 0 0 3px rgba(56,189,248,.10);
  }
  .box{
    border:1px solid var(--stroke);
    border-radius: 18px;
    padding: 14px;
    background: rgba(5,10,20,.45);
    box-shadow: var(--shadow);
    backdrop-filter: blur(8px);
  }

  table{
    width:100%;
    border-collapse: separate;
    border-spacing: 0;
    overflow:hidden;
    border-radius: 18px;
    border:1px solid var(--stroke);
    background: rgba(5,10,20,.45);
    box-shadow: var(--shadow);
    backdrop-filter: blur(8px);
  }
  th, td{ padding: 12px 12px; text-align:left; border-bottom:1px solid rgba(31,42,68,.7); }
  th{ background: rgba(255,255,255,.05); font-weight: 800; }
  tr:hover td{ background: rgba(255,255,255,.04); }
  tr:last-child td{ border-bottom:none; }

  .form{
    max-width: 620px;
    border:1px solid var(--stroke);
    border-radius: 18px;
    padding: 14px;
    background: rgba(5,10,20,.45);
    box-shadow: var(--shadow);
    backdrop-filter: blur(8px);
  }
  label{ display:block; margin-top:10px; margin-bottom:6px; font-weight:700; }
  input{
    width:100%;
    padding: 11px 12px;
    border-radius: 14px;
    border: 1px solid rgba(31,42,68,.9);
    background: rgba(255,255,255,.03);
    color: var(--text);
    outline:none;
  }
  input:focus{ border-color: rgba(56,189,248,.55); box-shadow: 0 0 0 4px rgba(56,189,248,.12); }
  .row{ display:flex; gap:12px; flex-wrap:wrap; }
  .row > div{ flex:1 1 180px; }

  .flash{
    border:1px solid rgba(34,197,94,.35);
    background: rgba(34,197,94,.10);
    padding: 12px;
    border-radius: 16px;
    margin-bottom: 12px;
  }
  .small{ font-size: 13px; color: var(--muted); }
  .actions-mini{ display:flex; gap:8px; flex-wrap:wrap; }
  .btn.xs{ padding: 8px 10px; border-radius: 12px; font-size: 14px; }
</style>
"""

def get_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    global _SCHEMA_READY
    if not _SCHEMA_READY:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'user',
                        full_name TEXT
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS locations (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS visits (
                        id SERIAL PRIMARY KEY,
                        location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
                        date DATE NOT NULL,
                        material TEXT NOT NULL,
                        spent NUMERIC DEFAULT 0,
                        discount NUMERIC DEFAULT 0,
                        created_by INTEGER REFERENCES users(id)
                    );
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS roles (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL
                    );
                """)
                cur.execute("""
                    INSERT INTO roles(name) VALUES ('admin'), ('user')
                    ON CONFLICT (name) DO NOTHING;
                """)

                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id SERIAL PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS visit_tags (
                        visit_id INTEGER NOT NULL REFERENCES visits(id) ON DELETE CASCADE,
                        tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
                        PRIMARY KEY (visit_id, tag_id)
                    );
                """)
            conn.commit()
            _SCHEMA_READY = True
        except Exception:
            conn.rollback()
            raise

    return conn


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            flash("Недостаточно прав (нужен admin).")
            return redirect(url_for("home"))
        return fn(*args, **kwargs)
    return wrapper


def fetch_roles(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM roles ORDER BY name;")
        return [r[0] for r in cur.fetchall()]


def create_user(conn, username: str, password: str, full_name: str | None, role: str = "user") -> int:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (%s, %s, %s, %s) RETURNING id",
            (username, generate_password_hash(password), role, full_name),
        )
        return int(cur.fetchone()[0])


def list_users(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id, username, role, COALESCE(full_name,'') FROM users ORDER BY id;")
        return cur.fetchall()




def fetch_user_by_username(conn, username: str):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, username, password_hash, role, full_name FROM users WHERE username=%s",
            (username,)
        )
        return cur.fetchone()

def rub(x):
    if x is None:
        return "0"
    n = int(round(float(x)))
    return f"{n:,}".replace(",", " ")

def fetch_locations_with_counts(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT l.id, l.name, COUNT(v.id) AS visits_cnt
            FROM locations l
            LEFT JOIN visits v ON v.location_id = l.id
            GROUP BY l.id, l.name
            ORDER BY l.id
        """)
        return cur.fetchall()

def fetch_location_name(conn, location_id: int):
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM locations WHERE id = %s", (location_id,))
        row = cur.fetchone()
        return row[0] if row else None

def fetch_materials(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT material
            FROM visits
            WHERE material IS NOT NULL AND material <> ''
            ORDER BY material
        """)
        return [r[0] for r in cur.fetchall()]
def fetch_tags(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM tags ORDER BY name;")
        return cur.fetchall()


def upsert_tag(conn, name: str) -> int:
    name = (name or "").strip()
    if not name:
        raise ValueError("empty tag")
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO tags (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id;",
            (name,),
        )
        return int(cur.fetchone()[0])


def fetch_visit_tag_ids(conn, visit_id: int):
    with conn.cursor() as cur:
        cur.execute("SELECT tag_id FROM visit_tags WHERE visit_id = %s ORDER BY tag_id;", (visit_id,))
        return {int(r[0]) for r in cur.fetchall()}


def set_visit_tags(conn, visit_id: int, tag_ids: list[int]):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM visit_tags WHERE visit_id = %s;", (visit_id,))
        for tid in tag_ids:
            cur.execute(
                "INSERT INTO visit_tags (visit_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                (visit_id, tid),
            )




def fetch_visit(conn, visit_id: int):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, location_id, date, material, spent, discount
            FROM visits
            WHERE id = %s
        """, (visit_id,))
        return cur.fetchone()

@app.route("/", methods=["GET"])
@login_required
def home():
    conn = get_connection()
    try:
        locations = fetch_locations_with_counts(conn)
        html = """
        {{ css|safe }}
        <div class="wrap">
          <div class="top">
            <div>
              <h1>Локации</h1>
              <div class="muted">Быстрый переход к аналитике, визитам и добавлению</div>
            </div>
            <div class="actions">
              {% if session.get('role') == 'admin' %}
                <a class="btn" href="{{ url_for('users') }}">Пользователи</a>
              {% endif %}
              <a class="btn danger" href="{{ url_for('logout') }}">Выйти</a>
            </div>
          </div>

          {% if not locations %}
            <div class="box">Локаций пока нет.</div>
          {% else %}
            <div class="grid">
              {% for id, name, cnt in locations %}
                <div class="card">
                  <div class="title">{{ name }}</div>
                  <div class="row" style="align-items:center; margin-top:8px;">
                    <div class="badge"><span class="dot"></span> ID: {{ id }}</div>
                    <div class="badge"><span class="dot" style="background:var(--accent)"></span> Визитов: {{ cnt }}</div>
                  </div>
                  <div class="actions" style="margin-top:12px;">
                    <a class="btn primary" href="{{ url_for('stats', location_id=id) }}">Аналитика</a>
                    <a class="btn" href="{{ url_for('visits', location_id=id) }}">Визиты</a>
                    <a class="btn success" href="{{ url_for('new_visit', location_id=id) }}">Добавить визит</a>
                  </div>
                </div>
              {% endfor %}
            </div>
          {% endif %}
        </div>
        """
        return render_template_string(html, css=CSS, locations=locations)
    finally:
        conn.close()

@app.route("/stats", methods=["GET"])
@login_required
def stats():
    location_id = request.args.get("location_id", type=int)
    if location_id is None:
        return redirect(url_for("home"))

    conn = get_connection()
    try:
        loc_name = fetch_location_name(conn, location_id)
        if not loc_name:
            return redirect(url_for("home"))

        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) AS visits_cnt,
                    SUM(spent) AS spent_sum,
                    SUM(discount) AS discount_sum,
                    AVG(spent) AS avg_spent,
                    AVG(discount) AS avg_discount
                FROM visits
                WHERE location_id = %s
            """, (location_id,))
            row = cur.fetchone()

        s = {
            "visits": row[0] or 0,
            "spent": rub(row[1]),
            "discount": rub(row[2]),
            "avg_check": rub(row[3]),
            "avg_discount": rub(row[4]),
        }

        html = """
        {{ css|safe }}
        <div class="wrap">
          <div class="top">
            <div>
              <h1>Аналитика</h1>
              <div class="muted">{{ loc_name }}</div>
            </div>
            <div class="actions">
              <a class="btn ghost" href="{{ url_for('home') }}">← К локациям</a>
              <a class="btn" href="{{ url_for('visits', location_id=location_id) }}">Визиты</a>
              <a class="btn success" href="{{ url_for('new_visit', location_id=location_id) }}">Добавить визит</a>
              <a class="btn danger" href="{{ url_for('logout') }}">Выйти</a>
            </div>
          </div>

          {% with messages = get_flashed_messages() %}
            {% if messages %}
              <div class="flash">
                {% for m in messages %}<div>{{ m }}</div>{% endfor %}
              </div>
            {% endif %}
          {% endwith %}

          <div class="box">
            <h2 style="margin:0 0 10px 0;">Статистика</h2>
            <div class="row">
              <div><span class="muted">Визитов</span><div style="font-size:22px;font-weight:900;">{{ s.visits }}</div></div>
              <div><span class="muted">Потрачено</span><div style="font-size:22px;font-weight:900;">{{ s.spent }} ₽</div></div>
              <div><span class="muted">Скидок</span><div style="font-size:22px;font-weight:900;">{{ s.discount }} ₽</div></div>
            </div>
            <div style="margin-top:12px;" class="row">
              <div><span class="muted">Средний чек</span><div style="font-size:18px;font-weight:900;">{{ s.avg_check }} ₽</div></div>
              <div><span class="muted">Средняя скидка</span><div style="font-size:18px;font-weight:900;">{{ s.avg_discount }} ₽</div></div>
            </div>
            <div class="small" style="margin-top:10px;">Данные пересчитываются сразу после добавления/редактирования/удаления визита.</div>
          </div>
        </div>
        """
        return render_template_string(html, css=CSS, location_id=location_id, loc_name=loc_name, s=s)
    finally:
        conn.close()

@app.route("/visits", methods=["GET"])
@login_required
def visits():
    location_id = request.args.get("location_id", type=int)
    if location_id is None:
        return redirect(url_for("home"))

    conn = get_connection()
    try:
        loc_name = fetch_location_name(conn, location_id)
        if not loc_name:
            return redirect(url_for("home"))

        with conn.cursor() as cur:
            cur.execute("""
                SELECT v.id, v.date, v.material, v.spent,
                       COALESCE(u.username, '—') AS author,
                       v.discount,
                       COALESCE(string_agg(t.name, ', ' ORDER BY t.name), '') AS tags
                FROM visits v
                LEFT JOIN users u ON u.id = v.created_by
                LEFT JOIN visit_tags vt ON vt.visit_id = v.id
                LEFT JOIN tags t ON t.id = vt.tag_id
                WHERE v.location_id = %s
                GROUP BY v.id, v.date, v.material, v.spent, v.discount, u.username
                ORDER BY v.date DESC, v.id DESC
                LIMIT 500
            """, (location_id,))
            rows = cur.fetchall()

        html = """
        {{ css|safe }}
        <div class="wrap">
          <div class="top">
            <div>
              <h1>Визиты</h1>
              <div class="muted">{{ loc_name }}</div>
            </div>
            <div class="actions">
              <a class="btn ghost" href="{{ url_for('home') }}">← К локациям</a>
              <a class="btn primary" href="{{ url_for('stats', location_id=location_id) }}">Аналитика</a>
              <a class="btn success" href="{{ url_for('new_visit', location_id=location_id) }}">Добавить визит</a>
              <a class="btn danger" href="{{ url_for('logout') }}">Выйти</a>
            </div>
          </div>

          {% with messages = get_flashed_messages() %}
            {% if messages %}
              <div class="flash">
                {% for m in messages %}<div>{{ m }}</div>{% endfor %}
              </div>
            {% endif %}
          {% endwith %}

          {% if not rows %}
            <div class="box">Пока нет визитов для этой локации.</div>
          {% else %}
            <table>
              <tr>
                <th style="width:70px;">ID</th>
                <th style="width:140px;">Дата</th>
                <th>Материал</th>
                <th style="width:140px;">Сумма, ₽</th>
                <th style="width:140px;">Автор</th>
                <th style="width:140px;">Скидка, ₽</th>
                <th>Теги</th>
                <th style="width:220px;">Действия</th>
              </tr>
              {% for id, d, m, s, author, disc, tags in rows %}
                <tr>
                  <td>{{ id }}</td>
                  <td>{{ d }}</td>
                  <td>{{ m }}</td>
                  <td>{{ s }}</td>
                  <td>{{ author }}</td>
                  <td>{{ disc }}</td>
                  <td class="muted">{{ tags }}</td>
                  <td>
                    <div class="actions-mini">
                      <a class="btn xs" href="{{ url_for('edit_visit', visit_id=id) }}">Редактировать</a>
                      <form method="post" action="{{ url_for('delete_visit', visit_id=id) }}" style="margin:0;"
                            onsubmit="return confirm('Удалить визит #{{ id }}?');">
                        <input type="hidden" name="location_id" value="{location_id}">
                        <button class="btn xs danger" type="submit">Удалить</button>
                      </form>
                    </div>
                  </td>
                </tr>
              {% endfor %}
            </table>
          {% endif %}
        </div>
        """
        return render_template_string(html, css=CSS, location_id=location_id, loc_name=loc_name, rows=rows)
    finally:
        conn.close()

@app.route("/visits/new", methods=["GET", "POST"])
@login_required
def new_visit():
    location_id = request.args.get("location_id", type=int)
    if location_id is None:
        return redirect(url_for("home"))

    if request.method == "GET":
        conn = get_connection()
        try:
            loc_name = fetch_location_name(conn, location_id)
            if not loc_name:
                return redirect(url_for("home"))
            materials = fetch_materials(conn)
            tags = fetch_tags(conn)
        finally:
            conn.close()

        html = """
        {{ css|safe }}
        <div class="wrap">
          <div class="top">
            <div>
              <h1>Добавить визит</h1>
              <div class="muted">{{ loc_name }}</div>
            </div>
            <div class="actions">
              <a class="btn ghost" href="{{ url_for('home') }}">← К локациям</a>
              <a class="btn" href="{{ url_for('visits', location_id=location_id) }}">Визиты</a>
              <a class="btn primary" href="{{ url_for('stats', location_id=location_id) }}">Аналитика</a>
              <a class="btn danger" href="{{ url_for('logout') }}">Выйти</a>
            </div>
          </div>

          <div class="form">
            <form method="post" action="{{ url_for('new_visit', location_id=location_id) }}">
              <label>Дата</label>
              <input name="date" type="date" value="{{ today }}" required>

              <label>Материал</label>
              <input name="material" type="text" maxlength="200" list="materials"
                     placeholder="Например: Сертификаты" required>
              <datalist id="materials">
                {% for m in materials %}<option value="{{ m }}"></option>{% endfor %}
              </datalist>


<label>Теги</label>
<div class="muted" style="margin:-6px 0 8px;">Можно выбрать несколько.</div>
<div style="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:12px;">
  {% for tid, tname in tags %}
    <label style="display:flex; gap:8px; align-items:center; padding:6px 10px; border:1px solid #e6e9ef; border-radius:999px; background:#fff;">
      <input type="checkbox" name="tag_ids" value="{{ tid }}">
      {{ tname }}
    </label>
  {% endfor %}
  {% if not tags %}<div class="muted">Тегов пока нет.</div>{% endif %}
</div>

<label>Новые теги (через запятую)</label>
<input name="new_tags" type="text" maxlength="400" placeholder="например: Срочно, Безнал, Повторный визит">

              <div class="row">
                <div>
                  <label>Сумма, ₽</label>
                  <input name="spent" type="number" step="1" min="0" value="0" required>
                </div>
                <div>
                  <label>Скидка, ₽</label>
                  <input name="discount" type="number" step="1" min="0" value="0">
                </div>
              </div>

              <div class="actions" style="margin-top:12px;">
                <button class="btn success" type="submit">Сохранить</button>
                <a class="btn" href="{{ url_for('visits', location_id=location_id) }}">Отмена</a>
              </div>
            </form>
          </div>
        </div>
        """
        return render_template_string(
            html,
            css=CSS,
            location_id=location_id,
            loc_name=loc_name,
            today=dt_date.today().isoformat(),
            materials=materials,
            tags=tags
        )

    visit_date = request.form.get("date")
    material = (request.form.get("material") or "").strip()

    selected_tag_ids = [int(x) for x in request.form.getlist("tag_ids") if str(x).isdigit()]
    new_tags_raw = (request.form.get("new_tags") or "").strip()
    spent = request.form.get("spent", type=int) or 0
    discount = request.form.get("discount", type=int) or 0

    if not material:
        return "Материал обязателен", 400

    conn = get_connection()
    try:
        loc_name = fetch_location_name(conn, location_id)
        if not loc_name:
            return redirect(url_for("home"))

        
        with conn.cursor() as cur:
            cur.execute("""
        INSERT INTO visits (location_id, date, material, spent, discount, created_by)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (location_id, visit_date, material, spent, discount, session["user_id"]))
            new_visit_id = int(cur.fetchone()[0])

        all_tag_ids = set(selected_tag_ids)
        if new_tags_raw:
            for part in new_tags_raw.split(","):
                name = part.strip()
                if name:
                    try:
                        all_tag_ids.add(upsert_tag(conn, name))
                    except Exception:
                        pass
        set_visit_tags(conn, new_visit_id, sorted(all_tag_ids))

        conn.commit()
        flash("Визит добавлен ✅")
        return redirect(url_for("visits", location_id=location_id))
    except Exception as e:
        conn.rollback()
        return f"Ошибка добавления визита: {e}", 400
    finally:
        conn.close()

@app.route("/visits/<int:visit_id>/edit", methods=["GET", "POST"])
@login_required
def edit_visit(visit_id: int):
    conn = get_connection()
    try:
        v = fetch_visit(conn, visit_id)
        if not v:
            flash("Визит не найден.")
            return redirect(url_for("home"))

        _id, location_id, v_date, material, spent, discount = v
        loc_name = fetch_location_name(conn, location_id) or f"Локация {location_id}"

        if request.method == "GET":
            materials = fetch_materials(conn)
            tags = fetch_tags(conn)
            selected = fetch_visit_tag_ids(conn, visit_id)
            html = """
            {{ css|safe }}
            <div class="wrap">
              <div class="top">
                <div>
                  <h1>Редактировать визит #{visit_id}</h1>
                  <div class="muted">{{ loc_name }}</div>
                </div>
                <div class="actions">
                  <a class="btn ghost" href="{{ url_for('home') }}">← К локациям</a>
                  <a class="btn" href="{{ url_for('visits', location_id=location_id) }}">Визиты</a>
                  <a class="btn primary" href="{{ url_for('stats', location_id=location_id) }}">Аналитика</a>
                  <a class="btn danger" href="{{ url_for('logout') }}">Выйти</a>
            </div>
              </div>

              <div class="form">
                <form method="post" action="{{ url_for('edit_visit', visit_id=visit_id) }}">
                  <input type="hidden" name="location_id" value="{location_id}">

                  <label>Дата</label>
                  <input name="date" type="date" value="{v_date.isoformat()}" required>

                  <label>Материал</label>
                  <input name="material" type="text" maxlength="200" list="materials"
                         value="{{ material }}" required>
                  <datalist id="materials">
                    {% for m in materials %}<option value="{{ m }}"></option>{% endfor %}
                  </datalist>

                  <div class="row">
                    <div>
                      <label>Сумма, ₽</label>
                      <input name="spent" type="number" step="1" min="0" value="{int(spent or 0)}" required>
                    </div>
                    <div>
                      <label>Скидка, ₽</label>
                      <input name="discount" type="number" step="1" min="0" value="{int(discount or 0)}">
                    </div>
                  </div>

                  <div class="actions" style="margin-top:12px;">
                    <button class="btn success" type="submit">Сохранить</button>
                    <a class="btn" href="{{ url_for('visits', location_id=location_id) }}">Отмена</a>
                  </div>
                </form>
              </div>
            </div>
            """
            return render_template_string(
                html,
                css=CSS,
                visit_id=visit_id,
                location_id=location_id,
                material=material,
                materials=materials
            )

        # POST
        location_id_post = request.form.get("location_id", type=int) or location_id
        visit_date = request.form.get("date")
        material_new = (request.form.get("material") or "").strip()

        selected_tag_ids = [int(x) for x in request.form.getlist("tag_ids") if str(x).isdigit()]
        new_tags_raw = (request.form.get("new_tags") or "").strip()
        spent_new = request.form.get("spent", type=int) or 0
        discount_new = request.form.get("discount", type=int) or 0

        if not material_new:
            return "Материал обязателен", 400

        with conn.cursor() as cur:
            cur.execute("""
        UPDATE visits
        SET date = %s, material = %s, spent = %s, discount = %s
        WHERE id = %s
    """, (visit_date, material_new, spent_new, discount_new, visit_id))

        all_tag_ids = set(selected_tag_ids)
        if new_tags_raw:
            for part in new_tags_raw.split(","):
                name = part.strip()
                if name:
                    try:
                        all_tag_ids.add(upsert_tag(conn, name))
                    except Exception:
                        pass
        set_visit_tags(conn, visit_id, sorted(all_tag_ids))

        conn.commit()
        flash(f"Визит #{visit_id} обновлён ✨")
        return redirect(url_for("visits", location_id=location_id_post))

    except Exception as e:
        conn.rollback()
        return f"Ошибка редактирования визита: {e}", 400
    finally:
        conn.close()

@app.route("/visits/<int:visit_id>/delete", methods=["POST"])
@login_required
def delete_visit(visit_id: int):
    location_id = request.form.get("location_id", type=int)

    conn = get_connection()
    try:
        # если location_id не пришёл — вытащим из БД
        if location_id is None:
            v = fetch_visit(conn, visit_id)
            if v:
                location_id = v[1]

        with conn.cursor() as cur:
            cur.execute("DELETE FROM visits WHERE id = %s", (visit_id,))
        conn.commit()

        flash(f"Визит #{visit_id} удалён 🗑️")
        if location_id:
            return redirect(url_for("visits", location_id=location_id))
        return redirect(url_for("home"))
    except Exception as e:
        conn.rollback()
        return f"Ошибка удаления визита: {e}", 400
    finally:
        conn.close()

@app.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    conn = get_connection()
    try:
        roles = fetch_roles(conn)

        if request.method == "POST":
            action = request.form.get("action") or ""
            if action == "create":
                username = (request.form.get("username") or "").strip()
                password = request.form.get("password") or ""
                full_name = (request.form.get("full_name") or "").strip() or None
                role = (request.form.get("role") or "user").strip()
                if role not in roles:
                    role = "user"

                if not username or not password:
                    flash("Нужно заполнить логин и пароль.")
                else:
                    try:
                        create_user(conn, username, password, full_name, role)
                        conn.commit()
                        flash("Пользователь добавлен ✅")
                    except Exception as e:
                        conn.rollback()
                        flash(f"Ошибка добавления пользователя: {e}")

            elif action == "set_role":
                user_id = request.form.get("user_id", type=int)
                role = (request.form.get("role") or "user").strip()
                if role not in roles:
                    role = "user"
                if user_id:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("UPDATE users SET role=%s WHERE id=%s", (role, user_id))
                        conn.commit()
                        flash("Роль обновлена ✅")
                    except Exception as e:
                        conn.rollback()
                        flash(f"Ошибка обновления роли: {e}")
            if action == "delete":
                user_id = request.form.get("user_id", type=int)

                if not user_id:
                    flash("Не выбран пользователь.")
                elif user_id == session.get("user_id"):
                    flash("Нельзя удалить самого себя.")
                else:
                    try:
                        with conn.cursor() as cur:
                            cur.execute("SELECT role FROM users WHERE id=%s", (user_id,))
                            row = cur.fetchone()
                            if not row:
                                raise ValueError("Пользователь не найден")

                            role = row[0]
                            if role == "admin":
                                cur.execute("SELECT COUNT(*) FROM users WHERE role='admin';")
                                admins = int(cur.fetchone()[0])
                                if admins <= 1:
                                    raise ValueError("Нельзя удалить последнего администратора")

                            # чтобы не упасть по внешнему ключу
                            cur.execute("UPDATE visits SET created_by = NULL WHERE created_by = %s", (user_id,))
                            cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
                        conn.commit()
                        flash("Пользователь удалён ✅")
                    except Exception as e:
                        conn.rollback()
                        flash(f"Ошибка удаления пользователя: {e}")


        rows = list_users(conn)
    finally:
        conn.close()

    return render_template_string(CSS + """
    <div class="wrap">
      <div class="top">
        <div>
          <h1>Пользователи</h1>
          <div class="muted">Добавление и управление ролями (только admin)</div>
        </div>
        <div class="actions">
          <a class="btn" href="{{ url_for('home') }}">На главную</a>
          <a class="btn danger" href="{{ url_for('logout') }}">Выйти</a>
        </div>
      </div>

      {% with messages = get_flashed_messages() %}
        {% if messages %}
          <div class="flash">
            {% for msg in messages %}<div>{{ msg }}</div>{% endfor %}
          </div>
        {% endif %}
      {% endwith %}

      <div class="grid" style="grid-template-columns: 1fr 1fr;">
        <div class="box">
          <h2 style="margin-bottom:10px;">Добавить пользователя</h2>
          <form method="post">
            <input type="hidden" name="action" value="create">

            <label>Логин</label>
            <input name="username" type="text" maxlength="80" required>

            <label>Пароль</label>
            <input name="password" type="password" minlength="4" required>

            <label>ФИО</label>
            <input name="full_name" type="text" maxlength="200" placeholder="необязательно">

            <label>Роль</label>
            <select name="role">
              {% for r in roles %}
                <option value="{{ r }}">{{ r }}</option>
              {% endfor %}
            </select>

            <div class="actions" style="margin-top:12px;">
              <button class="btn success" type="submit">Добавить</button>
            </div>
          </form>
        </div>

        <div class="box">
          <h2 style="margin-bottom:10px;">Список</h2>
          <table>
            <thead>
              <tr>
                <th style="width:70px;">ID</th>
                <th>Логин</th>
                <th>ФИО</th>
                <th style="width:220px;">Роль</th>
                <th style="width:140px;">Удалить</th>
              </tr>
            </thead>
            <tbody>
              {% for id, username, role, full_name in rows %}
                <tr>
                  <td>{{ id }}</td>
                  <td>{{ username }}</td>
                  <td>{{ full_name }}</td>
                  <td>
                    <form method="post" style="display:flex; gap:8px; align-items:center;">
                      <input type="hidden" name="action" value="set_role">
                      <input type="hidden" name="user_id" value="{{ id }}">
                      <select name="role">
                        {% for r in roles %}
                          <option value="{{ r }}" {% if r == role %}selected{% endif %}>{{ r }}</option>
                        {% endfor %}
                      </select>
                      <button class="btn small" type="submit">OK</button>
                    </form>
                  </td>
                </td>
                  <td>
                    {% if id != session.get('user_id') %}
                      <form method="post" onsubmit="return confirm('Удалить пользователя?');">
                        <input type="hidden" name="action" value="delete">
                        <input type="hidden" name="user_id" value="{{ id }}">
                        <button class="btn small danger" type="submit">Удалить</button>
                      </form>
                    {% else %}
                      <span class="muted">Это вы</span>
                    {% endif %}
                  </td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>
    """, rows=rows, roles=roles)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template_string(CSS + """
        <div class="wrap">
          <div class="top">
            <div>
              <h1>Вход</h1>
              <div class="muted">Введите логин и пароль</div>
            </div>
          </div>

          {% with messages = get_flashed_messages() %}
            {% if messages %}
              <div class="flash">
                {% for m in messages %}<div>{{ m }}</div>{% endfor %}
              </div>
            {% endif %}
          {% endwith %}

          <div class="form">
            <form method="post">
              <label>Логин</label>
              <input name="username" required>
              <label>Пароль</label>
              <input name="password" type="password" required>
              <div class="actions" style="margin-top:12px;">
                <button class="btn success" type="submit">Войти</button>
              </div>
            </form>
          </div>
        </div>
        """)

    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""

    conn = get_connection()
    try:
        user = fetch_user_by_username(conn, username)
        if not user:
            flash("Неверный логин или пароль")
            return redirect(url_for("login"))

        user_id, _, password_hash, role, full_name = user
        if not check_password_hash(password_hash, password):
            flash("Неверный логин или пароль")
            return redirect(url_for("login"))

        session["user_id"] = user_id
        session["role"] = role
        session["full_name"] = full_name or username
        flash("Вы вошли ✅")
        return redirect(url_for("home"))
    finally:
        conn.close()

@app.route("/logout")
@app.route("/logout/")
def logout():
    session.clear()
    flash("Вы вышли из системы")
    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
