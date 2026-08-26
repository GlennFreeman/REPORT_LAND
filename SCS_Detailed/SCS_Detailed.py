import datetime
import pathlib
import zoneinfo
from datetime import tzinfo
from pathlib import Path
from typing import Final, final

from msgspec import Struct


@final
class _Constants(Struct, frozen=True, kw_only=True):
    FILENAME: Final[str] = pathlib.Path(__file__).name
    DIRECTORY: Final[Path] = pathlib.Path(__file__).parent
    TIMEZONE: Final[tzinfo] = (
        tz
        if (tz := datetime.datetime.now().astimezone().tzinfo)
        else zoneinfo.ZoneInfo("America/New_York")
    )
    START_TIME: Final[str] = datetime.datetime.now(TIMEZONE).strftime(
        "📆⠀%Y／%m／%d⠀⏰⠀%H：%M：%S"
    )

    @final
    def __str__(self) -> str:
        return ""

    @final
    def __repr__(self) -> str:
        return ""


CONST: Final[_Constants] = _Constants()


def main() -> None:
    print(CONST.START_TIME)


if __name__ == "__main__":
    main()
