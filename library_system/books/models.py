from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Book(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('reserved', 'Reserved'),
        ('lost', 'Lost'),
        ('maintenance', 'Under Maintenance'),
    ]

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='books')
    description = models.TextField(blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.PositiveIntegerField(blank=True, null=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    cover_url = models.URLField(max_length=500, blank=True, help_text='External cover image URL')
    read_url = models.URLField(max_length=500, blank=True, help_text='Link to read the book online')
    pdf_file = models.FileField(upload_to='book_pdfs/', blank=True, null=True, help_text='Upload PDF of the book')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    date_added = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def is_available(self):
        return self.available_copies > 0 and self.status == 'available'

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return None
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @property
    def review_count(self):
        return self.reviews.count()


class BookReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('user', 'book')]

    def __str__(self):
        return f"{self.user.username} rated {self.book.title} {self.rating}/5"
