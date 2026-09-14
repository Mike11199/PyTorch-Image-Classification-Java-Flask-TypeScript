"""Change exits on the dedicated YouTube Tor client between download attempts."""

import time
import os
import socket
from contextlib import contextmanager

from stem import CircStatus, ControllerError, Signal
from stem.connection import AuthenticationFailure
from stem.control import Controller


@contextmanager
def tor_connection(progress):
    ready_by = time.monotonic() + 60
    controller = None
    while controller is None:
        candidate = None
        try:
            address = socket.gethostbyname(os.getenv("VIDEO_TOR_HOST", "127.0.0.1"))
            candidate = Controller.from_port(address=address, port=9051)
            candidate.authenticate()
            controller = candidate
        except (ControllerError, AuthenticationFailure, OSError):
            if candidate:
                candidate.close()
            if time.monotonic() >= ready_by:
                raise ValueError("The YouTube connection is not ready. Please try again shortly.") from None
            progress()
            time.sleep(2)
    try:
        with controller:
            while controller.get_info("status/circuit-established") != "1":
                if time.monotonic() >= ready_by:
                    raise ValueError("The YouTube connection is not ready. Please try again shortly.")
                progress()
                time.sleep(2)
            yield controller
    except ControllerError as error:
        raise ValueError("The YouTube connection was interrupted. Please try again.") from error


def change_exit(controller, progress):
    exits = {
        "$" + circuit.path[-1][0]
        for circuit in controller.get_circuits()
        if circuit.status == CircStatus.BUILT and circuit.purpose == "GENERAL"
        and len(circuit.path) >= 3
    }
    excluded = set(filter(None, (controller.get_conf("ExcludeExitNodes", "") or "").split(",")))
    # Keep exclusions bounded on this long-running, single-worker Tor client.
    if len(excluded) > 32:
        excluded.clear()
    excluded.update(exits)
    controller.set_conf("ExcludeExitNodes", ",".join(sorted(excluded)))
    while controller.get_newnym_wait() > 0:
        progress()
        time.sleep(min(2, controller.get_newnym_wait()))
    controller.signal(Signal.NEWNYM)
