"""Bound subprocess trees, not just the shell/JVM at their root."""
import os
import signal
import subprocess


def run_isolated(command, *, input=None, timeout=None, check=False,
                 capture_output=False, **kwargs):
    if capture_output:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if input is not None:
        kwargs['stdin'] = subprocess.PIPE
    process = subprocess.Popen(command, start_new_session=True, **kwargs)
    try:
        stdout, stderr = process.communicate(input=input, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        except ProcessLookupError:
            stdout, stderr = process.communicate()
        exc.output, exc.stderr = stdout, stderr
        raise
    finally:
        # A successful launcher can still leave daemon/tool processes behind.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    if check:
        result.check_returncode()
    return result
