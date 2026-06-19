import re

from csvpath.util.class_loader import ClassLoader


def _parse_versions(versions: list[str]) -> list[int]:
    #
    # ["v1", "v2", "v10"] becomes [10, 2, 1]
    #
    if versions is None:
        raise ValueError("Version numbers cannot be None")
    if not versions:
        raise ValueError("Version numbers not provided")
    parsed = []
    for v in versions:
        m = re.fullmatch(r"v(\d+)", v)
        if not m:
            raise ValueError(f"Unrecognized version format: {v!r}")
        parsed.append(int(m.group(1)))
    parsed.sort(reverse=True)
    return parsed


def connect(host, versions: list[str]):
    parsed = _parse_versions(versions)
    last_error = None
    for s in parsed:
        try:
            return ClassLoader.load(
                f"from flightpath.util.api.v{s} import FlightPathServerApiV{s}",
                args=[host],
                kwargs={},
            )
        except (ImportError, ModuleNotFoundError) as ex:
            #
            # this api version isn't implemented locally. i.e. the server is a later
            # release than the client.
            #
            last_error = ex
            continue
        #
        # anything else propagates immediately rather
        # than being mistaken for "version not implemented"
        #
    raise ModuleNotFoundError(
        f"No supported version implementation available "
        f"(server offered: {versions}); last load error: {last_error}"
    )
