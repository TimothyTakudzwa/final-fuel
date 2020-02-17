cd /home/final-fuel
source venv/bin/activate
python manage.py notify_late_deliveries
echo $(date -u) /home/final-fuel/delivery_alerts.log