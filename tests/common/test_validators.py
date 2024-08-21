import enum
import os
import pwd
from datetime import datetime, timedelta
from ipaddress import IPv4Address, ip_address
from uuid import UUID

import multidict
import pytest
import trafaret as t
import yarl
from dateutil.relativedelta import relativedelta

from ai.backend.common import validators as tx
from ai.backend.common.types import HostPortPair, VFolderID


def test_aliased_key() -> None:
    iv = t.Dict({
        t.Key("x") >> "z": t.Int,
        tx.AliasedKey(["y", "Y"]): t.Int,
    })
    assert iv.check({"x": 1, "y": 2}) == {"z": 1, "y": 2}

    with pytest.raises(t.DataError) as e:
        iv.check({"x": 1})
    err_data = e.value.as_dict()
    assert "y" in err_data
    assert "is required" in err_data["y"]

    with pytest.raises(t.DataError) as e:
        iv.check({"y": 2})
    err_data = e.value.as_dict()
    assert "x" in err_data
    assert "is required" in err_data["x"]

    with pytest.raises(t.DataError) as e:
        iv.check({"x": 1, "y": "string"})
    err_data = e.value.as_dict()
    assert "y" in err_data
    assert "can't be converted to int" in err_data["y"]

    with pytest.raises(t.DataError) as e:
        iv.check({"x": 1, "Y": "string"})
    err_data = e.value.as_dict()
    assert "Y" in err_data
    assert "can't be converted to int" in err_data["Y"]

    iv = t.Dict({
        t.Key("x", default=0): t.Int,
        tx.AliasedKey(["y", "Y"], default=1): t.Int,
    })
    assert iv.check({"x": 5, "Y": 6}) == {"x": 5, "y": 6}
    assert iv.check({"x": 5, "y": 6}) == {"x": 5, "y": 6}
    assert iv.check({"y": 3}) == {"x": 0, "y": 3}
    assert iv.check({"Y": 3}) == {"x": 0, "y": 3}
    assert iv.check({"x": 3}) == {"x": 3, "y": 1}
    assert iv.check({}) == {"x": 0, "y": 1}

    with pytest.raises(t.DataError) as e:
        iv.check({"z": 99})
    err_data = e.value.as_dict()
    assert "z" in err_data
    assert "not allowed key" in err_data["z"]


def test_multikey() -> None:
    iv = t.Dict({
        tx.MultiKey("x"): t.List(t.Int),
        t.Key("y"): t.Int,
    })

    data: multidict.MultiDict = multidict.MultiDict()
    data.add("x", 1)
    data.add("x", 2)
    data.add("y", 3)
    result = iv.check(data)
    assert result["x"] == [1, 2]
    assert result["y"] == 3

    data = multidict.MultiDict()
    data.add("x", 1)
    data.add("y", 3)
    result = iv.check(data)
    assert result["x"] == [1]
    assert result["y"] == 3

    plain_data = {
        "x": [10, 20],
        "y": 30,
    }
    result = iv.check(plain_data)
    assert result["x"] == [10, 20]
    assert result["y"] == 30

    plain_data_nolist = {
        "x": 10,
        "y": 30,
    }
    result = iv.check(plain_data_nolist)
    assert result["x"] == [10]
    assert result["y"] == 30


def test_multikey_string() -> None:
    iv = t.Dict({
        tx.MultiKey("x"): t.List(t.String),
        t.Key("y"): t.String,
    })

    plain_data = {
        "x": ["abc"],
        "y": "def",
    }
    result = iv.check(plain_data)
    assert result["x"] == ["abc"]
    assert result["y"] == "def"

    plain_data_nolist = {
        "x": "abc",
        "y": "def",
    }
    result = iv.check(plain_data_nolist)
    assert result["x"] == ["abc"]
    assert result["y"] == "def"


def test_binary_size() -> None:
    iv = tx.BinarySize()
    assert iv.check("10M") == 10 * (2**20)
    assert iv.check("1K") == 1024
    assert iv.check(1058476) == 1058476

    with pytest.raises(t.DataError):
        iv.check("XX")


def test_binary_size_commutative_with_null() -> None:
    iv1 = t.Null | tx.BinarySize()
    iv2 = tx.BinarySize() | t.Null

    iv1.check(None)
    iv2.check(None)

    with pytest.raises(t.DataError):
        iv1.check("xxxxx")
    with pytest.raises(t.DataError):
        iv2.check("xxxxx")


def test_delimiter_list() -> None:
    iv = tx.DelimiterSeperatedList[str](t.String(allow_blank=True), delimiter=":")
    assert iv.check("") == [""]
    assert iv.check(":") == ["", ""]
    iv = tx.DelimiterSeperatedList(
        t.String(allow_blank=True),
        delimiter=":",
        empty_str_as_empty_list=True,
    )
    assert iv.check("") == []
    assert iv.check(":") == ["", ""]
    iv = tx.DelimiterSeperatedList[str](t.String, delimiter=":")
    with pytest.raises(t.DataError):
        iv.check("")
    with pytest.raises(t.DataError):
        iv.check(":")
    assert iv.check("aaa:bbb:ccc") == ["aaa", "bbb", "ccc"]
    assert iv.check("xxx") == ["xxx"]
    iv2 = tx.DelimiterSeperatedList[HostPortPair](tx.HostPortPair, delimiter=",")
    assert iv2.check("127.0.0.1:6379,127.0.0.1:6380") == [
        (ip_address("127.0.0.1"), 6379),
        (ip_address("127.0.0.1"), 6380),
    ]


def test_string_list() -> None:
    iv = tx.StringList(delimiter=":", allow_blank=True)
    assert iv.check("aaa:bbb:ccc") == ["aaa", "bbb", "ccc"]
    assert iv.check(":bbb") == ["", "bbb"]
    assert iv.check("aaa:") == ["aaa", ""]
    assert iv.check("xxx") == ["xxx"]
    assert iv.check("") == [""]
    assert iv.check(123) == ["123"]
    iv = tx.StringList(delimiter=":", allow_blank=False)
    with pytest.raises(t.DataError):
        iv.check("")
    with pytest.raises(t.DataError):
        iv.check(":bbb")
    iv = tx.StringList(delimiter=":", allow_blank=True, min_length=2)
    with pytest.raises(t.DataError):
        iv.check("")
    with pytest.raises(t.DataError):
        iv.check("a")
    assert iv.check("a:b") == ["a", "b"]


def test_enum() -> None:
    class MyTypes(enum.Enum):
        TYPE1 = 1
        TYPE2 = 2

    iv = tx.Enum(MyTypes)
    assert iv.check(1) == MyTypes.TYPE1
    assert iv.check(2) == MyTypes.TYPE2
    with pytest.raises(t.DataError):
        iv.check(3)
    with pytest.raises(t.DataError):
        iv.check("STRING")

    iv = tx.Enum(MyTypes, use_name=True)
    assert iv.check("TYPE1") == MyTypes.TYPE1
    assert iv.check("TYPE2") == MyTypes.TYPE2
    with pytest.raises(t.DataError):
        iv.check("TYPE3")
    with pytest.raises(t.DataError):
        iv.check(0)


def test_path() -> None:
    # TODO: write tests
    pass


def test_host_port_pair() -> None:
    iv = tx.HostPortPair()

    p = iv.check(("127.0.0.1", 80))
    assert isinstance(p, tx._HostPortPair)
    assert p.host == IPv4Address("127.0.0.1")
    assert p.port == 80

    p = iv.check("127.0.0.1:80")
    assert isinstance(p, tx._HostPortPair)
    assert p.host == IPv4Address("127.0.0.1")
    assert p.port == 80

    p = iv.check({"host": "127.0.0.1", "port": 80})
    assert isinstance(p, tx._HostPortPair)
    assert p.host == IPv4Address("127.0.0.1")
    assert p.port == 80

    p = iv.check({"host": "127.0.0.1", "port": "80"})
    assert isinstance(p, tx._HostPortPair)
    assert p.host == IPv4Address("127.0.0.1")
    assert p.port == 80

    p = iv.check(("mydomain.com", 443))
    assert isinstance(p, tx._HostPortPair)
    assert p.host == "mydomain.com"
    assert p.port == 443

    p = iv.check("mydomain.com:443")
    assert isinstance(p, tx._HostPortPair)
    assert p.host == "mydomain.com"
    assert p.port == 443

    p = iv.check({"host": "mydomain.com", "port": 443})
    assert isinstance(p, tx._HostPortPair)
    assert p.host == "mydomain.com"
    assert p.port == 443

    p = iv.check({"host": "mydomain.com", "port": "443"})
    assert isinstance(p, tx._HostPortPair)
    assert p.host == "mydomain.com"
    assert p.port == 443

    with pytest.raises(t.DataError):
        p = iv.check(("127.0.0.1", -1))
    with pytest.raises(t.DataError):
        p = iv.check(("127.0.0.1", 0))
    with pytest.raises(t.DataError):
        p = iv.check(("127.0.0.1", 65536))
    with pytest.raises(t.DataError):
        p = iv.check("127.0.0.1:65536")
    with pytest.raises(t.DataError):
        p = iv.check(("", 80))
    with pytest.raises(t.DataError):
        p = iv.check(":80")
    with pytest.raises(t.DataError):
        p = iv.check({})
    with pytest.raises(t.DataError):
        p = iv.check({"host": "x"})
    with pytest.raises(t.DataError):
        p = iv.check({"port": 80})
    with pytest.raises(t.DataError):
        p = iv.check({"host": "", "port": 80})


def test_port_range() -> None:
    iv = tx.PortRange()

    r = iv.check("1000-2000")
    assert isinstance(r, tuple)
    assert len(r) == 2
    assert r[0] == 1000
    assert r[1] == 2000

    r = iv.check([1000, 2000])
    assert isinstance(r, tuple)
    assert len(r) == 2
    assert r[0] == 1000
    assert r[1] == 2000

    r = iv.check((1000, 2000))
    assert isinstance(r, tuple)
    assert len(r) == 2
    assert r[0] == 1000
    assert r[1] == 2000

    with pytest.raises(t.DataError):
        r = iv.check([0, 1000])
    with pytest.raises(t.DataError):
        r = iv.check([1000, 65536])
    with pytest.raises(t.DataError):
        r = iv.check([2000, 1000])
    with pytest.raises(t.DataError):
        r = iv.check("x-y")


def test_user_id() -> None:
    iv = tx.UserID()
    assert iv.check(123) == 123
    assert iv.check("123") == 123
    assert iv.check(os.getuid()) == os.getuid()
    assert iv.check(None) == os.getuid()
    assert iv.check("") == os.getuid()

    iv = tx.UserID(default_uid=1)
    assert iv.check(os.getuid()) == os.getuid()
    assert iv.check(None) == 1
    assert iv.check(1) == 1
    assert iv.check(123) == 123
    assert iv.check("123") == 123
    assert iv.check("") == 1
    assert iv.check(pwd.getpwuid(os.getuid())[0]) == os.getuid()
    assert iv.check(-1) == os.getuid()
    assert iv.check("-1") == os.getuid()

    with pytest.raises(t.DataError):
        iv.check("nonExistentUserName")
    with pytest.raises(t.DataError):
        iv.check([1, 2])
    with pytest.raises(t.DataError):
        iv.check((1, 2))


def test_slug_ascii() -> None:
    iv = tx.Slug()
    assert iv.check("a") == "a"
    assert iv.check("0Z") == "0Z"
    assert iv.check("abc") == "abc"
    assert iv.check("a-b") == "a-b"
    assert iv.check("a_b") == "a_b"
    with pytest.raises(t.DataError):
        iv.check("-b")
    with pytest.raises(t.DataError):
        iv.check("a_")
    with pytest.raises(t.DataError):
        iv.check("_")
    with pytest.raises(t.DataError):
        iv.check("")
    with pytest.raises(t.DataError):
        iv.check("a__b")
    with pytest.raises(t.DataError):
        iv.check("a--b")


def test_slug_length() -> None:
    iv = tx.Slug[2:4]  # type: ignore
    assert iv._min_length == 2
    assert iv._max_length == 4

    iv = tx.Slug(max_length=4)
    assert iv._min_length is None
    assert iv._max_length == 4
    assert iv.check("abc") == "abc"
    assert iv.check("abcd") == "abcd"
    with pytest.raises(t.DataError):
        iv.check("abcde")

    iv = tx.Slug(min_length=4)
    assert iv._min_length == 4
    assert iv._max_length is None
    with pytest.raises(t.DataError):
        iv.check("abc")
    assert iv.check("abcd") == "abcd"
    assert iv.check("abcde") == "abcde"

    iv = tx.Slug(min_length=2, max_length=4)
    with pytest.raises(t.DataError):
        iv.check("a")
    assert iv.check("ab") == "ab"
    assert iv.check("abcd") == "abcd"
    with pytest.raises(t.DataError):
        iv.check("abcde")

    iv = tx.Slug(min_length=2, max_length=2)
    with pytest.raises(t.DataError):
        iv.check("a")
    assert iv.check("ab") == "ab"
    with pytest.raises(t.DataError):
        iv.check("abc")

    with pytest.raises(TypeError):
        tx.Slug(min_length=2, max_length=1)
    with pytest.raises(TypeError):
        tx.Slug(max_length=-1)
    with pytest.raises(TypeError):
        tx.Slug(min_length=-1)


def test_slug_unicode() -> None:
    iv = tx.Slug(allow_unicode=False)
    with pytest.raises(t.DataError):
        iv.check("한글")
    with pytest.raises(t.DataError):
        iv.check("가-힣")
    with pytest.raises(t.DataError):
        iv.check("한_글")
    with pytest.raises(t.DataError):
        iv.check("_한글")
    with pytest.raises(t.DataError):
        iv.check("한글-")

    iv = tx.Slug(allow_unicode=True)
    assert iv.check("한글") == "한글"
    assert iv.check("가-힣") == "가-힣"
    assert iv.check("한_글") == "한_글"
    with pytest.raises(t.DataError):
        iv.check("_한글")
    with pytest.raises(t.DataError):
        iv.check("한글-")


def test_slug_spaces() -> None:
    iv = tx.Slug(allow_space=False)
    with pytest.raises(t.DataError):
        iv.check("")
    with pytest.raises(t.DataError):
        iv.check(" ")
    with pytest.raises(t.DataError):
        iv.check("\t")
    with pytest.raises(t.DataError):
        iv.check("a b")
    with pytest.raises(t.DataError):
        iv.check("a\tb")

    iv = tx.Slug(allow_space=True)
    with pytest.raises(t.DataError):
        iv.check("")
    with pytest.raises(t.DataError):
        iv.check(" ")
    with pytest.raises(t.DataError):
        iv.check("\t")
    assert iv.check("a b") == "a b"
    assert iv.check("a\tb") == "a\tb"
    with pytest.raises(t.DataError):
        # consecutive non-word chars are not allowed always.
        iv.check("ab  cd")


def test_slug_dot() -> None:
    iv = tx.Slug(allow_dot=False)
    with pytest.raises(t.DataError):
        iv.check(".")
    with pytest.raises(t.DataError):
        iv.check("...")
    with pytest.raises(t.DataError):
        iv.check("ab..cd")
    with pytest.raises(t.DataError):
        iv.check(".abc")
    with pytest.raises(t.DataError):
        iv.check("abc.")
    with pytest.raises(t.DataError):
        iv.check("ab.c")

    iv = tx.Slug(allow_dot=True)
    with pytest.raises(t.DataError):
        iv.check(".")
    with pytest.raises(t.DataError):
        iv.check("...")
    with pytest.raises(t.DataError):
        iv.check(".abc")
    with pytest.raises(t.DataError):
        iv.check("abc.")
    assert iv.check("ab.c") == "ab.c"
    with pytest.raises(t.DataError):
        # consecutive non-word chars are not allowed always.
        iv.check("ab..cd")


def test_json_string() -> None:
    iv = tx.JSONString()
    assert iv.check("{}") == {}
    assert iv.check('{"a":123}') == {"a": 123}
    assert iv.check("[]") == []
    with pytest.raises(ValueError):
        iv.check("x")


def test_time_duration() -> None:
    iv = tx.TimeDuration()
    date = datetime(2020, 2, 29)
    with pytest.raises(t.DataError):
        iv.check("")
    assert iv.check(0) == timedelta(seconds=0)
    assert iv.check(10) == timedelta(seconds=10)
    assert iv.check(86400.55) == timedelta(days=1, microseconds=550000)
    assert iv.check("1w") == timedelta(weeks=1)
    assert iv.check("1d") == timedelta(days=1)
    assert iv.check("0.5d") == timedelta(hours=12)
    assert iv.check("1h") == timedelta(hours=1)
    assert iv.check("1m") == timedelta(minutes=1)
    assert iv.check("1") == timedelta(seconds=1)
    assert iv.check("0.5h") == timedelta(minutes=30)
    assert iv.check("0.001") == timedelta(milliseconds=1)
    assert iv.check("1yr") == relativedelta(years=1)
    assert iv.check("1mo") == relativedelta(months=1)
    assert date + iv.check("4yr") == date + relativedelta(years=4)
    with pytest.raises(t.DataError):
        iv.check("-1")
    with pytest.raises(t.DataError):
        iv.check("a")
    with pytest.raises(t.DataError):
        iv.check("xxh")


def test_time_duration_negative() -> None:
    iv = tx.TimeDuration(allow_negative=True)
    with pytest.raises(t.DataError):
        iv.check("")
    assert iv.check("0.5h") == timedelta(minutes=30)
    assert iv.check("0.001") == timedelta(milliseconds=1)
    assert iv.check("-1") == timedelta(seconds=-1)
    assert iv.check("-3d") == timedelta(days=-3)
    assert iv.check("-1yr") == relativedelta(years=-1)
    assert iv.check("-1mo") == relativedelta(months=-1)
    with pytest.raises(t.DataError):
        iv.check("-a")
    with pytest.raises(t.DataError):
        iv.check("-xxh")


def test_url() -> None:
    iv = tx.URL()
    aws_ecr_url = "https://123456789012.dkr.ecr.us-east-1.amazonaws.com/my-container-repo"
    with pytest.raises(t.DataError):
        iv.check("")
    with pytest.raises(t.DataError):
        iv.check("example.com")
    assert iv.check("https://example.com") == yarl.URL("https://example.com")
    assert iv.check(aws_ecr_url) == yarl.URL(aws_ecr_url)
    iv = tx.URL(scheme_required=False)
    assert iv.check("example.com") == yarl.URL("example.com")


def test_vfolder_id() -> None:
    iv = tx.VFolderID()
    value: VFolderID = iv.check(
        "user:c6bb4a5d-dde6-42bc-92a2-58dc60adfdf1/f40ed400-5571-4a07-bc22-d557b7d44581"
    )
    assert str(value.quota_scope_id) == "user:c6bb4a5d-dde6-42bc-92a2-58dc60adfdf1"
    assert value.folder_id == UUID("f40ed400-5571-4a07-bc22-d557b7d44581")
    value = iv.check(
        "project:6784e3dc-e91c-4b2f-8e0e-d8be890256d8/f40ed40055714a07bc22d557b7d44581"
    )
    assert str(value.quota_scope_id) == "project:6784e3dc-e91c-4b2f-8e0e-d8be890256d8"
    assert value.folder_id == UUID("f40ed400-5571-4a07-bc22-d557b7d44581")
    value2: VFolderID = iv.check(str(value))
    assert value2 == value
    assert str(value2.quota_scope_id) == "project:6784e3dc-e91c-4b2f-8e0e-d8be890256d8"
    assert value2.folder_id == UUID("f40ed400-5571-4a07-bc22-d557b7d44581")
    with pytest.raises(t.DataError):
        iv.check(None)
    with pytest.raises(t.DataError):
        iv.check(1234)
    with pytest.raises(t.DataError):
        iv.check("")
    with pytest.raises(t.DataError):
        iv.check("/")
    with pytest.raises(t.DataError):
        iv.check("///")
    with pytest.raises(t.DataError):
        iv.check(":/x")
    with pytest.raises(t.DataError):
        iv.check(":/f40ed400-5571-4a07-bc22-d557b7d44581")
    with pytest.raises(ValueError, match="Invalid quota scope type"):
        iv.check("abc:def/f40ed400-5571-4a07-bc22-d557b7d44581")
    with pytest.raises(t.DataError):
        iv.check("_abcdef/f40ed400-5571-4a07-bc22-d557b7d44581")
    with pytest.raises(t.DataError):
        iv.check("-abcdef/f40ed400-5571-4a07-bc22-d557b7d44581")
    with pytest.raises(t.DataError):
        iv.check("abcdef-/f40ed400-5571-4a07-bc22-d557b7d44581")
    with pytest.raises(t.DataError):
        iv.check("abcdef//f40ed400-5571-4a07-bc22-d557b7d44581")
    with pytest.raises(t.DataError):
        iv.check("abc/def/f40ed400-5571-4a07-bc22-d557b7d44581")
    with pytest.raises(t.DataError):
        iv.check("user:/5571-4a07-bc22-d557b7d44581")
