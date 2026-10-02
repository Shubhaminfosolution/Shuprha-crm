from django.db.models import Q
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

from .serializers import PostDetailSerializer, PostSummarySerializer, live_posts


class BlogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class PostListView(generics.ListAPIView):
    serializer_class = PostSummarySerializer
    permission_classes = [AllowAny]
    authentication_classes = []  # public: ignore any token sent by the browser
    pagination_class = BlogPagination

    def get_queryset(self):
        qs = live_posts().filter(noindex=False)
        p = self.request.query_params
        if p.get("category"):
            qs = qs.filter(category__slug=p["category"])
        if p.get("tag"):
            qs = qs.filter(tags__slug=p["tag"])
        if p.get("q"):
            qs = qs.filter(Q(title__icontains=p["q"]) | Q(excerpt__icontains=p["q"]))
        return qs.distinct()


class PostDetailView(generics.RetrieveAPIView):
    serializer_class = PostDetailSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    lookup_field = "slug"

    def get_queryset(self):
        return live_posts()