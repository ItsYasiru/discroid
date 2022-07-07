from __future__ import annotations

import time
from random import randint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class Utils:
    @staticmethod
    def calculate_nonce():
        return str((int(time.time()) + 1420070400000) * 700000 + randint(10000, 99999))

    @staticmethod
    def bind_to_list(data: list, bind: Any) -> list[Any]:
        return [bind(datem) for datem in data]
