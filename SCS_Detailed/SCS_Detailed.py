import datetime
import pathlib
import zoneinfo
from datetime import tzinfo
from pathlib import Path
from typing import Final, final

import ibis
from ibis import Table
from ibis.backends import BaseBackend
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

    CM: Final[frozenset[str]] = frozenset(["pass"])
    SE: Final[frozenset[str]] = frozenset(["pass"])
    RES: Final[frozenset[str]] = frozenset(["pass"])

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


def initialize_ibis() -> BaseBackend:
    ibis.options.interactive = True
    ibis.options.verbose = True
    return ibis.polars.connect()


def ingest_latest_input_file(con: BaseBackend) -> Table:
    most_recent_file: Path = max(
        (f for f in CONST.INPUT_DIR.iterdir() if f.is_file()),
        key=lambda x: x.stat().st_mtime_ns,
    )
    table: Table = con.read_csv(most_recent_file)

    return table


def main() -> None:
    print(CONST.START_TIME)
    con: BaseBackend = initialize_ibis()
    table: Table = ingest_latest_input_file(con)
    print(table)


if __name__ == "__main__":
    main()
