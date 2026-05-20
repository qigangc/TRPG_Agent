from worlds.base import WorldBase
from worlds.dnd import DNDWorld
from worlds.cnc import CNCWorld

WORLD_REGISTRY: dict[str, WorldBase] = {
    "dnd": DNDWorld(),
    "cnc": CNCWorld(),
}


def get_world(world_id: str) -> WorldBase:
    if world_id not in WORLD_REGISTRY:
        raise ValueError(f"Unknown world: {world_id}. Available: {list(WORLD_REGISTRY.keys())}")
    return WORLD_REGISTRY[world_id]
