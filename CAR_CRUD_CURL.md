# Car (Vehicle) CRUD with curl

This document shows how to perform Create / Read / Update / Delete (CRUD) operations for `Car` (vehicle) records using curl against the project's REST API endpoints.

Prerequisites
- The Django development server must be running (default): `python manage.py runserver`
- You must have a Django user with `is_staff=True` (admin/staff). Create one with:

```powershell
python manage.py createsuperuser
```

- The examples below assume the site is served at `http://127.0.0.1:8000`.
- The REST API endpoints used:
  - `GET /api/cars/` — list all cars
  - `POST /api/cars/` — create a new car (staff only)
  - `GET /api/cars/<id>/` — retrieve a car
  - `PUT /api/cars/<id>/` — update a car (staff only)
  - `DELETE /api/cars/<id>/` — delete a car (staff only)

Notes about authentication & CSRF
- The project uses Django session authentication. To call the API with curl you must:
  1. Obtain the session cookie and CSRF token by GETting the login page.
  2. POST credentials to the login view with the CSRF token and cookie jar.
  3. Reuse the cookie jar and CSRF token for subsequent API calls.

POSIX / Linux / macOS (bash) example

1) Get login page and save cookies

```bash
BASE="http://127.0.0.1:8000"
COOKIEJAR=cookies.txt

# Get login page to receive CSRF cookie
curl -c $COOKIEJAR -s "$BASE/login/" -o /dev/null

# Extract csrftoken value from cookie jar (curl cookie format)
CSRF=$(grep csrftoken $COOKIEJAR | awk '{print $7}')
echo "csrf: $CSRF"
```

2) Login (POST username & password)

```bash
curl -b $COOKIEJAR -c $COOKIEJAR -s -L \
  -H "X-CSRFToken: $CSRF" \
  -d "username=admin&password=yourpassword" \
  "$BASE/login/"

# After this the sessionid cookie will be in $COOKIEJAR and you are authenticated.
```

3) List cars (GET)

```bash
curl -b $COOKIEJAR "$BASE/api/cars/"
```

4) Create a new car (POST multipart/form-data)

```bash
curl -b $COOKIEJAR -c $COOKIEJAR -L \
  -H "X-CSRFToken: $CSRF" \
  -F "category=Ambassador" \
  -F "ac_type=AC" \
  -F "total_cars=1" \
  -F "registration_number=DL01AB1234" \
  -F "price=2000.00" \
  -F "price_per_hour=250" \
  -F "price_per_km=15" \
  -F "fuel_consumption=petrol" \
  -F "status=available" \
  -F "image=@/path/to/image.jpg" \
  "$BASE/api/cars/"
```

5) Retrieve a car (GET)

```bash
curl -b $COOKIEJAR "$BASE/api/cars/1/"
```

6) Update a car (PUT with JSON)

Note: DRF’s view expects JSON for PUT when not multipart. You may use `-X PUT -H 'Content-Type: application/json' -d '{...}'`.

```bash
curl -b $COOKIEJAR -X PUT \
  -H "X-CSRFToken: $CSRF" \
  -H "Content-Type: application/json" \
  -d '{"price":"2100.00", "total_cars": 2}' \
  "$BASE/api/cars/1/"
```

7) Delete a car (DELETE)

```bash
curl -b $COOKIEJAR -X DELETE -H "X-CSRFToken: $CSRF" "$BASE/api/cars/1/"
```

Windows PowerShell notes
- PowerShell does not ship with the same shell utilities; using `curl` (aliased to `Invoke-WebRequest`/`iwr`) may differ. You can use PowerShell's `Invoke-WebRequest` and `Invoke-RestMethod` instead. Example to obtain cookies and CSRF:

```powershell
# Example outline (not full):
$resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/login/" -SessionVariable S
$csrf = ($resp.Cookies.GetCookies("http://127.0.0.1:8000") | Where-Object { $_.Name -eq 'csrftoken' }).Value
# Login with Invoke-RestMethod using -WebSession $S and header @{ 'X-CSRFToken' = $csrf }
```

Troubleshooting & tips
- If you get HTTP 403 on POST/PUT/DELETE: you likely missed the CSRF header or are not authenticated or not staff.
- Ensure your test user has `is_staff=True`.
- If images fail to upload, provide a valid path and ensure `MEDIA_ROOT` is correctly configured and writable.
- You can also use the Django admin UI (`/admin/`) for easier manual CRUD.

If you want, I can:
- Add a short PowerShell `ps1` script with equivalent steps, or
- Run a quick example (create one car) using the repo's test environment (I can demonstrate the curl calls locally if you want me to run them here).
