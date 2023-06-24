from django.contrib import admin
from users.models import User, Follow


class UserAdmin(admin.ModelAdmin):
    """Админка для пользователя."""
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = ('username',)
    search_fields = ('username',)


class FollowAdmin(admin.ModelAdmin):
    """Админка для подписок на авторов."""
    list_display = (
        'user',
        'author',
    )


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
