FROM registry-1.docker.io/library/python:3.11-slim@sha256:45a610eb30c258a202b7000414e1ade0c3549cf5ce1ca16c369e0da116d0fa89

RUN python -m pip install --no-cache-dir \
    pyperf==2.10.0 \
    psutil==7.2.2

RUN mkdir -p /opt/framework
COPY scripts/validate_generated_benchmark.py /opt/framework/
COPY scripts/measure_generated_benchmark.py /opt/framework/
COPY scripts/run_sandbox_command.py /opt/framework/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
