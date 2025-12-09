from flask import Flask, render_template_string, request, redirect, url_for, flash
import psycopg2
from datetime import date as dt_date
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

app = Flask(__name__)
app.secret_key = "dev"

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
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

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

def fetch_visit(conn, visit_id: int):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, location_id, date, material, spent, discount
            FROM visits
            WHERE id = %s
        """, (visit_id,))
        return cur.fetchone()

@app.route("/", methods=["GET"])
def home():
    conn = get_connection()
    try:
        locations = fetch_locations_with_counts(conn)
        html = f"""
        {CSS}
        <div class="wrap">
          <div class="top">
            <div>
              <h1>Локации</h1>
              <div class="muted">Быстрый переход к аналитике, визитам и добавлению</div>
            </div>
          </div>

          {{% if not locations %}}
            <div class="box">Локаций пока нет.</div>
          {{% else %}}
            <div class="grid">
              {{% for id, name, cnt in locations %}}
                <div class="card">
                  <div class="title">{{{{ name }}}}</div>
                  <div class="row" style="align-items:center; margin-top:8px;">
                    <div class="badge"><span class="dot"></span> ID: {{{{ id }}}}</div>
                    <div class="badge"><span class="dot" style="background:var(--accent)"></span> Визитов: {{{{ cnt }}}}</div>
                  </div>
                  <div class="actions" style="margin-top:12px;">
                    <a class="btn primary" href="{{{{ url_for('stats', location_id=id) }}}}">Аналитика</a>
                    <a class="btn" href="{{{{ url_for('visits', location_id=id) }}}}">Визиты</a>
                    <a class="btn success" href="{{{{ url_for('new_visit', location_id=id) }}}}">Добавить визит</a>
                  </div>
                </div>
              {{% endfor %}}
            </div>
          {{% endif %}}
        </div>
        """
        return render_template_string(html, locations=locations)
    finally:
        conn.close()

@app.route("/stats", methods=["GET"])
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

        html = f"""
        {CSS}
        <div class="wrap">
          <div class="top">
            <div>
              <h1>Аналитика</h1>
              <div class="muted">{loc_name}</div>
            </div>
            <div class="actions">
              <a class="btn ghost" href="{{{{ url_for('home') }}}}">← К локациям</a>
              <a class="btn" href="{{{{ url_for('visits', location_id=location_id) }}}}">Визиты</a>
              <a class="btn success" href="{{{{ url_for('new_visit', location_id=location_id) }}}}">Добавить визит</a>
            </div>
          </div>

          {{% with messages = get_flashed_messages() %}}
            {{% if messages %}}
              <div class="flash">
                {{% for m in messages %}}<div>{{{{ m }}}}</div>{{% endfor %}}
              </div>
            {{% endif %}}
          {{% endwith %}}

          <div class="box">
            <h2 style="margin:0 0 10px 0;">Статистика</h2>
            <div class="row">
              <div><span class="muted">Визитов</span><div style="font-size:22px;font-weight:900;">{{{{ s.visits }}}}</div></div>
              <div><span class="muted">Потрачено</span><div style="font-size:22px;font-weight:900;">{{{{ s.spent }}}} ₽</div></div>
              <div><span class="muted">Скидок</span><div style="font-size:22px;font-weight:900;">{{{{ s.discount }}}} ₽</div></div>
            </div>
            <div style="margin-top:12px;" class="row">
              <div><span class="muted">Средний чек</span><div style="font-size:18px;font-weight:900;">{{{{ s.avg_check }}}} ₽</div></div>
              <div><span class="muted">Средняя скидка</span><div style="font-size:18px;font-weight:900;">{{{{ s.avg_discount }}}} ₽</div></div>
            </div>
            <div class="small" style="margin-top:10px;">Данные пересчитываются сразу после добавления/редактирования/удаления визита.</div>
          </div>
        </div>
        """
        return render_template_string(html, location_id=location_id, s=s)
    finally:
        conn.close()

@app.route("/visits", methods=["GET"])
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
                SELECT id, date, material, spent, discount
                FROM visits
                WHERE location_id = %s
                ORDER BY date DESC, id DESC
                LIMIT 500
            """, (location_id,))
            rows = cur.fetchall()

        html = f"""
        {CSS}
        <div class="wrap">
          <div class="top">
            <div>
              <h1>Визиты</h1>
              <div class="muted">{loc_name}</div>
            </div>
            <div class="actions">
              <a class="btn ghost" href="{{{{ url_for('home') }}}}">← К локациям</a>
              <a class="btn primary" href="{{{{ url_for('stats', location_id=location_id) }}}}">Аналитика</a>
              <a class="btn success" href="{{{{ url_for('new_visit', location_id=location_id) }}}}">Добавить визит</a>
            </div>
          </div>

          {{% with messages = get_flashed_messages() %}}
            {{% if messages %}}
              <div class="flash">
                {{% for m in messages %}}<div>{{{{ m }}}}</div>{{% endfor %}}
              </div>
            {{% endif %}}
          {{% endwith %}}

          {{% if not rows %}}
            <div class="box">Пока нет визитов для этой локации.</div>
          {{% else %}}
            <table>
              <tr>
                <th style="width:70px;">ID</th>
                <th style="width:140px;">Дата</th>
                <th>Материал</th>
                <th style="width:140px;">Сумма, ₽</th>
                <th style="width:140px;">Скидка, ₽</th>
                <th style="width:220px;">Действия</th>
              </tr>
              {{% for id, d, m, s, disc in rows %}}
                <tr>
                  <td>{{{{ id }}}}</td>
                  <td>{{{{ d }}}}</td>
                  <td>{{{{ m }}}}</td>
                  <td>{{{{ s }}}}</td>
                  <td>{{{{ disc }}}}</td>
                  <td>
                    <div class="actions-mini">
                      <a class="btn xs" href="{{{{ url_for('edit_visit', visit_id=id) }}}}">Редактировать</a>
                      <form method="post" action="{{{{ url_for('delete_visit', visit_id=id) }}}}" style="margin:0;"
                            onsubmit="return confirm('Удалить визит #{{{{ id }}}}?');">
                        <input type="hidden" name="location_id" value="{location_id}">
                        <button class="btn xs danger" type="submit">Удалить</button>
                      </form>
                    </div>
                  </td>
                </tr>
              {{% endfor %}}
            </table>
          {{% endif %}}
        </div>
        """
        return render_template_string(html, location_id=location_id, rows=rows)
    finally:
        conn.close()

@app.route("/visits/new", methods=["GET", "POST"])
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
        finally:
            conn.close()

        html = f"""
        {CSS}
        <div class="wrap">
          <div class="top">
            <div>
              <h1>Добавить визит</h1>
              <div class="muted">{{{{ loc_name }}}}</div>
            </div>
            <div class="actions">
              <a class="btn ghost" href="{{{{ url_for('home') }}}}">← К локациям</a>
              <a class="btn" href="{{{{ url_for('visits', location_id=location_id) }}}}">Визиты</a>
              <a class="btn primary" href="{{{{ url_for('stats', location_id=location_id) }}}}">Аналитика</a>
            </div>
          </div>

          <div class="form">
            <form method="post" action="{{{{ url_for('new_visit', location_id=location_id) }}}}">
              <label>Дата</label>
              <input name="date" type="date" value="{{{{ today }}}}" required>

              <label>Материал</label>
              <input name="material" type="text" maxlength="200" list="materials"
                     placeholder="Например: Сертификаты" required>
              <datalist id="materials">
                {{% for m in materials %}}<option value="{{{{ m }}}}"></option>{{% endfor %}}
              </datalist>

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
                <a class="btn" href="{{{{ url_for('visits', location_id=location_id) }}}}">Отмена</a>
              </div>
            </form>
          </div>
        </div>
        """
        return render_template_string(
            html,
            location_id=location_id,
            loc_name=loc_name,
            today=dt_date.today().isoformat(),
            materials=materials
        )

    visit_date = request.form.get("date")
    material = (request.form.get("material") or "").strip()
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
                INSERT INTO visits (location_id, date, material, spent, discount)
                VALUES (%s, %s, %s, %s, %s)
            """, (location_id, visit_date, material, spent, discount))
        conn.commit()
        flash("Визит добавлен ✅")
        return redirect(url_for("visits", location_id=location_id))
    except Exception as e:
        conn.rollback()
        return f"Ошибка добавления визита: {e}", 400
    finally:
        conn.close()

@app.route("/visits/<int:visit_id>/edit", methods=["GET", "POST"])
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
            html = f"""
            {CSS}
            <div class="wrap">
              <div class="top">
                <div>
                  <h1>Редактировать визит #{visit_id}</h1>
                  <div class="muted">{loc_name}</div>
                </div>
                <div class="actions">
                  <a class="btn ghost" href="{{{{ url_for('home') }}}}">← К локациям</a>
                  <a class="btn" href="{{{{ url_for('visits', location_id=location_id) }}}}">Визиты</a>
                  <a class="btn primary" href="{{{{ url_for('stats', location_id=location_id) }}}}">Аналитика</a>
                </div>
              </div>

              <div class="form">
                <form method="post" action="{{{{ url_for('edit_visit', visit_id=visit_id) }}}}">
                  <input type="hidden" name="location_id" value="{location_id}">

                  <label>Дата</label>
                  <input name="date" type="date" value="{v_date.isoformat()}" required>

                  <label>Материал</label>
                  <input name="material" type="text" maxlength="200" list="materials"
                         value="{{{{ material }}}}" required>
                  <datalist id="materials">
                    {{% for m in materials %}}<option value="{{{{ m }}}}"></option>{{% endfor %}}
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
                    <a class="btn" href="{{{{ url_for('visits', location_id=location_id) }}}}">Отмена</a>
                  </div>
                </form>
              </div>
            </div>
            """
            return render_template_string(
                html,
                visit_id=visit_id,
                location_id=location_id,
                material=material,
                materials=materials
            )

        # POST
        location_id_post = request.form.get("location_id", type=int) or location_id
        visit_date = request.form.get("date")
        material_new = (request.form.get("material") or "").strip()
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
        conn.commit()
        flash(f"Визит #{visit_id} обновлён ✨")
        return redirect(url_for("visits", location_id=location_id_post))

    except Exception as e:
        conn.rollback()
        return f"Ошибка редактирования визита: {e}", 400
    finally:
        conn.close()

@app.route("/visits/<int:visit_id>/delete", methods=["POST"])
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
