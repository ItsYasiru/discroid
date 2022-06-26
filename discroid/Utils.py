from __future__ import annotations

import time
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Any


class Utils:
    @staticmethod
    def calculate_nonce(timestamp: float = time.time()):
        return str((int(timestamp) * 1000 - 1420070400000) * 4194304)

    @staticmethod
    def bind_to_list(data: list, bind: Any) -> list[Any]:
        return [bind(datem) for datem in data]
