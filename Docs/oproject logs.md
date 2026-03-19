✅ How to Stop the Pile‑Up
# 1. Reduce Celery Log Level
In your docker-compose.yml, change the Celery worker command to use --loglevel=WARNING (or ERROR):

yaml
celery_worker:
  command: celery -A core worker --loglevel=WARNING
This suppresses INFO messages (like task completion) and only logs warnings and errors. Apply the same to celery_beat if needed.

After changing, recreate the containers:

bash
docker-compose up -d
# 2. Enable Docker Log Rotation
As previously suggested, add log rotation limits to each service in docker-compose.yml:

yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
This keeps only the last three 10MB log files per container, automatically deleting old ones.

# 3. Optional: Suppress Celery Logs Completely
If you never need to see task logs, you can redirect stdout to /dev/null in the command, but that’s not recommended for debugging.

🧹 Clean Up Existing Logs
To free space now, truncate the current container logs (as shown earlier):

bash
docker ps -q | while read cid; do
    logpath=$(docker inspect --format='{{.LogPath}}' "$cid" 2>/dev/null)
    if [ -n "$logpath" ] && [ -f "$logpath" ]; then
        sudo truncate -s 0 "$logpath"
    fi
done
📉 Expected Result
After these changes, log volume will be drastically reduced, and Docker will automatically rotate what remains, preventing indefinite growth.

If you still see excessive logs, check if any tasks are being retried frequently (due to errors) – but that would be a separate issue.