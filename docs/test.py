import hashlib, hmac
from datetime import datetime

ss = b'''GET
/v1
20160930T01:23:45Z
host:your.sorna.api.endpoint
content-type:application/json
x-sorna-version:v1.20160915
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'''

ACCESS_KEY = 'AKIAIOSFODNN7EXAMPLE'
SECRET_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'

now = datetime(year=2016, month=9, day=30, hour=1, minute=23, second=45)

def sign(key, msg):
    return hmac.new(key, msg, hashlib.sha256).digest()

def get_sign_key():
    return sign(sign(SECRET_KEY.encode('ascii'), now.strftime('%Y%m%d').encode('ascii')), b'your.sorna.api.endpoint')

signature = hmac.new(get_sign_key(), ss, hashlib.sha256).hexdigest()
print('Authorization: Sorna method=HMAC-SHA256, credential={}:{}'.format(ACCESS_KEY, signature))
