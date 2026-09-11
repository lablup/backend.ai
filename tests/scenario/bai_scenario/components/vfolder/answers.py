"""폴더 시나리오가 답을 보는 자리.

노드 하나를 자리마다 보는 일은 여러 표가 같이 하므로 한 번만 적고, 표마다 다른 것은 무엇을
기대하느냐뿐이다. 데이터베이스와 저장소가 정하는 자리는 시나리오가 값을 말할 수 없어
무시한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, override
from uuid import UUID

from bai_scenario.components.domain import WrittenByThisRun
from bai_scenario.components.vfolder.stage import (
    STORAGE_HOST,
    AProjectAndACaller,
)

from ai.backend.common.dto.manager.v2.vfolder.response import (
    SearchVFoldersPayload,
    VFolderNode,
)
from ai.backend.manager.data.project.types import ProjectData
from ai.backend.manager.data.user.types import UserData
from ai.backend.testutils.scenario_steps import (
    Answered,
    Held,
    Same,
    SameAs,
    Skipped,
    Then,
    Told,
    Verdict,
)

# ---------------------------------------------------------------------------
# 답을 보는 자리
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NoAnswer(Verdict):
    """답이 와야 하는 자리가 예외로 막혔다. 그 자리는 볼 것이 없으므로 이것 하나만 답한다."""

    raised: BaseException | None

    @override
    def told(self) -> Told:
        name = type(self.raised).__name__ if self.raised is not None else "아무것도"
        return Told("답", problems=(f"답이 와야 하는데 {name}로 막혔다",))


def look_node(
    node: VFolderNode,
    *,
    named: str,
    owner: UUID | None,
    creator: UserData,
    started: datetime,
    project: ProjectData | None = None,
) -> list[Verdict]:
    """폴더 노드 하나를 자리마다 본다. 데이터베이스와 저장소가 정하는 자리는 무시한다."""
    return [
        Same("host", node.host, STORAGE_HOST),
        Same("metadata.name", node.metadata.name, named),
        Same("metadata.cloneable", node.metadata.cloneable, False),
        Same("metadata.last_used", node.metadata.last_used, None),
        Same(
            "access_control.ownership_type",
            node.access_control.ownership_type,
            "group" if project is not None else "user",
        ),
        Held("ownership.user_id", node.ownership.user_id, SameAs[UUID | None](owner, "소유자"))
        if owner is not None
        else Same("ownership.user_id", node.ownership.user_id, None),
        Held(
            "ownership.creator_id",
            node.ownership.creator_id,
            SameAs[UUID | None](creator.id, "만든 사람"),
        ),
        Same("ownership.creator_email", node.ownership.creator_email, creator.email),
        Same("unmanaged_path", node.unmanaged_path, None),
        Skipped("id", "데이터베이스가 만든다"),
        Skipped("status", "폴더가 만들어지는 동안 오가는 값이다"),
        Held(
            "ownership.project_id",
            node.ownership.project_id,
            SameAs[UUID | None](project.id, "만든 프로젝트"),
        )
        if project is not None
        else Skipped(
            "ownership.project_id",
            "개인 폴더는 그 사람의 개인 프로젝트에 붙는다. 그 id는 사용자를 만들 때 생긴다",
        ),
        Skipped("metadata.usage_mode", "타입이 이미 값을 못박는다"),
        Skipped("metadata.quota_scope_id", "저장소가 정한다"),
        Skipped("access_control.permission", "주인에게는 물어볼 것이 없다"),
        Skipped("quota", "저장소가 답하는 값이라 여기서 말할 수 없다"),
        Held("metadata.created_at", node.metadata.created_at, WrittenByThisRun(started)),
    ]


@dataclass(frozen=True)
class TheFolderBelongsToTheProject(Then[AProjectAndACaller, Any]):
    """만든 폴더가 통째로 오고, 그 주인은 프로젝트다. 개인 주인은 없다."""

    started: datetime
    named: str

    @override
    def says(self) -> str:
        return "만든 폴더 전체가 오고, 주인은 프로젝트다"

    @override
    def look(self, laid: AProjectAndACaller, answered: Answered[Any]) -> list[Verdict]:
        node = answered.response
        if not isinstance(node, VFolderNode):
            return [NoAnswer(answered.raised)]
        return look_node(
            node,
            named=self.named,
            owner=None,
            creator=laid.caller,
            started=self.started,
            project=laid.project,
        )


@dataclass(frozen=True)
class OnlyTheirsIsFound(Then[Any, Any]):
    """훑은 답에 부르는 사람이 볼 것만 담긴다."""

    counted: int

    @override
    def says(self) -> str:
        return f"볼 수 있는 폴더 {self.counted}개만 온다"

    @override
    def look(self, laid: Any, answered: Answered[Any]) -> list[Verdict]:
        page = answered.response
        if not isinstance(page, SearchVFoldersPayload):
            return [NoAnswer(answered.raised)]
        wanted = sorted(one.name for one in laid.seen)
        return [
            Same("items", sorted(one.metadata.name for one in page.items), wanted),
            Same("total_count", page.total_count, len(wanted)),
            Same("has_next_page", page.has_next_page, False),
            Same("has_previous_page", page.has_previous_page, False),
        ]
