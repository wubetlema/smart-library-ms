from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0005_book_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='pdf_file',
            field=models.FileField(blank=True, help_text='Upload PDF of the book', null=True, upload_to='book_pdfs/'),
        ),
    ]
