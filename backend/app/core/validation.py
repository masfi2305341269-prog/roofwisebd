import re
from typing import Tuple, Optional, Set, List

# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------

_LOCAL_PART_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+$")
_DOMAIN_LABEL_REGEX = re.compile(r"^[a-zA-Z0-9\-]+$")
_TLD_REGEX = re.compile(r"^[a-zA-Z]{2,}$")


def validate_email_format(email: Optional[str]) -> Tuple[bool, str]:
    """
    Explicit, strict email format validation for RoofwiseBD authentication.
    Validates according to standard RFC 5322 rules without external DNS dependencies:
    Rejects:
      - None, empty, or whitespace-only inputs
      - Total length > 254 characters or local part > 64 characters
      - Any whitespace inside the address
      - Missing '@' symbol or multiple '@' symbols
      - Empty local part (e.g. '@gmail.com', '@')
      - Local part starting with a dot (e.g. '.test@gmail.com')
      - Local part ending with a dot (e.g. 'test.@gmail.com')
      - Local part containing consecutive dots (e.g. 'test..name@gmail.com')
      - Local part containing invalid characters
      - Empty domain part (e.g. 'test@', '@')
      - Domain missing a dot/TLD (e.g. 'test@gmail')
      - Domain starting or ending with a dot or hyphen
      - Domain containing consecutive dots
      - Domain labels starting or ending with a hyphen
      - Domain labels with invalid characters
      - TLD shorter than 2 characters (e.g. 'test@gmail.c') or containing non-letters
    Returns (True, "") on success, (False, error_message) on failure.
    """
    if not email or not isinstance(email, str):
        return False, "Email address is required."

    raw = email.strip()
    if not raw:
        return False, "Email address is required."

    # Whitespace inside the address
    if re.search(r"\s", raw):
        return False, "Email address cannot contain whitespace."

    # Max length checks per RFC 5321
    if len(raw) > 254:
        return False, "Email address cannot exceed 254 characters."

    # Exactly one @
    at_count = raw.count("@")
    if at_count == 0:
        return False, "Email address must contain an @ symbol."
    if at_count > 1:
        return False, "Email address must contain exactly one @ symbol."

    local, domain = raw.split("@", 1)

    # Local part checks
    if not local:
        return False, "Email address is missing the local part before @ (e.g. '@gmail.com' is invalid)."
    if len(local) > 64:
        return False, "Email local part cannot exceed 64 characters."
    if local.startswith("."):
        return False, "Email local part cannot start with a period."
    if local.endswith("."):
        return False, "Email local part cannot end with a period."
    if ".." in local:
        return False, "Email local part cannot contain consecutive periods."
    if not _LOCAL_PART_REGEX.match(local):
        return False, "Email local part contains invalid characters."

    # Domain part checks
    if not domain:
        return False, "Email address is missing the domain after @."
    if domain.startswith(".") or domain.startswith("-"):
        return False, "Email domain cannot start with a period or hyphen."
    if domain.endswith(".") or domain.endswith("-"):
        return False, "Email domain cannot end with a period or hyphen."
    if ".." in domain:
        return False, "Email domain cannot contain consecutive periods."
    if "." not in domain:
        return False, "Email domain must contain a valid top-level domain (e.g. '.com')."

    domain_parts = domain.split(".")
    if any(len(p) == 0 for p in domain_parts):
        return False, "Email domain contains an empty label (e.g. double dot or trailing dot)."

    for label in domain_parts[:-1]:
        if len(label) > 63:
            return False, "Email domain label cannot exceed 63 characters."
        if label.startswith("-") or label.endswith("-"):
            return False, "Email domain labels cannot start or end with a hyphen."
        if not _DOMAIN_LABEL_REGEX.match(label):
            return False, f"Email domain label '{label}' contains invalid characters."

    # TLD checks
    tld = domain_parts[-1]
    if len(tld) < 2:
        return False, "Email top-level domain must be at least 2 characters (e.g. .com, .org)."
    if not _TLD_REGEX.match(tld):
        return False, "Email top-level domain must contain only letters."

    return True, ""

# Full official list of all 64 districts of Bangladesh
BANGLADESH_DISTRICTS_LIST: List[str] = [
    # Dhaka Division (13)
    "Dhaka", "Gazipur", "Narayanganj", "Tangail", "Faridpur", 
    "Narsingdi", "Manikganj", "Munshiganj", "Gopalganj", "Kishoreganj", 
    "Madaripur", "Rajbari", "Shariatpur",
    # Chattogram Division (11)
    "Chattogram", "Cox's Bazar", "Cumilla", "Feni", "Noakhali", 
    "Brahmanbaria", "Chandpur", "Rangamati", "Bandarban", "Khagrachhari", 
    "Lakshmipur",
    # Rajshahi Division (8)
    "Rajshahi", "Bogura", "Pabna", "Sirajganj", "Naogaon", 
    "Natore", "Chapai Nawabganj", "Joypurhat",
    # Khulna Division (10)
    "Khulna", "Jashore", "Kushtia", "Satkhira", "Jhenaidah", 
    "Bagerhat", "Chuadanga", "Magura", "Meherpur", "Narail",
    # Barishal Division (6)
    "Barishal", "Patuakhali", "Bhola", "Pirojpur", "Jhalokati", "Barguna",
    # Sylhet Division (4)
    "Sylhet", "Moulvibazar", "Habiganj", "Sunamganj",
    # Rangpur Division (8)
    "Rangpur", "Dinajpur", "Kurigram", "Gaibandha", "Nilphamari", 
    "Lalmonirhat", "Thakurgaon", "Panchagarh",
    # Mymensingh Division (4)
    "Mymensingh", "Jamalpur", "Netrokona", "Sherpur",
]

# Set of canonical lowercase district names and common aliases/transliterations
BANGLADESH_DISTRICTS_CANONICAL: Set[str] = {
    d.lower() for d in BANGLADESH_DISTRICTS_LIST
}

# Common transliterations & aliases
DISTRICT_ALIASES = {
    "chittagong": "Chattogram",
    "comilla": "Cumilla",
    "bogra": "Bogura",
    "jessore": "Jashore",
    "barisal": "Barishal",
    "coxs bazar": "Cox's Bazar",
    "cox's bazar": "Cox's Bazar",
    "coxsbazar": "Cox's Bazar",
    "chapai": "Chapai Nawabganj",
    "nawabganj": "Chapai Nawabganj",
    "chapainawabganj": "Chapai Nawabganj",
    "jhalakati": "Jhalokati",
    "maulvibazar": "Moulvibazar",
    "moulvi bazar": "Moulvibazar",
}

for alias in DISTRICT_ALIASES:
    BANGLADESH_DISTRICTS_CANONICAL.add(alias.lower())


# Name validation regex: English letters, Bangla Unicode (\u0980-\u09FF), spaces, hyphens, apostrophes, and period
NAME_REGEX = re.compile(r"^[a-zA-Z\u0980-\u09FF\s\-\'\.]+$")
LETTER_CHECK_REGEX = re.compile(r"[a-zA-Z\u0980-\u09FF]")

# Phone validation regex: Bangladesh format 01XXXXXXXXX or +8801XXXXXXXXX
# Valid operators: 013, 014, 015, 016, 017, 018, 019
PHONE_REGEX = re.compile(r"^(\+8801|01)[3-9]\d{8}$")


def validate_full_name(name: Optional[str]) -> Tuple[bool, str]:
    """
    Validates full name:
    - Required, non-empty, not purely whitespace.
    - Min length 2, max length 100.
    - Allows English and Bangla names, spaces, hyphens, and apostrophes.
    - Must contain at least one valid letter.
    """
    if not name or not isinstance(name, str):
        return False, "Full name is required."
    
    cleaned = name.strip()
    if len(cleaned) < 2:
        return False, "Full name must be at least 2 characters long."
    if len(cleaned) > 100:
        return False, "Full name cannot exceed 100 characters."
    
    if not LETTER_CHECK_REGEX.search(cleaned):
        return False, "Full name must contain at least one letter."
        
    if not NAME_REGEX.match(cleaned):
        return False, "Full name may only contain English letters, Bangla characters, spaces, hyphens, and apostrophes."
        
    return True, ""


def validate_bangladesh_phone(phone: Optional[str]) -> Tuple[bool, Optional[str], str]:
    """
    Validates optional Bangladesh mobile number:
    - If None or empty, returns (True, None, "")
    - Rejects alphabetic characters and invalid lengths
    - Accepts 01XXXXXXXXX or +8801XXXXXXXXX (operators 013-019)
    - Returns normalized stripped phone on success
    """
    if phone is None:
        return True, None, ""
        
    cleaned = phone.strip()
    if not cleaned:
        return True, None, ""
        
    # Check for disallowed alphabetic characters
    if re.search(r"[a-zA-Z]", cleaned):
        return False, None, "Phone number cannot contain alphabetic characters."
        
    # Normalize by removing interior whitespace or hyphens
    normalized = re.sub(r"[\s\-]", "", cleaned)
    
    # Handle optional leading '8801...' without '+' by adding '+'
    if normalized.startswith("8801") and len(normalized) == 13:
        normalized = "+" + normalized

    if not PHONE_REGEX.match(normalized):
        return False, None, "Invalid Bangladesh phone format. Use 01XXXXXXXXX or +8801XXXXXXXXX."
        
    return True, normalized, ""


def validate_bangladesh_district(address: Optional[str]) -> Tuple[bool, Optional[str], str]:
    """
    Validates optional district/address against Bangladesh district list:
    - If None or empty, returns (True, None, "")
    - Checks whether the district matches one of Bangladesh's 64 districts
    - Allows 'District' or 'District, Area' format
    - Returns sanitized district/address on success
    """
    if address is None:
        return True, None, ""
        
    cleaned = address.strip()
    if not cleaned:
        return True, None, ""
        
    # If format is "District, Area", check the leading District part
    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    district_candidate = parts[0].lower() if parts else cleaned.lower()
    
    if district_candidate not in BANGLADESH_DISTRICTS_CANONICAL:
        return False, None, (
            f"'{parts[0]}' is not a recognized Bangladesh district. "
            "Please select a valid district from Bangladesh."
        )
        
    return True, cleaned, ""
