import urllib.request
import json
import http.cookiejar
import time

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get_csrf():
    res = opener.open('http://127.0.0.1:8000/api/v1/auth/csrf')
    return json.loads(res.read())['csrf_token']

def post_reg(data):
    csrf = get_csrf()
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/auth/register',
        data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json', 'X-CSRF-Token': csrf}
    )
    try:
        res = opener.open(req)
        return res.status, json.loads(res.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

print("Starting Registration Validation Live Verification...")

# 1. Whitespace name
status, body = post_reg({'email': 'v1@roofwisebd.com', 'password': 'Password123!', 'full_name': '   '})
print('1. Whitespace name rejected:', status in (400, 422), status)
assert status in (400, 422)

# 2. Numeric name
status, body = post_reg({'email': 'v2@roofwisebd.com', 'password': 'Password123!', 'full_name': '1234567'})
print('2. Numeric name rejected:', status in (400, 422), status)
assert status in (400, 422)

# 3. Alphabetic phone
status, body = post_reg({'email': 'v3@roofwisebd.com', 'password': 'Password123!', 'full_name': 'Valid Name', 'phone': 'invalid_phone'})
print('3. Alphabetic phone rejected:', status in (400, 422), status)
assert status in (400, 422)

# 4. Invalid phone length
status, body = post_reg({'email': 'v4@roofwisebd.com', 'password': 'Password123!', 'full_name': 'Valid Name', 'phone': '017123'})
print('4. Short phone rejected:', status in (400, 422), status)
assert status in (400, 422)

# 5. Invalid operator
status, body = post_reg({'email': 'v5@roofwisebd.com', 'password': 'Password123!', 'full_name': 'Valid Name', 'phone': '01212345678'})
print('5. Invalid BD operator (012) rejected:', status in (400, 422), status)
assert status in (400, 422)

# 6. Arbitrary district
status, body = post_reg({'email': 'v6@roofwisebd.com', 'password': 'Password123!', 'full_name': 'Valid Name', 'address': 'RandomNonBDCity'})
print('6. Arbitrary district rejected:', status in (400, 422), status)
assert status in (400, 422)

# 7. Short password
status, body = post_reg({'email': 'v7@roofwisebd.com', 'password': 'Pass1', 'full_name': 'Valid Name'})
print('7. Short password rejected:', status in (400, 422), status)
assert status in (400, 422)

# 8. Valid registration with English name, valid BD phone, and valid BD district
ts = int(time.time())
status, body = post_reg({
    'email': f'valid_en_{ts}@roofwisebd.com',
    'password': 'Password123!',
    'full_name': 'Md. Tanvir Ahmed',
    'phone': '01712345678',
    'address': 'Dhaka, Uttara'
})
print('8. Valid English name + BD phone + district accepted:', status == 201, body.get('email'), body.get('phone'), body.get('address'))
assert status == 201
assert body['email'] == f'valid_en_{ts}@roofwisebd.com'
assert body['phone'] == '01712345678'
assert body['address'] == 'Dhaka, Uttara'

# 9. Valid registration with Bangla Unicode name and +8801 phone
status, body = post_reg({
    'email': f'valid_bn_{ts}@roofwisebd.com',
    'password': 'Password123!',
    'full_name': 'তানভীর আহমেদ',
    'phone': '+8801812345678',
    'address': 'Chattogram, Panchlaish'
})
print('9. Valid Bangla name + international BD phone accepted:', status == 201, body.get('full_name'), body.get('phone'), body.get('address'))
assert status == 201
assert body['full_name'] == 'তানভীর আহমেদ'
assert body['phone'] == '+8801812345678'

# 10. Email normalization check (Upper case input -> Lower case stored)
status, body = post_reg({
    'email': f'UPPERCASE_{ts}@ROOFWISEBD.COM',
    'password': 'Password123!',
    'full_name': "O'Connor",
    'address': 'Sylhet'
})
print('10. Email normalization check:', status == 201, body.get('email'))
assert status == 201
assert body['email'] == f'uppercase_{ts}@roofwisebd.com'

print('\nALL 10 LIVE REGISTRATION VALIDATION CHECKS PASSED PERFECTLY!')
