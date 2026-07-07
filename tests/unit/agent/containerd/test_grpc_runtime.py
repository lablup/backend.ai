import hashlib

from ai.backend.agent.containerd.grpc_runtime import _chain_id


class TestChainId:
    def test_single_layer_is_the_diff_id(self) -> None:
        assert _chain_id(["sha256:aaa"]) == "sha256:aaa"

    def test_empty_is_empty(self) -> None:
        assert _chain_id([]) == ""

    def test_two_layers_fold_with_sha256(self) -> None:
        d0, d1 = "sha256:aaa", "sha256:bbb"
        expected = "sha256:" + hashlib.sha256(f"{d0} {d1}".encode()).hexdigest()
        assert _chain_id([d0, d1]) == expected

    def test_three_layers_fold_left(self) -> None:
        d = ["sha256:a", "sha256:b", "sha256:c"]
        c1 = "sha256:" + hashlib.sha256(b"sha256:a sha256:b").hexdigest()
        c2 = "sha256:" + hashlib.sha256(f"{c1} sha256:c".encode()).hexdigest()
        assert _chain_id(d) == c2

    def test_deterministic(self) -> None:
        d = ["sha256:1", "sha256:2", "sha256:3"]
        assert _chain_id(d) == _chain_id(d)
