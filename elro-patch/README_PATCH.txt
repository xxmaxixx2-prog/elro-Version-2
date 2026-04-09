Pi Receiver patch

Changed files:
- pi5-receiver-configurable/api/app.py
- pi5-receiver-configurable/host/start-kiosk.sh
- pi5-receiver-configurable/docker-compose.yml

What this patch does:
- keeps the current Pi Receiver page structure
- adds Start Kiosk and Stop Kiosk buttons next to the title
- Open URL now also enables kiosk automatically
- API can toggle ENABLE_KIOSK in receiver.env
- host kiosk script stays alive and reacts to ENABLE_KIOSK changes without manual systemctl start/stop each time
- docker-compose mounts receiver.env into the API container so the API can update it

Recommended apply steps on the Pi:
1. Back up your current files.
2. Copy the three patched files into your repo.
3. Make sure the host script is executable:
   chmod +x host/start-kiosk.sh
4. Reinstall the host script so /opt/pi-receiver/host/start-kiosk.sh is updated:
   ./host/install_host_kiosk.sh
5. Rebuild the API container:
   sudo docker compose --env-file receiver.env up -d --build
6. Ensure the kiosk service is running once:
   sudo systemctl enable --now pi-receiver-kiosk.service

Important:
- After this patch, the service should stay running and react to ENABLE_KIOSK=1/0.
- The old manual scripts can still exist, but the web UI should no longer need them for normal start/stop usage.
