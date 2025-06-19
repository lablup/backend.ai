from ai.backend.client.session import Session


def test():
    with Session() as session:
        result = session.ComputeSession(
            name="test_session_12abcc7e-a2b6-4578-ae0c-1a0bfcd43b29"
        ).get_info()
        print(f"result: {result}")


if __name__ == "__main__":
    test()
