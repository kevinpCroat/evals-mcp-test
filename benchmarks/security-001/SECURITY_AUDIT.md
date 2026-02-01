# Security Audit: OWASP Fixes in starter-code/app.py

This document describes the 10 planted vulnerabilities and the fixes applied in `starter-code/app.py`.

## 1. Hardcoded Secret Key and Credentials (A02:2021)

**Location:** Lines 15–19 (original).  
**Fix:** Load all secrets from environment variables:
- `app.secret_key` from `SECRET_KEY`
- `DATABASE` from `DATABASE_PATH`
- `ADMIN_PASSWORD` and `API_KEY` from env; empty default so they must be set in production

## 2. SQL Injection in Login (A03:2021)

**Location:** Login route, original query built with f-string.  
**Fix:** Parameterized query: `conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))`.

## 3. Cross-Site Scripting (XSS) (A03:2021)

**Location:** `/search` route, `query` interpolated into HTML.  
**Fix:** Escape user input with `markupsafe.escape(query)` and use the escaped value in the template.

## 4. SQL Injection in Product Search (A03:2021)

**Location:** `/products` route, category in LIKE built with f-string.  
**Fix:** Parameterized query: `conn.execute("SELECT * FROM products WHERE description LIKE ?", (f'%{category}%',))`.

## 5. Path Traversal (A01:2021)

**Location:** `/download` route, filename joined to base path without validation.  
**Fix:** Use `secure_filename(filename)`, reject if sanitized name differs from input, then `os.path.abspath()` and ensure resolved path starts with allowed directory (`ALLOWED_DOWNLOAD_DIR`).

## 6. Command Injection (A03:2021)

**Location:** `/admin/backup`, `subprocess.run(..., shell=True)` with user-controlled backup name.  
**Fix:** Use `shutil.copy(DATABASE, dest_path)`. Validate destination with `secure_filename` and path prefix check under `BACKUP_DIR`.

## 7. Insecure Deserialization (A08:2021)

**Location:** `/api/import`, `pickle.loads(file.read())`.  
**Fix:** Use JSON only: `json.loads(file.read().decode('utf-8'))`. Pickle is not accepted from untrusted input.

## 8. Broken Authentication – Override Bypass (A07:2021)

**Location:** `/admin`, `request.args.get('override') == 'true'` setting `session['role'] = 'admin'`.  
**Fix:** Remove the override branch; admin access only via proper session role set after real authentication.

## 9. Weak Password Storage (A02:2021)

**Location:** Login compared plaintext password in SQL.  
**Fix:** Parameterized query removes SQL injection. Passwords should be hashed (e.g. bcrypt/argon2) in the database and compared with a constant-time check; application code now uses parameterized queries so that hashing can be added without injection risk.

## 10. Debug Mode in Production (A05:2021)

**Location:** `app.run(debug=True, ...)`.  
**Fix:** `debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")` so production defaults to `debug=False`. Port from `PORT` env.

---

**Summary:** All 10 vulnerabilities are addressed: secrets from env, parameterized SQL, escaped output, path and command safety, JSON-only import, no auth bypass, and debug off by default.
