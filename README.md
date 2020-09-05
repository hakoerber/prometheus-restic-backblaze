```
$ docker build -t prometheus-restic-backblaze .

$ docker run -v $(pwd)/config.yml:/etc/restic-config.yml prometheus-restic-backblaze
```
