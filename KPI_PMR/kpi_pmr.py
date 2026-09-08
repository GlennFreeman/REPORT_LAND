import datetime
import pathlib
import zoneinfo
from datetime import tzinfo
from pathlib import Path
from typing import Final, final

from msgspec import Struct


@final
class _Constants(Struct, frozen=True, kw_only=True):
    FILE_NAME: Final[str] = pathlib.Path(__file__).name
    DIRECTORY: Final[Path] = pathlib.Path(__file__).parent
    TIMEZONE: Final[tzinfo] = (
        datetime.datetime.now().astimezone().tzinfo
        or zoneinfo.ZoneInfo("America/New_York")
    )
    START_TIME: Final[str] = datetime.datetime.now(TIMEZONE).strftime(
        "📆 %Y／%m／%d ⋯ ⏰ %H：%M：%S"
    )
    LOG_FILE: Final[Path] = DIRECTORY / "_0_LOGS" / f"🗐{START_TIME}.log"
    INPUT_DIR: Final[Path] = DIRECTORY / "_1_INPUTS"
    OUTPUT_DIR: Final[Path] = DIRECTORY / "_2_OUTPUTS"

    @final
    def __post_init__(self):
        self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    @final
    def __repr__(self) -> str:
        return f"<_Constants file='{self.FILE_NAME}' start='{self.START_TIME}'>"

    @final
    def __str__(self) -> str:
        return self.__repr__()


CONST: Final[_Constants] = _Constants()


def most_recent_file(dir: Path, stem: str | Path | None = None) -> Path:
    match stem:
        case str():
            return max(
                dir.glob(f"*{stem}"),
                key=lambda x: x.stat().st_mtime_ns,
            )
        case Path():
            return max(
                dir.glob(f"*{stem.stem}"),
                key=lambda x: x.stat().st_mtime_ns,
            )
        case _:
            return max(
                (f for f in dir.iterdir() if f.is_file()),
                key=lambda x: x.stat().st_mtime_ns,
            )


def main() -> None:
    pass


if __name__ == "__main__":
    main()
