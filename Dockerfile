FROM debian:bookworm

RUN : \
    && apt-get update \
    && apt-get install -y \
        backblaze-b2 \
        curl \
        dumb-init \
        python3 \
        python3-prometheus-client \
        python3-yaml \
        restic \
    && apt-get -y clean

COPY ./restic-monitor.py /usr/local/bin/restic-monitor

CMD ["/usr/bin/dumb-init", "--", "/usr/local/bin/restic-monitor", "/etc/restic-backblaze-config.yml"]
