from django.contrib import admin
from user.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    search_fields = ('username', 'first_name', 'last_name')
