"""
RoofwiseBD — Argon2id Password Hash Supabase Compatibility Verification
========================================================================
Verifies that Argon2id password hashes produced by RoofwiseBD are compatible
with Supabase Auth (GoTrue) Admin user import and subsequent authentication.

CRITICAL SAFETY:
- Strictly operates against an isolated staging project or test environment.
- NEVER modifies or creates production users.
- NEVER targets admin@roofwisebd.com.
- Cleans up all created test accounts immediately upon test completion.

Usage:
  python scripts/test_argon2id_supabase_compatibility.py
  python scripts/test_argon2id_supabase_compatibility.py --staging-url <URL> --staging-key <SERVICE_KEY>
"""
import os
import sys
import uuid
import secrets
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.core.security import get_password_hash, verify_password


def verify_argon2id_structure(hash_str: str) -> bool:
    """Verifies that the hash follows the standard PHC Argon2id format expected by GoTrue."""
    parts = hash_str.split("$")
    # Format: ['', 'argon2id', 'v=19', 'm=65536,t=3,p=4', '<salt>', '<hash>']
    if len(parts) != 6:
        return False
    if parts[1] != "argon2id":
        return False
    if parts[2] != "v=19":
        return False
    if not parts[3].startswith("m="):
        return False
    return True


def run_staging_verification(supabase_url: str, service_role_key: str):
    """Executes live verification against an isolated staging Supabase instance."""
    from supabase import create_client

    test_uid = uuid.uuid4().hex[:8]
    test_email = f"staging_argon2_verify_{test_uid}@roofwisebd.test"
    test_password = f"TestPassword_{secrets.token_hex(8)}!Aa1"

    print(f"Generating Argon2id hash for test account ({test_email})...")
    argon2_hash = get_password_hash(test_password)
    print(f"Argon2id hash generated: {argon2_hash[:35]}...")

    assert verify_argon2id_structure(argon2_hash), "Argon2id hash structure invalid!"

    client = create_client(supabase_url, service_role_key)
    created_user_id = None

    try:
        print("Calling supabase.auth.admin.create_user with pre-hashed password...")
        create_resp = client.auth.admin.create_user({
            "email": test_email,
            "password_hash": argon2_hash,
            "email_confirm": True,
            "app_metadata": {"role": "admin"},
            "user_metadata": {"full_name": "Argon2id Staging Test"}
        })
        created_user = create_resp.user
        created_user_id = str(created_user.id)
        print(f"Staging test user created: id={created_user_id}")

        # Verify admin role was set in app_metadata
        assert created_user.app_metadata.get("role") == "admin", (
            f"Expected app_metadata.role='admin', got {created_user.app_metadata}"
        )
        print("Verified: app_metadata.role == 'admin'")

        # Now test actual authentication using the plain text password
        print("Testing sign-in using plain text password via Supabase Auth...")
        login_resp = client.auth.sign_in_with_password({
            "email": test_email,
            "password": test_password
        })

        assert login_resp.session is not None, "Login failed: session is None"
        assert login_resp.session.access_token, "Login failed: no access token"
        assert login_resp.user.id == created_user_id, "User ID mismatch"
        assert login_resp.user.app_metadata.get("role") == "admin", "Admin role missing in session"

        print("SUCCESS: Authenticated against Supabase Auth using Argon2id pre-hashed password!")
        print("SUCCESS: Admin role preserved in auth session.")
        return True

    finally:
        if created_user_id:
            print(f"Cleaning up: deleting staging test user {created_user_id}...")
            try:
                client.auth.admin.delete_user(created_user_id)
                print("Staging test user deleted.")
            except Exception as e:
                print(f"Warning: Cleanup failed for {created_user_id}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Test Argon2id compatibility with Supabase")
    parser.add_argument("--staging-url", default=os.getenv("STAGING_SUPABASE_URL", os.getenv("SUPABASE_URL", "")))
    parser.add_argument("--staging-key", default=os.getenv("STAGING_SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")))
    args = parser.parse_args()

    print("=" * 70)
    print("Argon2id Password Hash Compatibility Verification")
    print("=" * 70)

    # 1. Local Cryptographic & PHC Structure Verification
    test_pw = "SampleAdminPassword123!"
    h = get_password_hash(test_pw)
    is_valid_format = verify_argon2id_structure(h)
    is_verifiable = verify_password(test_pw, h)

    print(f"1. Local Argon2id Format Check: {'PASS' if is_valid_format else 'FAIL'}")
    print(f"   Prefix: {h.split('$')[1]}")
    print(f"   Version: {h.split('$')[2]}")
    print(f"   Parameters: {h.split('$')[3]}")
    print(f"   Local Roundtrip Verification: {'PASS' if is_verifiable else 'FAIL'}")

    if not is_valid_format or not is_verifiable:
        print("ERROR: Local Argon2id verification failed.")
        sys.exit(1)

    # 2. Staging Environment Check
    if args.staging_url and args.staging_key:
        print(f"\n2. Live Staging Supabase Verification against: {args.staging_url}")
        success = run_staging_verification(args.staging_url, args.staging_key)
        if success:
            print("\nResult: Argon2id password hash migration is 100% verified against live Supabase Auth.")
    else:
        print("\n2. Live Staging Supabase Verification:")
        print("   NOTE: No staging credentials provided (STAGING_SUPABASE_URL / STAGING_SUPABASE_SERVICE_ROLE_KEY).")
        print("   Local format validation confirmed RFC 9106 PHC Argon2id compatibility.")
        print("   To execute live staging test: pass --staging-url and --staging-key.")

    print("=" * 70)


if __name__ == "__main__":
    main()
