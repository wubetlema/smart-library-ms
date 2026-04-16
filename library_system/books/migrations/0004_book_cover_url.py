from django.db import migrations, models

# Open Library cover API: https://covers.openlibrary.org/b/isbn/{ISBN}-L.jpg
def ol(isbn):
    return f'https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg'

COVERS = {
    '9780062315007': ol('9780062315007'),   # The Alchemist
    '9780061935466': ol('9780061935466'),   # To Kill a Mockingbird
    '9780451524935': ol('9780451524935'),   # 1984
    '9780743273565': ol('9780743273565'),   # The Great Gatsby
    '9780060850524': ol('9780060850524'),   # Brave New World
    '9780735211292': ol('9780735211292'),   # Atomic Habits
    '9781585424337': ol('9781585424337'),   # Think and Grow Rich
    '9780743269513': ol('9780743269513'),   # 7 Habits
    '9780671027032': ol('9780671027032'),   # How to Win Friends
    '9781577314806': ol('9781577314806'),   # The Power of Now
    '9780062316097': ol('9780062316097'),   # Sapiens
    '9780553296983': ol('9780553296983'),   # Diary of a Young Girl
    '9780393317558': ol('9780393317558'),   # Guns Germs and Steel
    '9781599869773': ol('9781599869773'),   # The Art of War
    '9780062397348': ol('9780062397348'),   # A People's History
    '9781612680194': ol('9781612680194'),   # Rich Dad Poor Dad
    '9780804139021': ol('9780804139021'),   # Zero to One
    '9780307887894': ol('9780307887894'),   # The Lean Startup
    '9780066620992': ol('9780066620992'),   # Good to Great
    '9780062060242': ol('9780062060242'),   # Innovator's Dilemma
}


def add_cover_urls(apps, schema_editor):
    Book = apps.get_model('books', 'Book')
    for isbn, url in COVERS.items():
        Book.objects.filter(isbn=isbn).update(cover_url=url)


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0003_book_read_url_seed_books'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='cover_url',
            field=models.URLField(blank=True, max_length=500,
                                  help_text='External cover image URL'),
        ),
        migrations.RunPython(add_cover_urls, migrations.RunPython.noop),
    ]
