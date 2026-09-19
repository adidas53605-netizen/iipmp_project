# IIPMP — Integrated Infrastructure Project Monitoring Platform

Production-grade Django web application for real-time monitoring, financial tracking, risk assessment, and milestone management of infrastructure projects.

---

## 🚀 Section 1 & 2 Upgrade Highlights

### Security & Authentication
- **Password Complexity**: Minimum 8 characters with $\ge 1$ uppercase, $\ge 1$ lowercase, $\ge 1$ digit, and $\ge 1$ special character (`!@#$%^&*(),.?":{}|<>`).
- **Account Lockout**: 5 failed login attempts lock the account for 15 minutes automatically.
- **Role-Based Access Control (RBAC)**: 5 roles (`Admin`, `Ministry Official`, `Field Officer`, `Auditor`, `Public Viewer`) enforced via `@role_required` view decorators.
- **HttpOnly Cookies**: Session & CSRF cookies configured with `HttpOnly = True` and `SameSite = Lax`.
- **Dedicated Admin Portal**: `/admin-login/` with MFA (TOTP) code prompt.

### Production Infrastructure & Reliability
- **Render Paid Tier Setup**: Configured in `render.yaml` with `plan: starter` (always-on, zero cold starts) + managed PostgreSQL instance.
- **Automated Database Backups**: Timestamped SQLite backups with automatic 7-day retention management via `python manage.py backup_db`.
- **Database Indexes**: Indexed `status`, `risk_level`, `state`, `district`, `ministry`, `expected_completion`, and compound query paths.
- **Secret Isolation**: Hardcoded keys removed; configured via `.env.example`.

---

## 🛠️ Deployment & Paid Tier Setup (Render)

1. **Connect Repository to Render**:
   - Navigate to [Render Dashboard](https://dashboard.render.com).
   - Select **New Blueprint Instance** and connect this repository.
   - Render automatically detects `render.yaml`.

2. **Verify Paid Tier Plan**:
   - Ensure service plan is set to **Starter** or **Standard** (`plan: starter`).
   - The instance will remain always-on 24/7 without dynamic spin-downs or cold start delays.

3. **PostgreSQL Migration Path**:
   - Render provisions `iipmp-postgres-db` automatically from `render.yaml`.
   - Django connects using `dj_database_url` via the `DATABASE_URL` environment variable.
   - Run initial migrations: `python manage.py migrate`.
   - Load seed data: `python manage.py loaddata seed_data.json` (or `python manage.py csv_import`).

---

## 💾 Automated Database Backups & Operations

To trigger a manual database backup or configure cron execution:

```bash
# Run backup management command (creates backup under backups/db_backup_YYYYMMDD_HHMMSS.sqlite3)
python manage.py backup_db

# Configure retention limit (e.g. keep last 14 backups)
python manage.py backup_db --keep 14
```

---

## 🧪 Running Security & System Verification Tests

```bash
# System check
python manage.py check

# Run unit tests (Security, Lockout, RBAC, Admin Portal)
python manage.py test monitoring
```
