# prometheus-restic-backblaze

**A prometheus exporter to pull restic snapshot timestamps from Backblaze**

---

[Restic](https://restic.net/) works very well with [Backblaze B2 cloud storage](https://www.backblaze.com/b2/cloud-storage.html).

I wanted to have a way to monitor restic backups in Backblaze with prometheus. We're talking about "black box" monitoring here, so not monitoring the backup process itself but **only** whether a snapshot actually exists in the end.

This prometheus exporter reads restic snapshots in backblaze and reports `restic_latest_snapshot_timestamp` metrics with the unix timestamp of the latest snapshot it can find for a tuple of `(repository, host, paths)`, which will be added as labels.

It can be used as a Docker container, see below.

## Configuration

The config is simple YAML and contains a list of repositories to monitor:

```yaml
repositories:
  - name: name of your repository
    bucket: the b2 bucket
    folder: the subfolder inside the b2 bucket
    b2_account_id: your_b2_api_id
    b2_account_key: your_b2_api_key
    restic_password: your_restic_password
```

## Build and run the container

```
$ docker build -t prometheus-restic-backblaze .
$ docker run -e LISTEN_PORT=8080 -v $(pwd)/config.yml:/etc/restic-config.yml prometheus-restic-backblaze
```

## Example alerting rules

Here is an example alertmanager alert:

```yaml
- alert: BackupTooOld
  expr: time() - restic_latest_snapshot_timestamp > 14 * 24 * 60 * 60 # => 14 days
  annotations:
    summary: |
      Backup for too old: {{$value|humanizeDuration}}

```

It's very important to also add an `absent()` rule, otherwise there would be no alert if the exporter fails:

```yaml
- alert: BackupDataMissingMycloud
  expr: absent(restic_latest_snapshot_timestamp{repository="your_repository"})
  annotations:
    summary: |
      No data for backup from repository {{$labels.repository}}
```
