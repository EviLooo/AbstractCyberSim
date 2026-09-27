"""Validate and apply cyber actions without trusting cognition output."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Protocol, Union

from abms_cyber.environment.detection import apply_detection


class ActionType(str, Enum):
    MOVE = "MOVE"
    SCAN = "SCAN"
    EXPLOIT = "EXPLOIT"
    ESCALATE = "ESCALATE"


@dataclass(frozen=True)
class ActionRequest:
    """A cognition request after basic parsing but before world validation."""

    action: ActionType
    target_id: str

    @classmethod
    def from_value(
        cls,
        value: Union["ActionRequest", str, Mapping[str, Any]],
    ) -> "ActionRequest":
        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            parts = value.strip().split(":")
            if len(parts) != 2:
                raise ValueError("action string must use ACTION:TARGET_ID format")
            action_value, target_value = parts
        elif isinstance(value, Mapping):
            action_value = value.get("action")
            target_value = value.get("target_id")
        else:
            raise ValueError("action must be an ActionRequest, string, or mapping")

        if not isinstance(action_value, str) or not action_value.strip():
            raise ValueError("action is required")
        if target_value is None or not str(target_value).strip():
            raise ValueError("target_id is required")

        try:
            action = ActionType(action_value.strip().upper())
        except ValueError as exc:
            allowed = ", ".join(item.value for item in ActionType)
            raise ValueError(f"unknown action; allowed actions are: {allowed}") from exc

        return cls(action=action, target_id=str(target_value).strip())


@dataclass(frozen=True)
class ActionResult:
    """A JSON-ready summary of validation, outcome, and state changes."""

    action: str
    target_id: Optional[str]
    valid: bool
    success: bool
    reason: str
    detection_delta: float = 0.0
    state_changes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ActionAgent(Protocol):
    current_node: Any
    privilege_level: int


class ActionResolver:
    """The single trusted gateway from cognition output to environment changes."""

    def __init__(self, model: Any) -> None:
        self.model = model

    def resolve(
        self,
        agent: ActionAgent,
        action: Union[ActionRequest, str, Mapping[str, Any]],
    ) -> ActionResult:
        try:
            request = ActionRequest.from_value(action)
        except ValueError as exc:
            return ActionResult(
                action="INVALID",
                target_id=None,
                valid=False,
                success=False,
                reason=str(exc),
            )

        target = self.model.network.get_node(request.target_id)
        if target is None:
            return self._invalid(request, "target node does not exist")

        if request.action is ActionType.MOVE:
            return self._move(agent, request, target)
        if request.action is ActionType.SCAN:
            return self._scan(agent, request, target)
        if request.action is ActionType.EXPLOIT:
            return self._exploit(agent, request, target)
        return self._escalate(agent, request, target)

    def _move(self, agent: ActionAgent, request: ActionRequest, target: Any) -> ActionResult:
        source = agent.current_node
        if request.target_id not in source.neighbors:
            return self._invalid(request, "MOVE target must be a direct neighbor")
        if (
            self.model.config.move_requires_compromised_source
            and not source.compromised
        ):
            return self._invalid(request, "current node must be compromised before MOVE")

        previous_node = source.id
        agent.current_node = target
        return self._success(
            request,
            "agent moved to the neighboring node",
            {"previous_node": previous_node, "current_node": target.id},
        )

    def _scan(self, agent: ActionAgent, request: ActionRequest, target: Any) -> ActionResult:
        if target.id != agent.current_node.id:
            return self._invalid(request, "SCAN target must be the current node")

        was_scanned = target.scanned
        target.scanned = True
        update = apply_detection(self.model, self.model.config.scan_detection)
        return self._success(
            request,
            "node scan completed",
            {
                "scanned": True,
                "was_already_scanned": was_scanned,
                "discovered_neighbors": sorted(target.neighbors),
            },
            update.delta,
        )

    def _exploit(self, agent: ActionAgent, request: ActionRequest, target: Any) -> ActionResult:
        if target.id != agent.current_node.id:
            return self._invalid(request, "EXPLOIT target must be the current node")
        if target.compromised:
            return self._success(
                request,
                "node is already compromised",
                {"compromised": True, "changed": False},
            )

        succeeded = self.model.random.random() < target.vulnerability_level
        if succeeded:
            target.compromised = True
            detection_amount = self.model.config.exploit_success_detection
            reason = "exploit succeeded"
        else:
            detection_amount = self.model.config.exploit_failure_detection
            reason = "exploit failed"
        update = apply_detection(self.model, detection_amount)
        return ActionResult(
            action=request.action.value,
            target_id=request.target_id,
            valid=True,
            success=succeeded,
            reason=reason,
            detection_delta=update.delta,
            state_changes={"compromised": target.compromised},
        )

    def _escalate(self, agent: ActionAgent, request: ActionRequest, target: Any) -> ActionResult:
        if target.id != agent.current_node.id:
            return self._invalid(request, "ESCALATE target must be the current node")
        if not target.compromised:
            return self._invalid(request, "node must be compromised before ESCALATE")
        if agent.privilege_level >= self.model.config.required_privilege:
            return self._success(
                request,
                "required privilege is already held",
                {"privilege_level": agent.privilege_level, "changed": False},
            )

        succeeded = (
            self.model.random.random() < self.model.config.escalate_success_prob
        )
        if succeeded:
            agent.privilege_level = self.model.config.required_privilege
            detection_amount = self.model.config.escalate_success_detection
            reason = "privilege escalation succeeded"
        else:
            detection_amount = self.model.config.escalate_failure_detection
            reason = "privilege escalation failed"
        update = apply_detection(self.model, detection_amount)
        return ActionResult(
            action=request.action.value,
            target_id=request.target_id,
            valid=True,
            success=succeeded,
            reason=reason,
            detection_delta=update.delta,
            state_changes={"privilege_level": agent.privilege_level},
        )

    @staticmethod
    def _invalid(request: ActionRequest, reason: str) -> ActionResult:
        return ActionResult(
            action=request.action.value,
            target_id=request.target_id,
            valid=False,
            success=False,
            reason=reason,
        )

    @staticmethod
    def _success(
        request: ActionRequest,
        reason: str,
        state_changes: dict[str, Any],
        detection_delta: float = 0.0,
    ) -> ActionResult:
        return ActionResult(
            action=request.action.value,
            target_id=request.target_id,
            valid=True,
            success=True,
            reason=reason,
            detection_delta=detection_delta,
            state_changes=state_changes,
        )
