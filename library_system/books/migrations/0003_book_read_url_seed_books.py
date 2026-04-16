from django.db import migrations, models
from django.utils.text import slugify

BOOKS = [
    # Fiction
    ('Fiction', 'The Alchemist', 'Paulo Coelho', '9780062315007', 'HarperOne', 1988,
     'A young shepherd travels from Spain to Egypt in search of treasure.',
     'https://www.google.com/books/edition/The_Alchemist/FzVjBgAAQBAJ'),
    ('Fiction', 'To Kill a Mockingbird', 'Harper Lee', '9780061935466', 'Harper Perennial', 1960,
     'A story of racial injustice and childhood innocence in the American South.',
     'https://www.google.com/books/edition/To_Kill_a_Mockingbird/PGR2AwAAQBAJ'),
    ('Fiction', '1984', 'George Orwell', '9780451524935', 'Signet Classic', 1949,
     'A dystopian novel about totalitarianism and surveillance.',
     'https://www.google.com/books/edition/1984/kotPYEqx7kMC'),
    ('Fiction', 'The Great Gatsby', 'F. Scott Fitzgerald', '9780743273565', 'Scribner', 1925,
     'A story of wealth, love, and the American Dream in the 1920s.',
     'https://www.google.com/books/edition/The_Great_Gatsby/iXn5U2IzoBEC'),
    ('Fiction', 'Brave New World', 'Aldous Huxley', '9780060850524', 'Harper Perennial', 1932,
     'A futuristic society controlled by technology and conditioning.',
     'https://www.google.com/books/edition/Brave_New_World/aSgHAAAACAAJ'),

    # Personal Development
    ('Personal Development', 'Atomic Habits', 'James Clear', '9780735211292', 'Avery', 2018,
     'Tiny changes that lead to remarkable results through habit formation.',
     'https://www.google.com/books/edition/Atomic_Habits/XfFvDwAAQBAJ'),
    ('Personal Development', 'Think and Grow Rich', 'Napoleon Hill', '9781585424337', 'Tarcher', 1937,
     'Principles of personal achievement and financial success.',
     'https://www.google.com/books/edition/Think_and_Grow_Rich/fBnsAAAAMAAJ'),
    ('Personal Development', 'The 7 Habits of Highly Effective People', 'Stephen R. Covey', '9780743269513', 'Free Press', 1989,
     'Powerful lessons in personal change and effectiveness.',
     'https://www.google.com/books/edition/The_7_Habits_of_Highly_Effective_People/upUxaNWSaREC'),
    ('Personal Development', 'How to Win Friends and Influence People', 'Dale Carnegie', '9780671027032', 'Pocket Books', 1936,
     'Timeless advice on communication and building relationships.',
     'https://www.google.com/books/edition/How_to_Win_Friends_and_Influence_People/gDqoswEACAAJ'),
    ('Personal Development', 'The Power of Now', 'Eckhart Tolle', '9781577314806', 'New World Library', 1997,
     'A guide to spiritual enlightenment and living in the present.',
     'https://www.google.com/books/edition/The_Power_of_Now/4EBuDQAAQBAJ'),

    # History
    ('History', 'Sapiens', 'Yuval Noah Harari', '9780062316097', 'Harper', 2011,
     'A brief history of humankind from the Stone Age to the present.',
     'https://www.google.com/books/edition/Sapiens/1EiJAwAAQBAJ'),
    ('History', 'The Diary of a Young Girl', 'Anne Frank', '9780553296983', 'Bantam', 1947,
     'The diary of a Jewish girl hiding during the Nazi occupation.',
     'https://www.google.com/books/edition/The_Diary_of_a_Young_Girl/0orjkgEACAAJ'),
    ('History', 'Guns, Germs, and Steel', 'Jared Diamond', '9780393317558', 'W. W. Norton', 1997,
     'Why some civilizations came to dominate others.',
     'https://www.google.com/books/edition/Guns_Germs_and_Steel/E6ZcLc8vMR4C'),
    ('History', 'The Art of War', 'Sun Tzu', '9781599869773', 'Filiquarian', 500,
     'Ancient Chinese military treatise on strategy and tactics.',
     'https://www.google.com/books/edition/The_Art_of_War/weaKDwAAQBAJ'),
    ('History', 'A People\'s History of the United States', 'Howard Zinn', '9780062397348', 'Harper', 1980,
     'American history told from the perspective of ordinary people.',
     'https://www.google.com/books/edition/A_People_s_History_of_the_United_States/AvkEAAAAMBAJ'),

    # Business
    ('Business', 'Rich Dad Poor Dad', 'Robert T. Kiyosaki', '9781612680194', 'Plata Publishing', 1997,
     'What the rich teach their kids about money that the poor do not.',
     'https://www.google.com/books/edition/Rich_Dad_Poor_Dad/aFoKDgAAQBAJ'),
    ('Business', 'Zero to One', 'Peter Thiel', '9780804139021', 'Crown Business', 2014,
     'Notes on startups and how to build the future.',
     'https://www.google.com/books/edition/Zero_to_One/QFkqnAAACAAJ'),
    ('Business', 'The Lean Startup', 'Eric Ries', '9780307887894', 'Crown Business', 2011,
     'How constant innovation creates radically successful businesses.',
     'https://www.google.com/books/edition/The_Lean_Startup/r9x-OXdzpPcC'),
    ('Business', 'Good to Great', 'Jim Collins', '9780066620992', 'HarperBusiness', 2001,
     'Why some companies make the leap and others don\'t.',
     'https://www.google.com/books/edition/Good_to_Great/H4e-DgAAQBAJ'),
    ('Business', 'The Innovator\'s Dilemma', 'Clayton M. Christensen', '9780062060242', 'HarperBusiness', 1997,
     'How disruptive technologies cause great firms to fail.',
     'https://www.google.com/books/edition/The_Innovator_s_Dilemma/SIexi_qgq2gC'),
]


def seed_books(apps, schema_editor):
    Category = apps.get_model('books', 'Category')
    Book = apps.get_model('books', 'Book')

    for (cat_name, title, author, isbn, publisher, year, desc, read_url) in BOOKS:
        cat, _ = Category.objects.get_or_create(
            name=cat_name,
            defaults={'slug': slugify(cat_name)}
        )
        Book.objects.get_or_create(
            isbn=isbn,
            defaults={
                'title': title,
                'author': author,
                'category': cat,
                'publisher': publisher,
                'publication_year': year,
                'description': desc,
                'read_url': read_url,
                'total_copies': 2,
                'available_copies': 2,
                'status': 'available',
            }
        )


def unseed_books(apps, schema_editor):
    Book = apps.get_model('books', 'Book')
    isbns = [b[3] for b in BOOKS]
    Book.objects.filter(isbn__in=isbns).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_seed_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='read_url',
            field=models.URLField(blank=True, max_length=500,
                                  help_text='Link to read the book online'),
        ),
        migrations.RunPython(seed_books, unseed_books),
    ]
