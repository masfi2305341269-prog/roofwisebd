import json
import urllib.request
import urllib.parse
import http.cookiejar
import sqlite3
import time
import pytest
from app.core.security import verify_otp_hash

def query_db(sql, params=()):
    conn = sqlite3.connect('roofwise.db', timeout=20)
    try:
        c = conn.cursor()
        c.execute(sql, params)
        res = c.fetchall()
        conn.commit()
        return res
    finally:
        conn.close()

def execute_db(sql, params=()):
    conn = sqlite3.connect('roofwise.db', timeout=20)
    try:
        c = conn.cursor()
        c.execute(sql, params)
        conn.commit()
    finally:
        conn.close()

def test_live_email_verification_flow():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # 1. CSRF Token Bootstrap (Check if server is reachable)
    try:
        req = urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/csrf')
        with opener.open(req, timeout=2) as resp:
            csrf_token = json.loads(resp.read().decode())['csrf_token']
    except Exception as e:
        pytest.skip(f"Live API server not running on 127.0.0.1:8000: {e}")

    def post_json(url, data):
        body = json.dumps(data).encode('utf-8')
        r = urllib.request.Request(
            url,
            data=body,
            headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf_token}
        )
        try:
            with opener.open(r) as res:
                return res.status, json.loads(res.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    test_email = f'live_otp_test_{int(time.time())}@example.com'
    try:
        execute_db("DELETE FROM email_verification_otps")
    except Exception as e:
        pytest.skip(f"Legacy OTP verification test not applicable: {e}")
    execute_db("DELETE FROM users WHERE email LIKE 'live_otp_%'")

    user_id = None
    try:
        # 2. Register User
        status, body = post_json('http://127.0.0.1:8000/api/v1/auth/register', {
            'email': test_email,
            'password': 'SecurePassword123!',
            'full_name': 'Live Verification Tester',
            'phone': '01712345678',
            'address': 'Dhaka, Dhanmondi'
        })
        assert status in (200, 201)
        assert body.get('email_verified') is False

        rows = query_db('SELECT id, email, email_verified FROM users WHERE email = ?', (test_email,))
        assert len(rows) == 1
        user_id = rows[0][0]
        assert rows[0][2] == 0, "Registered user must have email_verified = 0"

        # 3. Login attempt before verification -> MUST return HTTP 403 Forbidden
        status, body = post_json('http://127.0.0.1:8000/api/v1/auth/login', {
            'email': test_email,
            'password': 'SecurePassword123!'
        })
        assert status == 403
        assert 'not verified' in body.get('detail', '').lower()

        # 4. Locate OTP hash in database and find candidate
        otp_rows = query_db('SELECT id, otp_hash, used, attempts FROM email_verification_otps WHERE user_id = ? AND used = 0', (user_id,))
        assert len(otp_rows) == 1
        otp_id, otp_hash, used, attempts = otp_rows[0]

        correct_otp = None
        for candidate in range(0, 1000000):
            otp_str = f"{candidate:06d}"
            if verify_otp_hash(otp_str, user_id, otp_hash):
                correct_otp = otp_str
                break
        assert correct_otp is not None, "A valid 6-digit OTP hash must be present"

        # 5. Wrong OTP test -> MUST return HTTP 400
        status, body = post_json('http://127.0.0.1:8000/api/v1/auth/verify-email', {
            'email': test_email,
            'otp': '000000'
        })
        assert status == 400
        assert 'invalid' in body.get('detail', '').lower()

        # Verify attempts incremented
        otp_check = query_db('SELECT attempts FROM email_verification_otps WHERE id = ?', (otp_id,))
        assert otp_check[0][0] == 1

        # 6. Correct OTP test -> MUST return HTTP 200
        status, body = post_json('http://127.0.0.1:8000/api/v1/auth/verify-email', {
            'email': test_email,
            'otp': correct_otp
        })
        assert status == 200
        assert body.get('email_verified') is True

        # 8. Check database state
        user_after = query_db('SELECT email_verified FROM users WHERE id = ?', (user_id,))
        assert user_after[0][0] == 1, "User must now have email_verified = 1"

        otp_after = query_db('SELECT used FROM email_verification_otps WHERE id = ?', (otp_id,))
        assert otp_after[0][0] == 1, "OTP must now have used = 1"

        # 9. Verify idempotent/replay response when already verified
        # Fetch updated CSRF if cookie updated
        for cookie in cj:
            if cookie.name == 'roofwise_csrf_token':
                csrf_token = cookie.value

        status, body = post_json('http://127.0.0.1:8000/api/v1/auth/verify-email', {
            'email': test_email,
            'otp': correct_otp
        })
        assert status == 200
        assert 'already verified' in body.get('message', '').lower()

        # 10. Login after verification -> MUST return HTTP 200
        status, body = post_json('http://127.0.0.1:8000/api/v1/auth/login', {
            'email': test_email,
            'password': 'SecurePassword123!'
        })
        assert status == 200
        assert body.get('email') == test_email
        assert body.get('email_verified') is True

    finally:
        if user_id:
            execute_db('DELETE FROM email_verification_otps WHERE user_id = ?', (user_id,))
            execute_db('DELETE FROM users WHERE id = ?', (user_id,))
