from django.contrib import admin

from .models import Post, Group, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Модель для админа сайта."""

    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Модель для управления группами в админке."""

    list_display = (
        'title',
        'slug',
        'description'
    )
    empty_value_display = '-пусто-'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Модель для управления комментариями в адмиинке."""

    list_display = (
        'post',
        'author',
        'text',
        'created'
    )
    list_editable = ('text',)
    list_filter = ('created',)
