from ai.backend.common.distributed.raft.resp_interpreter import RespInterpreter


def test_resp_interpreter() -> None:
    interpreter = RespInterpreter()

    interpreter.execute("SET image-pull-rate 0")
    image_pull_rate = interpreter.execute("GET image-pull-rate")
    assert image_pull_rate == 0

    interpreter.execute("INCR image-pull-rate")
    image_pull_rate = interpreter.execute("GET image-pull-rate")
    assert image_pull_rate == 1

    interpreter.execute("INCRBY image-pull-rate 2")
    image_pull_rate = interpreter.execute("GET image-pull-rate")
    assert image_pull_rate == 3
