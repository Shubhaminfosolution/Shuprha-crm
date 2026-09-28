from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
import math


# ─────────────────────────────────────────
# CATEGORY
# ─────────────────────────────────────────
class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    slug        = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ─────────────────────────────────────────
# TAG
# ─────────────────────────────────────────
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ─────────────────────────────────────────
# BLOG POST
# ─────────────────────────────────────────
class BlogPost(models.Model):

    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
    ]

    # ── Core content ──────────────────────
    title       = models.CharField(max_length=255)
    slug        = models.SlugField(max_length=280, unique=True, blank=True)
    excerpt     = models.CharField(
                     max_length=300, blank=True,
                     help_text='Short summary shown in listings. Auto-filled from content if left blank.'
                  )
    content     = models.TextField(help_text='Rich text HTML from Tiptap editor')

    # ── Featured image ────────────────────
    featured_image     = models.ImageField(upload_to='blog/featured/', blank=True, null=True)
    featured_image_alt = models.CharField(
                             max_length=200, blank=True,
                             help_text='Required for SEO/accessibility if an image is set'
                          )

    # ── Taxonomy ───────────────────────────
    category = models.ForeignKey(
                   Category, on_delete=models.SET_NULL,
                   null=True, blank=True,
                   related_name='posts'
               )
    tags     = models.ManyToManyField(Tag, blank=True, related_name='posts')

    # ── SEO fields ─────────────────────────
    meta_title       = models.CharField(
                           max_length=60, blank=True,
                           help_text='Defaults to post title if left blank. Keep under 60 chars.'
                        )
    meta_description = models.CharField(
                           max_length=160, blank=True,
                           help_text='Defaults to excerpt if left blank. Keep under 160 chars.'
                        )
    canonical_url     = models.URLField(blank=True, help_text='Only set if this content is syndicated elsewhere')
    noindex           = models.BooleanField(default=False, help_text='Hide this post from search engines')

    # ── Publishing ──────────────────────────
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)

    # ── Authorship ───────────────────────────
    author = models.ForeignKey(
                 settings.AUTH_USER_MODEL,
                 on_delete=models.SET_NULL,
                 null=True, blank=True,
                 related_name='blog_posts'
             )

    # ── Meta ──────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'published_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        if not self.excerpt and self.content:
            # Strip basic HTML tags for a naive excerpt fallback
            import re
            plain = re.sub('<[^<]+?>', '', self.content)
            self.excerpt = plain[:280].rsplit(' ', 1)[0] + '…' if len(plain) > 280 else plain

        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    # ── SEO helpers ───────────────────────────
    @property
    def effective_meta_title(self):
        return self.meta_title or self.title

    @property
    def effective_meta_description(self):
        return self.meta_description or self.excerpt

    @property
    def reading_time_minutes(self):
        import re
        word_count = len(re.sub('<[^<]+?>', '', self.content).split())
        return max(1, math.ceil(word_count / 200))  # ~200 wpm average

    @property
    def is_live(self):
        return self.status == 'published' and self.published_at and self.published_at <= timezone.now()