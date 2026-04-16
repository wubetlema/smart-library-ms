from django.db import migrations
from django.utils.text import slugify


CATEGORIES = [
    ('Fiction', 'Novels, short stories, and imaginative literature.'),
    ('Personal Development', 'Books on self-improvement, habits, and mindset.'),
    ('History', 'Historical events, biographies, and world history.'),
    ('Business', 'Entrepreneurship, management, finance, and economics.'),
]


def add_categories(apps, schema_editor):
    Category = apps.get_model('books', 'Category')
    for name, description in CATEGORIES:
        Category.objects.get_or_create(
            name=name,
            defaults={'description': description, 'slug': slugify(name)},
        )


def remove_categories(apps, schema_editor):
    Category = apps.get_model('books', 'Category')
    Category.objects.filter(name__in=[c[0] for c in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_categories, remove_categories),
    ]
