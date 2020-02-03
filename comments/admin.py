from django.contrib import admin
from .models import CommentsPermission, Comment


class CommentsAdmin(admin.ModelAdmin):
    def comments_allowed(self, request):
        objects = self.model.objects.count()
        if objects >= 1:
            return False
        else:
            return True


admin.site.register(Comment)
admin.site.register(CommentsPermission, CommentsAdmin)
