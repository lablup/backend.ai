import uuid

from ai.backend.client.session import Session


def test():
    with Session() as session:
        result = session.Network(
            network_id=uuid.UUID("6d8fc578-60b0-443b-af7c-627d925c4382")
        ).delete()
        print(result)


if __name__ == "__main__":
    test()
