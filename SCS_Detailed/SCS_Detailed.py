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
        "📆 %Y／%m／%d ⋯ ⏰ %H：%M：%S"
    )
    LOGFILE: Final[Path] = DIRECTORY / "_0_LOGS" / f"🗐{START_TIME}.log"
    INPUTDIR: Final[Path] = DIRECTORY / "_1_INPUTS"
    OUTPUTDIR: Final[Path] = DIRECTORY / "_2_OUTPUTS"

    CM: Final[frozenset[str]] = frozenset(["pass"])
    SE: Final[frozenset[str]] = frozenset(["pass"])
    RES: Final[frozenset[str]] = frozenset(["pass"])

    @final
    def __post_init__(self):
        self.LOGFILE.parent.mkdir(parents=True, exist_ok=True)
        self.INPUTDIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUTDIR.mkdir(parents=True, exist_ok=True)

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
