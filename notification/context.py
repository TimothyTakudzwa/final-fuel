from .models import Notification


def notification_alert(request):
    notifications = False
    if request.user.is_authenticated:
        msgs = Notification.objects.filter(user=request.user, is_read=False)
        if msgs.exists():
            for msg in msgs:
                msg_user = Notification.objects.get(user=request.user, is_read=False, id=msg.id)
                msg_user.is_read = True
            return {'notifications': True}
        else:
            return {'notifications': notifications}
    else:
        return {}

