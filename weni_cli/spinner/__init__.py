import sys
import threading
from types import TracebackType
from typing import Literal, Optional

import rich_click as click
from .spinners import snake_clockwise


class Spinner(object):
    def __init__(
        self,
        beep: bool = False,
        disable: bool = False,
        force: bool = False,
        stream: bool = sys.stdout,
        spinner: bool = snake_clockwise,
        delay: float = 0.25,
        label: Optional[str] = None,
        label_placement: Literal["left", "right"] = "right",
        keep_label: bool = False,
        finished_spinner: Optional[str] = None,
    ):
        self.spinner = spinner
        self.disable = disable
        self.beep = beep
        self.force = force
        self.stream = stream
        self.stop_running = None
        self.spin_thread = None
        self.delay = delay
        self.label = label
        self.label_placement = label_placement
        self.keep_label = keep_label
        self.finished_spinner = finished_spinner
        self.tty_output = self.stream.isatty() or self.force
        self.spinner_template = _spinner_template(self.label, self.label_placement)

    def start(self) -> None:
        if self.tty_output and not self.disable:
            self.stop_running = threading.Event()
            self.spin_thread = threading.Thread(target=self.init_spin)
            self.spin_thread.start()

    def stop(self) -> None:
        if self.spin_thread:
            self.stop_running.set()
            self.spin_thread.join()

            if self.tty_output:
                if self.beep:
                    self.stream.write("\7")
                    self.stream.flush()
                spaces = " " * (len(self.spinner_template) - 1)
                self.stream.write(spaces + "\b")
                self.stream.flush()

        if self.keep_label and self.label:
            text = _end_label(self.finished_spinner, self.spinner_template, self.label)
            click.echo(text, file=self.stream)

    def init_spin(self) -> None:
        while not self.stop_running.is_set():
            self.stream.write(self.spinner_template % next(self.spinner))
            self.stream.flush()
            self.stop_running.wait(self.delay)
            self.stream.write("\b")
            self.stream.flush()

        self.stream.write(" ")
        self.stream.write("\b")
        self.stream.flush()

    def __enter__(self) -> "Spinner":
        self.start()
        return self

    def __exit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb: TracebackType) -> bool:
        if not self.disable:
            self.stop()
        return False


def spinner(
    beep: bool = False,
    disable: bool = False,
    force: bool = False,
    stream: bool = sys.stdout,
    spinner: bool = snake_clockwise,
    delay: float = 0.25,
    label: Optional[str] = None,
    label_placement: Literal["left", "right"] = "right",
    keep_label: bool = False,
    finished_spinner: Optional[str] = None,
):
    """This function creates a context manager that is used to display a
    spinner on stdout as long as the context has not exited.

    The spinner is created only if stdout is not redirected, or if the spinner
    is forced using the `force` parameter.

    Parameters
    ----------
    beep : bool
        Beep when spinner finishes.
    disable : bool
        Hide spinner.
    force : bool
        Force creation of spinner even when stdout is redirected.
    stream : IO
        Stream to write the spinner to.
    spinner : cycle[str]
        Spinner animation to display.
    delay : float
        Delay, in seconds, between spinner frames.
    label : Optional[str]
        Label to display next to the spinner.
    label_placement : Literal['left', 'right']
        Whether to display the label to the left or right of the spinner.
    keep_label : bool
        When using a label, keep label around in output (even if redirected) once the spinner is finished.
    finished_spinner : Optional[str]
        When using a label and keep_label is True, replace the spinner character with this character in the
        output that is kept around. Useful for replacing a finished spinner with '✓' or similar.

    Example
    -------

        with spinner():
            do_something()
            do_something_else()

    """
    return Spinner(beep, disable, force, stream, spinner, delay, label, label_placement, keep_label, finished_spinner)


def _spinner_template(label: Optional[str], label_placement: Literal["left", "right"]) -> str:
    if not label:
        return "%s"
    if label_placement == "left":
        return f"{label} %s"
    else:
        return f"%s {label}"


def _end_label(finished_spinner: Optional[str], spinner_template: str, label: str) -> None:
    if finished_spinner:
        return spinner_template % finished_spinner
    else:
        return label
