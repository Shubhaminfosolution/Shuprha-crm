from django.contrib import admin
from .models import Category, Tag, BlogPost


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display  = ['title', 'status', 'category', 'author', 'published_at', 'updated_at']
    list_filter   = ['status', 'category', 'tags']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'featured_image', 'featured_image_alt')
        }),
        ('Taxonomy', {
            'fields': ('category', 'tags')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'canonical_url', 'noindex'),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('status', 'published_at', 'author')
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )