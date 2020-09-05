FROM debian:buster

RUN : \
    && apt-get update \
    && apt-get install -y \
        curl \
        python3 \
        python3-prometheus-client \
        python3-yaml \
        restic \
    && apt-get -y clean

RUN : \
    && curl -s -L -o /usr/local/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.2/dumb-init_1.2.2_amd64 \
    && chmod +x /usr/local/bin/dumb-init

RUN : \
    && curl -s -L https://github.com/restic/restic/releases/download/v0.9.6/restic_0.9.6_linux_amd64.bz2 \
        | bzip2 > /usr/local/bin/restic \
    && chmod +x /usr/local/bin/restic

COPY ./restic-monitor.py /usr/local/bin/restic-monitor

CMD ["/usr/local/bin/dumb-init", "--", "/usr/local/bin/restic-monitor", "/etc/restic-backblaze-config.yml"]
