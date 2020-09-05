#!/usr/bin/env python3

import os
import json
import sys
import datetime
import subprocess
import time

import prometheus_client
import yaml

with open(sys.argv[1], 'r') as fd:
    config = yaml.safe_load(fd)

output = {}

class ResticBackblazeCollector(object):
    def __init__(self):
        self._last_update = 0

    def get_info(self):
        for repo in config['repositories']:
            print("Collecting snapshots from backblaze")
            cmd =  [
                "/usr/bin/restic",
                "--repo", "b2:{bucket}:{folder}".format(
                    bucket=repo['bucket'],
                    folder=repo['folder']),
                "snapshots",
                "--json",
                "--no-cache",
                "--no-lock"
            ]

            env = {
                "B2_ACCOUNT_ID": repo["b2_account_id"],
                "B2_ACCOUNT_KEY": repo["b2_account_key"],
                "RESTIC_PASSWORD": repo["restic_password"]
            }

            restic_cmd = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                check=True,
                env=env
            )
            print("Done")

            snapshots = json.loads(restic_cmd.stdout)

            def _get_backup_id(snapshot):
                hostname = snapshot['hostname']
                paths = ','.join(snapshot['paths'])
                return (hostname, paths)

            def _parse_timestamp(timestamp):
                # get rid of everything after .<millieconds>
                timestamp = timestamp.split('.')[0]
                return datetime.datetime.strptime(
                    timestamp,
                    '%Y-%m-%dT%H:%M:%S'
                )

            distinct_backups = []
            for snapshot in snapshots:
                backup = _get_backup_id(snapshot)
                if backup not in distinct_backups:
                    distinct_backups.append(backup)

            latest_snapshots = []
            for backup in distinct_backups:
                latest = None
                latest_timestamp = datetime.datetime.fromtimestamp(0) # unixtime 0
                for snapshot in snapshots:
                    if _get_backup_id(snapshot) == backup:
                        timestamp = _parse_timestamp(snapshot['time'])
                        if timestamp > latest_timestamp:
                            latest = snapshot
                            latest_timestamp = timestamp
                latest_snapshots.append(latest)

            output[repo['name']] = []
            for snapshot in latest_snapshots:
                output[repo['name']].append({
                    "host": snapshot["hostname"],
                    "paths": ",".join(snapshot["paths"]),
                    "timestamp": _parse_timestamp(snapshot['time']).timestamp(),
                })

        return output


    def collect(self):
        called = time.time()

        age = called - self._last_update
        if age > 24 * 60 * 60:
            self._output = self.get_info()
            self._last_update = time.time()
        else:
            print("Using cached metrics")

        metric_timestamp = prometheus_client.core.GaugeMetricFamily(
            'restic_latest_snapshot_timestamp',
            "Timestamp of the latest restic snapshot",
            labels=["repository", "host", "paths"])

        for repo, info in self._output.items():
            for snapshot in info:
                metric_timestamp.add_metric(
                    labels=[
                        repo,
                        snapshot["host"],
                        snapshot["paths"]
                    ],
                    value=snapshot["timestamp"]
                )

        yield metric_timestamp

prometheus_client.REGISTRY.register(ResticBackblazeCollector())

if __name__ == '__main__':
    prometheus_client.start_http_server(int(os.environ["LISTEN_PORT"]))
    while True:
        time.sleep(1)
