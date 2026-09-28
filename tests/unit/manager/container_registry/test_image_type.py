"""The type a scan records for an image, read off its role and feature labels."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from ai.backend.common.docker import LabelName
from ai.backend.manager.container_registry.base import _image_type
from ai.backend.manager.data.image.types import ImageType


class TestImageType:
    @pytest.mark.parametrize(
        ("labels", "expected"),
        [
            pytest.param(
                {LabelName.ROLE: "SYSTEM"},
                ImageType.SYSTEM,
                id="the-system-role-marks-a-system-image",
            ),
            pytest.param(
                {LabelName.FEATURES: "uid-match operation"},
                ImageType.SYSTEM,
                id="the-operation-feature-marks-a-system-image",
            ),
            pytest.param(
                {LabelName.ROLE: "SYSTEM", LabelName.FEATURES: "uid-match private"},
                ImageType.SYSTEM,
                id="the-sftp-server-image-as-a-live-registry-carries-it",
            ),
            pytest.param(
                {LabelName.ROLE: "COMPUTE"},
                ImageType.COMPUTE,
                id="the-compute-role-stays-compute",
            ),
            pytest.param(
                {LabelName.ROLE: "INFERENCE", LabelName.ENDPOINT_PORTS: "vllm"},
                ImageType.COMPUTE,
                id="the-inference-role-is-absorbed-into-compute",
            ),
            pytest.param({}, ImageType.COMPUTE, id="an-image-without-labels-is-compute"),
            pytest.param(
                {LabelName.FEATURES: "uid-match"},
                ImageType.COMPUTE,
                id="a-feature-list-without-operation-stays-compute",
            ),
            pytest.param(
                {LabelName.FEATURES: "uid-match operational"},
                ImageType.COMPUTE,
                id="a-feature-merely-starting-with-operation-does-not-match",
            ),
            pytest.param(
                {LabelName.FEATURES: ""},
                ImageType.COMPUTE,
                id="an-empty-feature-list-is-compute",
            ),
        ],
    )
    def test_the_labels_decide_the_type(
        self, labels: Mapping[str, Any], expected: ImageType
    ) -> None:
        assert _image_type(labels) == expected
