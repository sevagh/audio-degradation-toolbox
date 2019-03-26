from pydub.playback import play
import os
import sys
from contextlib import contextmanager

# https://stackoverflow.com/a/22434262/4023381
def fileno(file_or_fd):
    fd = getattr(file_or_fd, "fileno", lambda: file_or_fd)()
    if not isinstance(fd, int):
        raise ValueError("Expected a file (`.fileno()`) or a file descriptor")
    return fd


@contextmanager
def suppress_output(to=os.devnull, stdout=None):
    stdout = sys.stdout
    stderr = sys.stderr

    stdout_fd = fileno(stdout)
    stderr_fd = fileno(stderr)

    with os.fdopen(os.dup(stdout_fd), "wb") as copied_stdout, os.fdopen(
        os.dup(stderr_fd), "wb"
    ) as copied_stderr:
        stdout.flush()
        stderr.flush()
        try:
            os.dup2(fileno(to), stdout_fd)
            os.dup2(fileno(to), stderr_fd)
        except ValueError:
            with open(to, "wb") as to_file:
                os.dup2(to_file.fileno(), stdout_fd)
                os.dup2(to_file.fileno(), stderr_fd)
        try:
            yield None
        finally:
            stdout.flush()
            stderr.flush()
            os.dup2(copied_stdout.fileno(), stdout_fd)
            os.dup2(copied_stderr.fileno(), stderr_fd)


def playback_shim(audio):
    with suppress_output():
        play(audio.sound)
