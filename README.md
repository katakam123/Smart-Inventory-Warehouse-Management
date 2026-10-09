# Smart Inventory & Warehouse Management System

A REST API backend built with FastAPI, SQLAlchemy, and MySQL to manage products, warehouses, stock levels, suppliers, purchase orders, sales orders, stock transfers, stock adjustments, returns, refunds, and notifications.

## Features

* JWT-based authentication
* Role-based access control
* Product, category, supplier, customer, and warehouse management
* Inventory tracking and stock movements
* Purchase and sales order management
* Warehouse stock transfers and stock adjustments
* Returns and refund processing
* Low-stock notifications and email alerts
* Audit logs and inventory reports
* Alembic database migrations
* Swagger UI API documentation

## Technology Stack

* Python 3.9+
* FastAPI
* Pydantic
* SQLAlchemy
* MySQL
* Alembic
* JWT authentication
* SMTP email notifications
* Uvicorn

## Project Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd smart_inventory_system
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```cmd
venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure MySQL

Create the database in MySQL:

```sql
CREATE DATABASE smart_inventory_db;
```

Create a local `.env` file by copying `.env.example`, then update the database username, password, host, and database name.

### 5. Configure environment variables

Example `.env.example`:

```env
DATABASE_URL=mysql+pymysql://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:3306/smart_inventory_db

SECRET_KEY=replace_with_a_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM=your_email@gmail.com
SMTP_USE_TLS=true
```

Use your own local values in `.env`. Never commit real passwords, secret keys, or email credentials.

If your database password contains special URL characters, URL-encode the password in `DATABASE_URL`.

### 6. Run database migrations

Check the current migration:

```bash
alembic current
```

View migration history:

```bash
alembic history
```

Generate a migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe your schema change"
```

Review the generated file in `alembic/versions/` before applying it.

Apply migrations:

```bash
alembic upgrade head
```

Check the current revision again:

```bash
alembic current
```

For a new migration, ensure the database is up to date before generating another revision. Do not use `alembic stamp head` to hide unapplied schema changes.

### 7. Start the API

```bash
uvicorn app.main:app --reload
```

Open the documentation:

* Swagger UI: `http://127.0.0.1:8000/docs`
* ReDoc: `http://127.0.0.1:8000/redoc`

## User Roles

The application uses these roles:

* **Admin:** administrative access, subject to endpoint permissions.
* **Inventory Manager:** inventory management, approvals, and reporting, subject to endpoint permissions.
* **Warehouse Staff:** permitted warehouse operations, subject to assigned warehouse and endpoint permissions.

Create test accounts through your implemented registration, seed, or administrative user-creation process. See the test-credentials section below.

## API Endpoints

The following routes are part of the intended API scope. Confirm the exact paths and HTTP methods against the routers registered in `app/main.py` before publishing this list.

| Module          | Endpoint examples                                                                                                             |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Authentication  | Login and token generation                                                                                                    |
| Products        | Product CRUD                                                                                                                  |
| Categories      | Category CRUD                                                                                                                 |
| Warehouses      | Warehouse CRUD                                                                                                                |
| Inventory       | Stock lookup and inventory operations                                                                                         |
| Suppliers       | Supplier CRUD                                                                                                                 |
| Purchase orders | Create, view, and receive orders                                                                                              |
| Sales orders    | Create, view, and dispatch orders                                                                                             |
| Transfers       | `POST /transfers`, `GET /transfers`, `PUT /transfers/{transfer_id}/dispatch`, `/receive`, `/cancel`                           |
| Adjustments     | `POST /adjustments`, `GET /adjustments`, `PUT /adjustments/{adjustment_id}/approve`, `/reject`                                |
| Returns         | `POST /sales-orders/{so_id}/returns`, `GET /returns`, inspection, approval, and rejection routes                              |
| Audit logs      | `GET /audit-logs`                                                                                                             |
| Reports         | `GET /reports/dashboard`, `/stock-valuation`, `/low-stock`, `/sales`, `/top-products`, `/dead-stock`, `/supplier-performance` |

For the authoritative endpoint list, use the OpenAPI documentation at `/docs`.

## SMTP Email Setup

1. Configure the SMTP variables in `.env`.
2. For Gmail, enable two-step verification and generate an app password.
3. Put the app password in `SMTP_PASSWORD`, not your regular account password.
4. Restart the API after changing environment variables.
5. Trigger each implemented notification workflow.
6. Check the recipient inbox and spam folder.
7. Capture screenshots of successfully received emails.

Required evidence:

* Low-stock alert
* Sales order dispatched
* Refund processed

Do not include passwords, tokens, or private customer data in screenshots.

## Test Credentials

Document only local development accounts that have actually been created and tested. For example:

| Role              | Test username/email            | Test password       |
| ----------------- | ------------------------------ | ------------------- |
| Admin             | Fill in after creating account | Local test password |
| Inventory Manager | Fill in after creating account | Local test password |
| Warehouse Staff   | Fill in after creating account | Local test password |

These accounts are for local development only. Do not use production credentials or reuse real passwords.

## Testing

Run automated tests, if included:

```bash
pytest -v
```

Record the tests that pass and any known limitations. Manually test protected endpoints using Swagger's **Authorize** feature and a valid JWT token.

## Screenshots and Evidence

Store project evidence in the `screenshots/` directory:

* `screenshots/swagger/` — successful API requests and responses
* `screenshots/emails/low_stock_alert.png`
* `screenshots/emails/sales_order_dispatched.png`
* `screenshots/emails/refund_processed.png`

Screenshots should come from actual successful runs of the application.

## Assumptions and Limitations

* MySQL is the configured database.
* The database schema is managed through Alembic migrations.
* Access depends on the authenticated user's role and, where applicable, assigned warehouse.
* Inventory changes should occur only after the corresponding business operation is validated and committed.
* Return eligibility, refund calculation, stock-transfer handling, and stock-adjustment approval follow the rules implemented in the services.
* Email delivery depends on valid SMTP settings and the email provider.
* Email sending and payment/refund integrations should not be described as production-ready unless they have been implemented and tested.
* Replace any planned feature or example route with the actual implemented behavior before publishing.

## Security Notes

* Keep `.env` out of version control.
* Use a strong random JWT secret.
* Never commit real SMTP credentials, access tokens, or production data.
* Use test data and development-only credentials.

## License

Add the license appropriate for your project.
