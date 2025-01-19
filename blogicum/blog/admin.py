from django.contrib import admin
from blog.models import (
    Category,
    Location,
    Post,
)

admin.site.empty_value_display = '-пусто-'


class PostInline(admin.TabularInline):
    model = Post
    extra = -2


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    search_fields = ('text',)
    list_display = (
        'id',
        'title',
        'text',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
        'created_at',
    )
    list_editable = (
        'category',
        'is_published',
        'location',
    )
    list_filter = ('created_at',)
    list_display_links = ('title',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'id',
        'title',
        'description',
        'slug',
        'is_published',
        'created_at',
    )
    list_editable = (
        'is_published',
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'is_published',
        'created_at',
    )
    list_editable = (
        'is_published',
    )
