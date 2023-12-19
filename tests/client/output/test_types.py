from ai.backend.client.output.types import FieldSet, FieldSpec


def test_fieldspec_init():
    f = FieldSpec("key_foo")
    assert f.field_ref == "key_foo"
    assert f.field_name == "key_foo"
    assert f.humanized_name == "Key Foo"
    assert f.alt_name == "key_foo"
    assert not f.subfields

    f = FieldSpec("key_foo", "Foo")
    assert f.field_ref == "key_foo"
    assert f.field_name == "key_foo"
    assert f.humanized_name == "Foo"
    assert f.alt_name == "key_foo"
    assert not f.subfields

    fs = FieldSet([f])
    assert fs["key_foo"] == f

    f = FieldSpec("key_foo", "Foo", alt_name="key_fuu")
    assert f.field_ref == "key_foo"
    assert f.field_name == "key_foo"
    assert f.humanized_name == "Foo"
    assert f.alt_name == "key_fuu"
    assert not f.subfields

    fs = FieldSet([f])
    assert fs["key_fuu"] == f

    f = FieldSpec("key_foo { bar }")
    assert f.field_ref == "key_foo { bar }"
    assert f.field_name == "key_foo"
    assert f.humanized_name == "Key Foo"
    assert not f.subfields  # not initialized in this case

    f = FieldSpec(
        "key_foo",
        subfields=FieldSet([
            FieldSpec("bar"),
            FieldSpec("baz", alt_name="bbb"),
        ]),
    )
    assert f.field_ref == "key_foo { bar baz baz }"
    assert f.field_name == "key_foo"
    assert f.humanized_name == "Key Foo"
    assert f.subfields["bar"].field_ref == "bar"
    assert f.subfields["bbb"].field_ref == "baz"

    f = FieldSpec(
        "key_foo",
        subfields=FieldSet([
            FieldSpec(
                "bar",
                subfields=FieldSet([
                    FieldSpec("kaz"),
                ]),
            ),
        ]),
    )
    assert f.field_ref == "key_foo { bar { kaz } bar { kaz } }"
    assert f.field_name == "key_foo"
    assert f.humanized_name == "Key Foo"
    assert f.subfields["bar"].field_ref == "bar { kaz }"
