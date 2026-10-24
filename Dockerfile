# The sandbox image every generated script runs in (imle.sandbox.run_script).
# Versions match what role 2 tests the agent with and what A3's prompt lists
# (agents/coding.py PACKAGES); change them together.
#
#     docker build -t imle-sandbox:latest .
FROM python:3.13.6-slim

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY docker-requirements.txt /tmp/docker-requirements.txt
RUN pip install -r /tmp/docker-requirements.txt \
 && pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu \
 && rm /tmp/docker-requirements.txt
