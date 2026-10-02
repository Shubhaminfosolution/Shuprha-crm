import math

from django.db.models import Q
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator
from rest_framework import serializers

from .models import BlogPost, Category, Tag


def live_posts():
    """Only published posts whose publish time has passed."""
    return (
        BlogPost.objects.filter(status="published", published_at__lte=timezone.now())
        .select_related("category", "author")
        .prefetch_related("tags")
        .order_by("-published_at")
    )


class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["name", "slug"]


class TagMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "slug"]


class PostSummarySerializer(serializers.ModelSerializer):
    excerpt = serializers.SerializerMethodField()
    featured_image = serializers.SerializerMethodField()
    category = CategoryMiniSerializer(read_only=True)
    tags = TagMiniSerializer(many=True, read_only=True)
    author = serializers.SerializerMethodField()
    reading_time_minutes = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id", "title", "slug", "excerpt",
            "featured_image", "featured_image_alt",
            "category", "tags", "author",
            "published_at", "reading_time_minutes",
        ]

    def get_excerpt(self, obj):
        return obj.excerpt or Truncator(strip_tags(obj.content or "")).chars(160)

    def get_featured_image(self, obj):
        if not obj.featured_image:
            return None
        url = obj.featured_image.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def get_author(self, obj):
        user = obj.author
        if not user:
            return {"name": ""}
        return {"name": user.get_full_name() or user.get_username()}

    def get_reading_time_minutes(self, obj):
        words = len(strip_tags(obj.content or "").split())
        return max(1, math.ceil(words / 200))


class PostDetailSerializer(PostSummarySerializer):
    meta_title = serializers.SerializerMethodField()
    meta_description = serializers.SerializerMethodField()
    related_posts = serializers.SerializerMethodField()

    class Meta(PostSummarySerializer.Meta):
        fields = PostSummarySerializer.Meta.fields + [
            "content", "meta_title", "meta_description",
            "canonical_url", "noindex", "updated_at", "related_posts",
        ]

    def get_meta_title(self, obj):
        return obj.meta_title or obj.title

    def get_meta_description(self, obj):
        return obj.meta_description or self.get_excerpt(obj)

    def get_related_posts(self, obj):
        qs = live_posts().exclude(pk=obj.pk)
        if obj.category_id:
            qs = qs.filter(category_id=obj.category_id)
        return PostSummarySerializer(qs[:3], many=True, context=self.context).data