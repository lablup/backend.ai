from ai.backend.client.session import Session


def test():
    with Session() as session:
        result = session.RateLimit.get_hot_anonymous_clients()
        print(result)


if __name__ == "__main__":
    test()