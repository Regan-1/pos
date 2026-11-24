import os
import secrets
import sqlite3
import uuid
from datetime import date
from markupsafe import Markup
from flask import Flask, abort, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-this")
DATABASE = os.environ.get("DATABASE", "bus_booking.db")


def connect_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    with connect_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS buses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                departure TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                fare REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT UNIQUE NOT NULL,
                bus_id INTEGER NOT NULL REFERENCES buses(id),
                travel_date TEXT NOT NULL,
                passenger_name TEXT NOT NULL,
                seats INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS bookings_bus_date
                ON bookings(bus_id, travel_date);
        """)

        if db.execute("SELECT COUNT(*) FROM buses").fetchone()[0] == 0:
            db.executemany(
                """INSERT INTO buses (origin, destination, departure, capacity, fare)
                   VALUES (?, ?, ?, ?, ?)""",
                [
                    ("New York", "Boston", "08:00", 40, 29.99),
                    ("New York", "Boston", "13:30", 40, 34.99),
                    ("Boston", "New York", "09:00", 40, 29.99),
                    ("Chicago", "Detroit", "07:45", 36, 24.50),
                    ("Detroit", "Chicago", "15:00", 36, 24.50),
                    ("Los Angeles", "San Diego", "10:15", 44, 19.99),
                ],
            )


def available_seats(db, bus_id, travel_date):
    row = db.execute(
        """SELECT b.capacity - COALESCE(SUM(bookings.seats), 0) AS available
           FROM buses b
           LEFT JOIN bookings
             ON bookings.bus_id = b.id AND bookings.travel_date = ?
           WHERE b.id = ?
           GROUP BY b.id""",
        (travel_date, bus_id),
    ).fetchone()
    return row["available"] if row else 0


def valid_travel_date(value):
    try:
        parsed = date.fromisoformat(value)
        return parsed.isoformat() if parsed >= date.today() else None
    except (TypeError, ValueError):
        return None


def csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(24)
    return session["_csrf_token"]


BASE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ title }} | Bus Booking</title>
  <style>
    body { font: 16px system-ui, sans-serif; max-width: 900px; margin: 32px auto;
           padding: 0 16px; color: #18212f; background: #f5f7fa; }
    header, .card { background: white; padding: 20px; border-radius: 12px;
                    margin-bottom: 16px; box-shadow: 0 2px 8px #0000000d; }
    header a { color: #1769aa; text-decoration: none; font-weight: bold; }
    h1 { margin-top: 0; }
    label { display: block; margin: 12px 0 5px; }
    input, button { font: inherit; padding: 10px; border: 1px solid #ccd3dd;
                    border-radius: 7px; }
    button, .button { background: #1769aa; color: white; border: 0;
                      cursor: pointer; text-decoration: none; padding: 10px 14px;
                      border-radius: 7px; display: inline-block; }
    .search { display: flex; gap: 12px; flex-wrap: wrap; align-items: end; }
    .error { color: #a32121; }
    .muted { color: #647184; }
  </style>
</head>
<body>
  <header><a href="{{ url_for('index') }}">🚌 Bus Booking</a></header>
  {{ body|safe }}
</body>
</html>
"""


def page(title, template, **context):
    body = render_template_string(template, **context)
    return render_template_string(BASE, title=title, body=Markup(body))


@app.get("/")
def index():
    travel_date = valid_travel_date(request.args.get("date")) or date.today().isoformat()
    origin = request.args.get("origin", "").strip()
    destination = request.args.get("destination", "").strip()

    with connect_db() as db:
        buses = db.execute(
            """SELECT * FROM buses
               WHERE (? = '' OR lower(origin) = lower(?))
                 AND (? = '' OR lower(destination) = lower(?))
               ORDER BY departure""",
            (origin, origin, destination, destination),
        ).fetchall()

        bus_list = []
        for bus in buses:
            bus_list.append({
                "bus": bus,
                "available": available_seats(db, bus["id"], travel_date),
            })

    return page("Find a bus", """
      <section class="card">
        <h1>Find your bus</h1>
        <form class="search" method="get">
          <div>
            <label for="origin">From</label>
            <input id="origin" name="origin" value="{{ origin }}" placeholder="City">
          </div>
          <div>
            <label for="destination">To</label>
            <input id="destination" name="destination" value="{{ destination }}" placeholder="City">
          </div>
          <div>
            <label for="date">Travel date</label>
            <input id="date" type="date" name="date" value="{{ travel_date }}" required>
          </div>
          <button type="submit">Search buses</button>
        </form>
      </section>

      {% for item in bus_list %}
        {% set bus = item.bus %}
        <section class="card">
          <h2>{{ bus.origin }} → {{ bus.destination }}</h2>
          <p>Departure: {{ bus.departure }} · Fare: ${{ "%.2f"|format(bus.fare) }} per seat</p>
          <p>{{ item.available }} seats available on {{ travel_date }}</p>
          {% if item.available > 0 %}
            <a class="button" href="{{ url_for('book', bus_id=bus.id, travel_date=travel_date) }}">
              Book seats
            </a>
          {% else %}
            <span class="muted">Fully booked</span>
          {% endif %}
        </section>
      {% else %}
        <section class="card">No buses match that search.</section>
      {% endfor %}
    """, bus_list=bus_list, travel_date=travel_date, origin=origin,
       destination=destination)


@app.route("/book/<int:bus_id>", methods=["GET", "POST"])
def book(bus_id):
    travel_date = valid_travel_date(
        request.values.get("travel_date") or request.args.get("travel_date")
    )
    if not travel_date:
        abort(400, "Choose a valid date today or later.")

    with connect_db() as db:
        bus = db.execute("SELECT * FROM buses WHERE id = ?", (bus_id,)).fetchone()
        if not bus:
            abort(404)

        available = available_seats(db, bus_id, travel_date)

        if request.method == "POST":
            submitted_token = request.form.get("csrf_token", "")
            if not secrets.compare_digest(submitted_token, csrf_token()):
                abort(400, "Invalid form token. Please reload the page.")

            passenger_name = request.form.get("passenger_name", "").strip()
            try:
                seats = int(request.form.get("seats", "0"))
            except ValueError:
                seats = 0

            error = None
            if not passenger_name or len(passenger_name) > 80:
                error = "Enter a passenger name (up to 80 characters)."
            elif seats < 1:
                error = "Choose at least one seat."

            if not error:
                # Lock before checking availability so simultaneous bookings
                # cannot reserve more seats than the bus capacity.
                db.execute("BEGIN IMMEDIATE")
                available = available_seats(db, bus_id, travel_date)

                if seats > available:
                    db.rollback()
                    error = f"Only {available} seat(s) remain. Please try again."
                else:
                    reference = uuid.uuid4().hex[:12].upper()
                    db.execute(
                        """INSERT INTO bookings
                           (reference, bus_id, travel_date, passenger_name, seats)
                           VALUES (?, ?, ?, ?, ?)""",
                        (reference, bus_id, travel_date, passenger_name, seats),
                    )
                    db.commit()

                    return page("Booking confirmed", """
                      <section class="card">
                        <h1>Booking confirmed</h1>
                        <p>Your booking reference is <strong>{{ reference }}</strong>.</p>
                        <p>{{ bus.origin }} → {{ bus.destination }} · {{ travel_date }}</p>
                        <p>Departure: {{ bus.departure }} · Passenger: {{ passenger_name }}</p>
                        <p>Seats: {{ seats }} · Total: ${{ "%.2f"|format(bus.fare * seats) }}</p>
                        <a class="button" href="{{ url_for('index') }}">Find another bus</a>
                      </section>
                    """, reference=reference, bus=bus, travel_date=travel_date,
                       passenger_name=passenger_name, seats=seats)

            return page("Book seats", BOOKING_TEMPLATE, bus=bus,
                        travel_date=travel_date, available=available,
                        error=error, passenger_name=passenger_name,
                        selected_seats=seats)

    return page("Book seats", BOOKING_TEMPLATE, bus=bus,
                travel_date=travel_date, available=available,
                error=None, passenger_name="", selected_seats=1)


BOOKING_TEMPLATE = """
<section class="card">
  <h1>Book {{ bus.origin }} → {{ bus.destination }}</h1>
  <p>{{ travel_date }} · Departure {{ bus.departure }} ·
     ${{ "%.2f"|format(bus.fare) }} per seat</p>
  <p>{{ available }} seats available</p>

  {% if error %}<p class="error">{{ error }}</p>{% endif %}

  {% if available > 0 %}
    <form method="post">
      <input type="hidden" name="travel_date" value="{{ travel_date }}">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

      <label for="passenger_name">Passenger name</label>
      <input id="passenger_name" name="passenger_name" maxlength="80"
             value="{{ passenger_name }}" required>

      <label for="seats">Number of seats</label>
      <input id="seats" type="number" name="seats" min="1"
             max="{{ available }}" value="{{ selected_seats }}" required>

      <p><button type="submit">Confirm booking</button></p>
    </form>
  {% else %}
    <p class="error">This bus is fully booked for that date.</p>
  {% endif %}
  <a href="{{ url_for('index', date=travel_date) }}">Back to search</a>
</section>
"""


init_db()

if __name__ == "__main__":
    app.run(debug=True)