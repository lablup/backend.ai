from datetime import datetime

from dateutil.tz import tzutc

from ai.backend.client.auth import generate_signature


def test_generate_signature(defconfig):
    kwargs = dict(
        method="GET",
        version=defconfig.version,
        endpoint=defconfig.endpoint,
        date=datetime.now(tzutc()),
        rel_url="/path/to/api/",
        content_type="plain/text",
        access_key=defconfig.access_key,
        secret_key=defconfig.secret_key,
        hash_type="md5",
    )
    headers, signature = generate_signature(**kwargs)

    assert kwargs["hash_type"].upper() in headers["Authorization"]
    assert kwargs["access_key"] in headers["Authorization"]
    assert signature in headers["Authorization"]
