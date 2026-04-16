import csv
import io
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from accounts.decorators import role_required
from activity.utils import log_action
from .models import BorrowRecord


@login_required
@role_required('admin', 'librarian')
def export_borrows_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="borrow_records.csv"'
    writer = csv.writer(response)
    writer.writerow(['#', 'Member', 'Book', 'ISBN', 'Borrowed Date',
                     'Due Date', 'Returned Date', 'Status', 'Fine (ETB)', 'Fine Paid'])
    for i, r in enumerate(BorrowRecord.objects.select_related('member', 'book').all(), 1):
        writer.writerow([
            i, r.member.get_full_name() or r.member.username,
            r.book.title, r.book.isbn or '',
            r.borrowed_date, r.due_date, r.returned_date or '',
            r.get_status_display(), r.fine_amount, 'Yes' if r.fine_paid else 'No',
        ])
    log_action(request.user, 'EXPORT', 'Exported borrow records CSV', request)
    return response


@login_required
@role_required('admin', 'librarian')
def export_overdue_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="overdue_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['#', 'Member', 'Email', 'Book', 'Due Date', 'Days Overdue', 'Fine (ETB)'])
    for i, r in enumerate(BorrowRecord.objects.filter(status='overdue').select_related('member', 'book'), 1):
        writer.writerow([
            i, r.member.get_full_name() or r.member.username,
            r.member.email, r.book.title,
            r.due_date, r.days_overdue, r.calculate_fine(),
        ])
    log_action(request.user, 'EXPORT', 'Exported overdue report CSV', request)
    return response


@login_required
@role_required('admin', 'librarian')
def export_books_csv(request):
    from books.models import Book
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="books_catalog.csv"'
    writer = csv.writer(response)
    writer.writerow(['#', 'Title', 'Author', 'ISBN', 'Category',
                     'Publisher', 'Year', 'Total Copies', 'Available', 'Status'])
    for i, b in enumerate(Book.objects.select_related('category').all(), 1):
        writer.writerow([
            i, b.title, b.author, b.isbn or '',
            b.category.name if b.category else '',
            b.publisher, b.publication_year or '',
            b.total_copies, b.available_copies, b.get_status_display(),
        ])
    log_action(request.user, 'EXPORT', 'Exported books catalog CSV', request)
    return response


@login_required
@role_required('admin', 'librarian')
def export_report_pdf(request):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
    except ImportError:
        return HttpResponse('reportlab not installed. Run: pip install reportlab', status=500)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('Library System – Full Report', styles['Title']))
    elements.append(Paragraph(f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M")}', styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))

    # Overdue section
    elements.append(Paragraph('Overdue Books', styles['Heading2']))
    overdue = BorrowRecord.objects.filter(status='overdue').select_related('member', 'book')
    data = [['Member', 'Book', 'Due Date', 'Days Overdue', 'Fine (ETB)']]
    for r in overdue:
        data.append([r.member.get_full_name() or r.member.username,
                     r.book.title[:35], str(r.due_date), str(r.days_overdue), str(r.calculate_fine())])
    if len(data) == 1:
        data.append(['No overdue books', '', '', '', ''])

    t = Table(data, colWidths=[4*cm, 6*cm, 3*cm, 3*cm, 3*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#212529')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fff3f3'), colors.white]),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.5*cm))

    # Fines section
    elements.append(Paragraph('Fines Report', styles['Heading2']))
    fines = BorrowRecord.objects.filter(fine_amount__gt=0).select_related('member', 'book')
    data2 = [['Member', 'Book', 'Fine (ETB)', 'Paid', 'Status']]
    for r in fines:
        data2.append([r.member.get_full_name() or r.member.username,
                      r.book.title[:35], str(r.fine_amount),
                      'Yes' if r.fine_paid else 'No', r.get_status_display()])
    if len(data2) == 1:
        data2.append(['No fines recorded', '', '', '', ''])

    t2 = Table(data2, colWidths=[4.5*cm, 6.5*cm, 3*cm, 2*cm, 3*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#212529')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(t2)

    doc.build(elements)
    buffer.seek(0)
    log_action(request.user, 'EXPORT', 'Exported full report PDF', request)
    return HttpResponse(buffer, content_type='application/pdf',
                        headers={'Content-Disposition': 'attachment; filename="library_report.pdf"'})
