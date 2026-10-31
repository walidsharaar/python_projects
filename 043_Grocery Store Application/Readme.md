# FreshCart · Grocery Store Management System

A full-stack web application to run a small grocery store: sell at a point-of-sale screen, manage products and
prices, browse orders and follow sales on a dashboard. Built with a Python/Flask REST API, PostgreSQL and a
dependency-free JavaScript frontend.

---

## Features

- **Sign-in and roles:** staff accounts with two roles.
  - **Administrator:** dashboard, products, staff and all sales.
  - **Cashier:** new sales and orders only.
- **Dashboard (admin):** choose 7 / 30 / 90 days.
  - KPIs (revenue, orders, average order, customers) compared with the previous period.
  - Revenue area chart with hover details and a busiest-hours heatmap.
  - Top products, top customers, sales per staff member and recent orders.
- **Point of sale:** tap product tiles to fill the cart, adjust quantities (decimals for kg/litre), search with
  Enter-to-add, and complete the sale. Totals are always calculated by the server, and each sale records who made it.
- **Orders:** searchable (customer name or `#order`), paginated list with a printable receipt panel showing who sold it.
- **Products (admin):** add, edit and delete products with an emoji icon, unit and price.
  - The icon picker suggests an emoji from the name.
  - Price changes never alter past orders, and products that were sold cannot be deleted.
- **Staff (admin):** create cashiers and admins, reset passwords, disable accounts.
- **Modern UI:** light/dark theme, responsive layout (bottom navigation on phones), keyboard accessible.
- **Documented REST API:** OpenAPI 3.1 spec with interactive Swagger docs at `/api/docs`.

## Security

- **Passwords:** stored as salted scrypt hashes; every user can change their own.
- **Sessions:** a signed, HttpOnly, SameSite=Lax cookie that expires after 12 hours by default.
  - Changing a password signs out the user's other sessions.
  - Disabling an account takes effect on its next request.
- **Lockout:** 5 wrong passwords lock an account for 5 minutes. An admin password reset lifts the lock.
- **Sign-in errors:** unknown usernames and wrong passwords get the same answer, in the same time.
- **Permissions:** checked by the API on every request; the UI only hides what the role cannot use.
- **Admins:** an admin cannot remove their own admin rights or disable themselves.
- **No default password:** setup asks you to choose the first administrator's.

Planned: inventory / stock levels.

---

## Tech Stack & Architecture

- **Backend:** Python 3.10+, Flask 3 (app factory + blueprint), psycopg 3 with a connection pool, Waitress (production WSGI server)
- **Database:** PostgreSQL (tables `users`, `uom`, `products`, `orders`, `order_details`)
- **Frontend:** single-page app in plain ES modules and modern CSS. No build step, no frameworks.
- **Architecture:** 3 tiers
  1. **UI** (`ui/`): static files served by Flask; talks to the API with `fetch`.
  2. **API / business logic** (`backend/app/`): REST endpoints, validation, error handling.
  3. **Data access** (`backend/app/repositories/`): parameterized SQL, one module per resource.

```
├── setup.bat / run.bat        one-time setup / start the app (Windows)
├── requirements.txt
├── .env.example               all settings, copy to .env
├── backend/
│   ├── server.py              entry point (Waitress, or Flask dev server with FLASK_DEBUG=1)
│   ├── init_db.py             create database user, database, tables, sample data
│   ├── schema.sql / seed.sql
│   ├── app/
│   │   ├── __init__.py        create_app(): config, JSON, routes, security headers
│   │   ├── api.py             REST endpoints  /api/v1/...
│   │   ├── auth.py            sign-in, sessions, lockout, role checks
│   │   ├── validation.py      request validation
│   │   ├── errors.py          errors -> RFC 9457 problem details
│   │   ├── db.py              connection pool
│   │   ├── config.py          settings from .env
│   │   ├── openapi.yaml       API specification
│   │   └── repositories/      SQL for uoms, products, orders, stats
│   └── tests/                 pytest: validation + API tests against Postgres
└── ui/
    ├── index.html, css/app.css
    └── js/  app.js (router), api.js, ui.js, icons.js, config.js, views/
```

---

## Quick Start (Windows)

Requirements: Python 3.10+ and PostgreSQL installed and running.

1. Double-click **`setup.bat`**. The first time it creates `.env` and stops.
2. Open `.env` and replace `change-me` in `DATABASE_URL` with a password of your choice. Save it.
3. Double-click **`setup.bat`** again. When asked, enter the password of the PostgreSQL admin user `postgres`
   (chosen when you installed PostgreSQL). It creates the database user, database, tables and sample data,
   and generates a `SECRET_KEY` in `.env`.
4. The first time, it asks you to **create the administrator account** (username, name, password).
5. Double-click **`run.bat`**, open http://127.0.0.1:5000/ and sign in. Add cashiers under **Staff**.

Existing databases are upgraded in place (new tables and columns are added; no data is deleted).

The manual steps below do the same thing on any OS.

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/your-username/grocery-store-system.git
cd grocery-store-system
```

### 1. Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
```

### 2. Configure the environment

Copy `.env.example` to `.env` and set `DATABASE_URL` to your Postgres database:

```ini
DATABASE_URL=postgresql://grocery_user:<password>@localhost:5432/grocery_db
```

All settings (pool size, host/port, log level, CORS) are documented in `.env.example`.

### 3. Create the database

```bash
cd backend
python init_db.py --create-db --seed   # first time: creates user + database (asks for the 'postgres' password)
                                       # and the first administrator account
python init_db.py --create-admin       # add another admin, or reset an admin's forgotten password
python init_db.py                      # tables only, e.g. on a production server
python init_db.py --reset --seed       # DELETE all app data and start fresh
```

### 4. Run the server

```bash
cd backend
python server.py
```

- App: <http://127.0.0.1:5000/>
- API docs: <http://127.0.0.1:5000/api/docs>
- Health check: `GET /health` returns `{"status": "ok"}` when the database is reachable

With `FLASK_DEBUG=0` (the default) the app runs on [Waitress](https://docs.pylonsproject.org/projects/waitress/);
set `FLASK_DEBUG=1` only on your own machine for auto-reload. You can also start Waitress directly:

```bash
cd backend
waitress-serve --listen=0.0.0.0:5000 server:app
```

### 5. Run the tests

```bash
cd backend
pytest                                     # validation tests
set TEST_DATABASE_URL=postgresql://...     # a separate, disposable database - it gets wiped!
pytest                                     # + API tests against Postgres
```

---

## REST API

Base URL `/api/v1`. Full specification: `/api/v1/openapi.yaml`, interactive docs: `/api/docs`.

| Method | Endpoint | Description | Success |
|---|---|---|---|
| POST | `/auth/login` | Sign in: `{username, password}`; sets the session cookie | `200` user |
| POST | `/auth/logout` | Sign out | `204` |
| GET | `/auth/me` | The signed-in user | `200` |
| PUT | `/auth/password` | Change own password: `{current_password, new_password}` | `204` |
| GET | `/users` | List staff accounts *(admin)* | `200 {items}` |
| POST | `/users` | Create: `{username, full_name, role, password}` *(admin)* | `201` + `Location` |
| PUT | `/users/{id}` | Update: `{full_name, role, is_active, password?}` *(admin)* | `200` |
| GET | `/uoms` | List units of measure | `200 {items}` |
| GET | `/products` | List products | `200 {items}` |
| POST | `/products` | Create a product: `{name, uom_id, price_per_unit}` | `201` + `Location` header |
| GET | `/products/{id}` | Get a product | `200` |
| PUT | `/products/{id}` | Replace a product (same body as POST) | `200` |
| DELETE | `/products/{id}` | Delete a product (`409` if it was sold) | `204` |
| GET | `/orders?limit=50&offset=0&q=` | Orders, newest first; `q` = customer name or `#id` | `200 {items, total, limit, offset}` |
| POST | `/orders` | Create an order: `{customer_name, items: [{product_id, quantity}]}` | `201` + `Location` header |
| GET | `/orders/{id}` | Get an order with its items | `200` |
| GET | `/stats/summary?days=30` | Period totals vs. previous period, daily sales, top products/customers, sales by staff, busiest hours *(admin)* | `200` |

Everything except login/logout requires a signed-in user (`401`). Product changes, statistics and staff
management are admin-only (`403` for cashiers). Products have an optional `icon` (emoji); orders include
`created_by_name`.

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/v1/orders \
     -H "Content-Type: application/json" \
     -d '{"customer_name": "Alice", "items": [{"product_id": 1, "quantity": 2}]}'
```

- Bodies are JSON only (`415` otherwise). Prices and totals are calculated by the server; any sent by the client are ignored.
- Errors use [RFC 9457 problem details](https://www.rfc-editor.org/rfc/rfc9457) with `Content-Type: application/problem+json`:

  ```json
  {"type": "about:blank", "title": "Conflict", "status": 409, "detail": "A product named 'Tomato' already exists"}
  ```

---

## License

This project is open-source and available under the [MIT License](LICENSE).
