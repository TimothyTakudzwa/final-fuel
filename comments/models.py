from django.db import models

from buyer.models import User
from supplier.models import Subsidiaries

"""

Comments Permissions Model


"""


class CommentsPermission(models.Model):
    allowed = models.BooleanField(default=True)

    def __str__(self):
        return str(self.allowed)

    def save(self, *args, **kwargs):
        super(CommentsPermission, self).save(*args, **kwargs)
        """ One permission rule should be present """
        if CommentsPermission.objects.filter().count() > 1:
            self.delete()


"""

Comments Model


"""


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_comment')
    station = models.ForeignKey(Subsidiaries, on_delete=models.CASCADE, related_name='station_name')
    comment_type = models.CharField(default='USER', max_length=20)
    comment = models.CharField(max_length=200)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f'{str(self.user.username)} - {str(self.station.name)}'

    class Meta:
        ordering = ['date', 'time']

