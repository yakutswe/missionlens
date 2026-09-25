"""Explicitly spoofable actor selection for a localhost synthetic-data demo.

This is not authentication. Never expose these routes to real users or data.
"""

from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Header, HTTPException


@dataclass(frozen=True)
class DemoActor:
    id: str
    role: Literal["analyst", "supervisor"]


ACTORS = {
    "analyst-demo": DemoActor("analyst-demo", "analyst"),
    "supervisor-demo": DemoActor("supervisor-demo", "supervisor"),
}


def get_demo_actor(
    x_demo_actor: Annotated[str | None, Header(alias="X-Demo-Actor")] = None,
) -> DemoActor:
    actor = ACTORS.get(x_demo_actor or "")
    if actor is None:
        raise HTTPException(status_code=401, detail="Select a local demo actor")
    return actor


def require_role(actor: DemoActor, role: str) -> None:
    if actor.role != role:
        raise HTTPException(status_code=403, detail=f"Requires {role} demo role")
