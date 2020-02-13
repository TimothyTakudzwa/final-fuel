from django.contrib import admin
from .models import CommentsPermission, Comment


"""

Comments Admin

"""


class CommentsAdmin(admin.ModelAdmin):
    """Restricting comments"""
    def comments_allowed(self, request):
        objects = self.model.objects.count()
        if objects >= 1:
            return False
        else:
            return True


admin.site.register(Comment)
admin.site.register(CommentsPermission, CommentsAdmin)
