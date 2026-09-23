FROM perf-benchmark-sandbox:py311-v1

RUN python -m pip install --no-cache-dir \
    openpyxl==3.1.5 \
    fsspec==2025.3.0 \
    cachetools==5.5.0 \
    smart-open==7.0.4
