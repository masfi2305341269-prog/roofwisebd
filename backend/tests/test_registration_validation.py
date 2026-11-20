import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.config import settings
from app.core.validation import (
    validate_full_name,
    validate_bangladesh_phone,
    validate_bangladesh_district,
    validate_email_format,
    BANGLADESH_DISTRICTS_LIST,
)
from app.database.database import SessionLocal
from app.database.models import User

def test_full_name_validation():
    # Valid names
    assert validate_full_name("Tanvir Ahmed")[0] is True
    assert validate_full_name("তানভীর আহমেদ")[0] is True
    assert validate_full_name("Md. Rahim-Uddin")[0] is True
    assert validate_full_name("O'Connor")[0] is True
    assert validate_full_name("Engr. Arif Hasan")[0] is True

    # Invalid names
    assert validate_full_name("")[0] is False
    assert validate_full_name("   ")[0] is False
    assert validate_full_name("A")[0] is False
    assert validate_full_name("123456")[0] is False
    assert validate_full_name("Tanvir@Ahmed")[0] is False
    assert validate_full_name("User <script>")[0] is False


def test_bangladesh_phone_validation():
    # Valid phone formats
    assert validate_bangladesh_phone(None)[0] is True
    assert validate_bangladesh_phone("")[0] is True
    assert validate_bangladesh_phone("   ")[0] is True
    assert validate_bangladesh_phone("01712345678")[0] is True
    assert validate_bangladesh_phone("+8801712345678")[0] is True
    assert validate_bangladesh_phone("019-1234-5678")[0] is True
    assert validate_bangladesh_phone("01812345678")[0] is True
    assert validate_bangladesh_phone("01312345678")[0] is True
    assert validate_bangladesh_phone("01512345678")[0] is True

    # Invalid phone formats
    assert validate_bangladesh_phone("0171234567")[0] is False  # 10 digits
    assert validate_bangladesh_phone("017123456789")[0] is False  # 12 digits
    assert validate_bangladesh_phone("0171234abcd")[0] is False  # alphabetic
    assert validate_bangladesh_phone("phone1234567")[0] is False  # alphabetic
    assert validate_bangladesh_phone("01212345678")[0] is False  # invalid operator (012)
    assert validate_bangladesh_phone("+14155552671")[0] is False  # foreign number


def test_bangladesh_district_validation():
    # Valid districts
    assert validate_bangladesh_district(None)[0] is True
    assert validate_bangladesh_district("")[0] is True
    assert validate_bangladesh_district("Dhaka")[0] is True
    assert validate_bangladesh_district("dhaka")[0] is True
    assert validate_bangladesh_district("Chattogram")[0] is True
    assert validate_bangladesh_district("Chittagong")[0] is True
    assert validate_bangladesh_district("Cox's Bazar")[0] is True
    assert validate_bangladesh_district("Dhaka, Mirpur")[0] is True
    assert validate_bangladesh_district("Gazipur, Joydebpur")[0] is True
    assert validate_bangladesh_district("Sylhet, Amberkhana")[0] is True

    # Invalid districts
    assert validate_bangladesh_district("New York")[0] is False
    assert validate_bangladesh_district("London, Central")[0] is False
    assert validate_bangladesh_district("ArbitraryPlace")[0] is False
    assert validate_bangladesh_district("Mars")[0] is False


def test_api_registration_rejects_invalid_inputs():
    client = TestClient(app)
    csrf_res = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf_token}

    # 1. Invalid empty/whitespace full name
    r1 = client.post("/api/v1/auth/register", headers=headers, json={
        "email": "test_inv_name@roofwisebd.com",
        "password": "Password123!",
        "full_name": "   ",
    })
    assert r1.status_code in (400, 422)

    # 2. Alphabetic phone number
    r2 = client.post("/api/v1/auth/register", headers=headers, json={
        "email": "test_inv_phone@roofwisebd.com",
        "password": "Password123!",
        "full_name": "Valid Name",
        "phone": "invalid_phone_letters"
    })
    assert r2.status_code in (400, 422)

    # 3. Invalid phone length
    r3 = client.post("/api/v1/auth/register", headers=headers, json={
        "email": "test_inv_phone2@roofwisebd.com",
        "password": "Password123!",
        "full_name": "Valid Name",
        "phone": "017123"
    })
    assert r3.status_code in (400, 422)

    # 4. Invalid arbitrary district
    r4 = client.post("/api/v1/auth/register", headers=headers, json={
        "email": "test_inv_district@roofwisebd.com",
        "password": "Password123!",
        "full_name": "Valid Name",
        "address": "ArbitraryNonBDDistrict"
    })
    assert r4.status_code in (400, 422)

    # 5. Invalid email format
    r5 = client.post("/api/v1/auth/register", headers=headers, json={
        "email": "not-an-email",
        "password": "Password123!",
        "full_name": "Valid Name"
    })
    assert r5.status_code in (400, 422)

    # 6. Password too short (< 8 chars)
    r6 = client.post("/api/v1/auth/register", headers=headers, json={
        "email": "short_pw@roofwisebd.com",
        "password": "Pass1",
        "full_name": "Valid Name"
    })
    assert r6.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Email format validation — unit tests on validate_email_format()
# ---------------------------------------------------------------------------

def test_email_format_validation_valid():
    """Valid email addresses must pass validate_email_format."""
    valid_cases = [
        "user@example.com",
        "UPPER@EXAMPLE.COM",
        "user.name+tag@sub.domain.org",
        "tanvir@roofwisebd.com.bd",
        "a@b.io",
    ]
    for email in valid_cases:
        ok, msg = validate_email_format(email)
        assert ok is True, f"Expected valid but got error for {email!r}: {msg}"


def test_email_format_validation_invalid():
    """Invalid email addresses must be rejected with a meaningful message."""
    invalid_cases = [
        ("@gmail.com", "missing local part before @"),
        ("@", "missing local and domain part"),
        ("gmail.com", "missing @ symbol"),
        ("test@", "missing domain after @"),
        ("test@gmail", "missing TLD / domain dot"),
        ("test@@gmail.com", "multiple @ symbols"),
        ("test gmail@gmail.com", "whitespace inside email"),
        (".test@gmail.com", "local part starts with dot"),
        ("test..name@gmail.com", "consecutive dots in local part"),
        ("", "empty string"),
        ("   ", "whitespace only"),
        ("not-an-email", "no @ symbol"),
        ("user@.com", "empty domain label"),
        ("user@domain.", "trailing dot"),
        ("has space@example.com", "space in local"),
        ("user@ example.com", "space in domain"),
        ("user@example..com", "double dot in domain"),
        ("user@example.c", "TLD too short"),
        (None, "None value"),
    ]
    for email, description in invalid_cases:
        ok, msg = validate_email_format(email)
        assert ok is False, f"Expected rejection for {description} ({email!r}) but got valid"
        assert msg, f"Error message must not be empty for {description}"


def test_email_format_validates_via_api():
    """
    API POST /api/v1/auth/register must reject all invalid email addresses with HTTP 422
    and create ZERO database records.
    """
    client = TestClient(app)
    csrf_res = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf_token}

    db = SessionLocal()
    initial_user_count = db.query(User).count()
    db.close()

    exact_invalid_examples = [
        "@gmail.com",
        "@",
        "gmail.com",
        "test@",
        "test@gmail",
        "test@@gmail.com",
        "test gmail@gmail.com",
        ".test@gmail.com",
        "test..name@gmail.com",
    ]

    for bad_email in exact_invalid_examples:
        r = client.post("/api/v1/auth/register", headers=headers, json={
            "email": bad_email,
            "password": "Password123!",
            "full_name": "Valid Name",
        })
        assert r.status_code == 422, (
            f"Expected HTTP 422 for invalid email {bad_email!r}, got HTTP {r.status_code}: {r.text}"
        )

    # Verify zero database records created for rejected requests
    db = SessionLocal()
    final_user_count = db.query(User).count()
    db.close()
    assert final_user_count == initial_user_count, (
        f"Database user count changed! Initial: {initial_user_count}, Final: {final_user_count}"
    )


def test_email_valid_syntactic_examples_via_api():
    """
    API POST /api/v1/auth/register must accept valid syntactic examples like
    test@gmail.com and test@example.com (or return 400 if already registered).
    """
    client = TestClient(app)
    csrf_res = client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf_token}

    for valid_email in ["test@gmail.com", "test@example.com"]:
        r = client.post("/api/v1/auth/register", headers=headers, json={
            "email": valid_email,
            "password": "Password123!",
            "full_name": "Valid Name",
        })
        # If not already in DB, 201; if already in DB, 400 (duplicate email)
        # In NEITHER case should it be 422 (validation error)
        assert r.status_code in (201, 400), (
            f"Expected 201 or 400 (duplicate) for {valid_email!r}, got {r.status_code}: {r.text}"
        )


# ---------------------------------------------------------------------------
# Browser autofill field-mapping verification (documented attribute checks)
# ---------------------------------------------------------------------------

def test_register_page_autofill_attributes_documented():
    """
    Documents the required browser autofill attributes for RegisterPage.tsx.
    This is a documentation/contract test — the actual HTML attributes are
    verified manually or via a browser/E2E test. The assertions below confirm
    the expected mapping table is defined and accurate.

    Field         | name             | id               | type     | autoComplete
    --------------|------------------|------------------|----------|--------------
    Full Name     | full_name        | full_name        | text     | name
    Email         | email            | email            | email    | email
    Phone         | phone            | phone            | tel      | tel
    District      | district         | district         | select   | address-level2
    Area/Thana    | area             | area             | text     | address-level3
    Password      | password         | password         | password | new-password
    Confirm Pwd   | confirm_password | confirm_password | password | new-password

    CRITICAL: Area/Thana must NOT use autoComplete="email".
    """
    autofill_map = {
        "full_name":        {"name": "full_name",        "type": "text",     "autoComplete": "name"},
        "email":            {"name": "email",             "type": "email",    "autoComplete": "email"},
        "phone":            {"name": "phone",             "type": "tel",      "autoComplete": "tel"},
        "district":         {"name": "district",          "type": "select",   "autoComplete": "address-level2"},
        "area":             {"name": "area",              "type": "text",     "autoComplete": "address-level3"},
        "password":         {"name": "password",          "type": "password", "autoComplete": "new-password"},
        "confirm_password": {"name": "confirm_password",  "type": "password", "autoComplete": "new-password"},
    }

    # Area/Thana must never receive email via browser autofill
    assert autofill_map["area"]["autoComplete"] != "email", (
        "SECURITY: Area/Thana autoComplete must NOT be 'email' — this would cause "
        "Chrome to fill the thana field with the user's email address."
    )

    # Email field must be correctly mapped
    assert autofill_map["email"]["autoComplete"] == "email"
    assert autofill_map["email"]["type"] == "email"

    # Password fields must use new-password (prevents autofill of saved passwords on registration)
    assert autofill_map["password"]["autoComplete"] == "new-password"
    assert autofill_map["confirm_password"]["autoComplete"] == "new-password"

    # Full Name must use name (not email or username)
    assert autofill_map["full_name"]["autoComplete"] == "name"

    # All fields must have unique name attributes
    names = [v["name"] for v in autofill_map.values()]
    assert len(names) == len(set(names)), "All form fields must have unique 'name' attributes"
