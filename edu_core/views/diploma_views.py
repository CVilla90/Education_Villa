# Portfolio\Education_Villa\edu_core\views\diploma_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.db.models import Q
from fpdf import FPDF
from ..models import Diploma
from ..forms import DiplomaForm

def diploma_search(request):
    query = request.GET.get("query", "")
    if query:
        diplomas = Diploma.objects.filter(
            Q(verification_key__icontains=query) | 
            Q(student_name__icontains=query)
        ).distinct()
    else:
        diplomas = Diploma.objects.none()  # Return an empty query if no query is provided

    return render(request, 'edu_core/diploma/diploma_search.html', {'diplomas': diplomas})


def view_diploma_online(request, pk):
    diploma = get_object_or_404(Diploma, pk=pk)
    return render(request, 'edu_core/diploma/diploma_view.html', {'diploma': diploma})


def download_diploma_pdf(request, verification_key):
    # Retrieve the diploma details
    diploma = get_object_or_404(Diploma, verification_key=verification_key)

    # Find image paths
    logo_path = finders.find('edu_core/images/Education Villa logo 2.jpg')
    signature_path = finders.find('edu_core/images/evsignature.jpg')
    evx_logo_path = finders.find('edu_core/images/EVX logo 1.jpg')

    # Create an instance of FPDF and add a page
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()

    # Set a border around the page
    pdf.set_line_width(0.5)
    pdf.rect(10, 10, 277, 190)

    # Add the main title "Certificate"
    pdf.set_font('Arial', 'B', 30)
    pdf.set_xy(0, 40)
    pdf.cell(0, 20, 'Certificate', ln=True, align='C')

    # Add subtitle "to certify that"
    pdf.set_font('Arial', '', 16)
    pdf.cell(0, 10, 'to certify that', ln=True, align='C')

    # Add the student name
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 15, diploma.student_name, ln=True, align='C')

    # Add the course completion statement
    pdf.set_font('Arial', '', 14)
    pdf.cell(0, 10, 'received passing grades and successfully completed', ln=True, align='C')

    # Add the course name
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 15, diploma.course_name, ln=True, align='C')

    # Add "a course offered by Education Villa"
    pdf.set_font('Arial', '', 14)
    pdf.cell(0, 10, 'a course offered by Education Villa', ln=True, align='C')

    # Add issued date and verification key at the bottom
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Issued by: {diploma.issued_by.get_full_name()} on {diploma.issue_date}", ln=True, align='C')
    pdf.cell(0, 10, f"Verification Key: {diploma.verification_key}", ln=True, align='C')

    # Add images: Left side for the logo, right side for the EVX logo
    if logo_path:
        pdf.image(logo_path, x=20, y=30, w=40)  # Adjust size and position for left-side logo
    if evx_logo_path:
        pdf.image(evx_logo_path, x=240, y=150, w=30)  # Adjust size and position for right-side logo
    if signature_path:
        pdf.image(signature_path, x=20, y=160, w=40)  # Adjust position for the signature

    # Output PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="diploma_{verification_key}.pdf"'
    response.write(pdf.output(dest='S').encode('latin1'))

    return response


@login_required
def create_diploma(request):
    if request.method == 'POST':
        form = DiplomaForm(request.POST)
        if form.is_valid():
            diploma = form.save(commit=False)
            diploma.issued_by = request.user  # Automatically set the issuing user
            diploma.save()
            return redirect('view_diploma', pk=diploma.pk)
    else:
        form = DiplomaForm()
    return render(request, 'edu_core/diploma/diploma_create.html', {'form': form})
