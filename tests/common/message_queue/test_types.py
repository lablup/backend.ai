from uuid import UUID

from ai.backend.common.data.user.types import UserData
from ai.backend.common.json import dump_json, load_json
from ai.backend.common.message_queue.types import MessageMetadata


class TestMessageMetadata:
    def test_serialize_with_all_fields(self):
        user = UserData(
            user_id=UUID("12345678-1234-5678-1234-567812345678"),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role="user",
            domain_name="default",
        )
        metadata = MessageMetadata(request_id="req-123", user=user)

        serialized = metadata.serialize()
        assert isinstance(serialized, bytes)

        # Verify the serialized data contains expected fields
        deserialized_dict = load_json(serialized)
        assert deserialized_dict["request_id"] == "req-123"
        assert "user" in deserialized_dict
        assert deserialized_dict["user"]["user_id"] == "12345678-1234-5678-1234-567812345678"
        assert deserialized_dict["user"]["is_authorized"] is True
        assert deserialized_dict["user"]["is_admin"] is False
        assert deserialized_dict["user"]["role"] == "user"
        assert deserialized_dict["user"]["domain_name"] == "default"

    def test_serialize_with_no_user(self):
        metadata = MessageMetadata(request_id="req-456", user=None)

        serialized = metadata.serialize()
        assert isinstance(serialized, bytes)

        deserialized_dict = load_json(serialized)
        assert deserialized_dict["request_id"] == "req-456"
        assert deserialized_dict["user"] is None

    def test_serialize_with_no_request_id(self):
        user = UserData(
            user_id=UUID("87654321-4321-8765-4321-876543218765"),
            is_authorized=True,
            is_admin=True,
            is_superadmin=False,
            role="admin",
            domain_name="test-domain",
        )
        metadata = MessageMetadata(request_id=None, user=user)

        serialized = metadata.serialize()
        assert isinstance(serialized, bytes)

        deserialized_dict = load_json(serialized)
        assert deserialized_dict["request_id"] is None
        assert "user" in deserialized_dict

    def test_serialize_with_no_fields(self):
        metadata = MessageMetadata()

        serialized = metadata.serialize()
        assert isinstance(serialized, bytes)

        deserialized_dict = load_json(serialized)
        assert deserialized_dict["request_id"] is None
        assert deserialized_dict["user"] is None

    def test_deserialize_with_all_fields(self):
        data = {
            "request_id": "req-789",
            "user": {
                "user_id": "11111111-2222-3333-4444-555555555555",
                "is_authorized": True,
                "is_admin": False,
                "is_superadmin": False,
                "role": "member",
                "domain_name": "org1",
            },
        }
        serialized = dump_json(data)

        metadata = MessageMetadata.deserialize(serialized)
        assert metadata.request_id == "req-789"
        assert isinstance(metadata.user, UserData)
        assert str(metadata.user.user_id) == "11111111-2222-3333-4444-555555555555"
        assert metadata.user.is_authorized is True
        assert metadata.user.is_admin is False
        assert metadata.user.is_superadmin is False
        assert metadata.user.role == "member"
        assert metadata.user.domain_name == "org1"

    def test_deserialize_from_string(self):
        data = {
            "request_id": "req-string",
            "user": {
                "user_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "is_authorized": False,
                "is_admin": True,
                "is_superadmin": True,
                "role": "superadmin",
                "domain_name": "system",
            },
        }
        serialized_str = dump_json(data).decode("utf-8")

        metadata = MessageMetadata.deserialize(serialized_str)
        assert metadata.request_id == "req-string"
        assert isinstance(metadata.user, UserData)
        assert str(metadata.user.user_id) == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        assert metadata.user.is_authorized is False
        assert metadata.user.is_admin is True
        assert metadata.user.is_superadmin is True

    def test_deserialize_with_legacy_user_id_field(self):
        # Test backward compatibility - remove user_id if present
        data = {
            "request_id": "req-legacy",
            "user_id": "should-be-removed",
            "user": {
                "user_id": "99999999-8888-7777-6666-555544443333",
                "is_authorized": True,
                "is_admin": False,
                "is_superadmin": False,
                "role": "user",
                "domain_name": "default",
            },
        }
        serialized = dump_json(data)

        metadata = MessageMetadata.deserialize(serialized)
        assert metadata.user is not None
        assert metadata.request_id == "req-legacy"
        assert hasattr(metadata, "user_id") is False  # user_id field should be removed
        assert str(metadata.user.user_id) == "99999999-8888-7777-6666-555544443333"

    def test_deserialize_with_invalid_user_data(self):
        # Test when user is not a dict
        data = {"request_id": "req-invalid", "user": "invalid-user-data"}
        serialized = dump_json(data)

        metadata = MessageMetadata.deserialize(serialized)
        assert metadata.request_id == "req-invalid"
        assert metadata.user is None

    def test_deserialize_with_no_user(self):
        data = {"request_id": "req-no-user"}
        serialized = dump_json(data)

        metadata = MessageMetadata.deserialize(serialized)
        assert metadata.request_id == "req-no-user"
        assert metadata.user is None

    def test_deserialize_empty_data(self):
        data = {}
        serialized = dump_json(data)

        metadata = MessageMetadata.deserialize(serialized)
        assert metadata.request_id is None
        assert metadata.user is None

    def test_serialize_deserialize_roundtrip(self):
        # Test complete roundtrip
        user = UserData(
            user_id=UUID("fedcba98-7654-3210-fedc-ba9876543210"),
            is_authorized=True,
            is_admin=True,
            is_superadmin=False,
            role="manager",
            domain_name="enterprise",
        )
        original = MessageMetadata(request_id="roundtrip-test", user=user)

        serialized = original.serialize()
        deserialized = MessageMetadata.deserialize(serialized)
        assert deserialized.user is not None
        assert original.user is not None
        assert deserialized.request_id == original.request_id
        assert str(deserialized.user.user_id) == str(original.user.user_id)
        assert deserialized.user.is_authorized == original.user.is_authorized
        assert deserialized.user.is_admin == original.user.is_admin
        assert deserialized.user.is_superadmin == original.user.is_superadmin
        assert deserialized.user.role == original.user.role
        assert deserialized.user.domain_name == original.user.domain_name
