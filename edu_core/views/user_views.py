# Portfolio\Education_Villa\edu_core\views\user_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views import generic
from ..models import UserProfile
from ..forms import UserProfileForm, CertificationForm, CustomUserCreationForm
from django.db.models import Min

class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'edu_core/user/signup.html'

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'edu_core/user/profile.html', {'profile': profile})

@login_required
def edit_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    certifications = profile.certifications.all()
    max_certifications = 5  # Maximum number of certifications allowed

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        certification_form = CertificationForm(request.POST, request.FILES)

        if 'profile_form' in request.POST and profile_form.is_valid():
            profile_form.save()
            return redirect('profile')
        elif 'certification_form' in request.POST:
            if certification_form.is_valid():
                # Check if the limit of certifications is reached
                if certifications.count() >= max_certifications:
                    # Find the oldest certification and delete it
                    oldest_certification = certifications.aggregate(Min('id'))['id__min']
                    certification_to_delete = certifications.get(id=oldest_certification)
                    certification_to_delete.delete()
                
                # Save the new certification
                new_certification = certification_form.save(commit=False)
                new_certification.user_profile = profile
                new_certification.save()
                return redirect('edit_profile')

    else:
        profile_form = UserProfileForm(instance=profile)
        certification_form = CertificationForm()

    return render(request, 'edu_core/user/edit_profile.html', {
        'profile_form': profile_form,
        'certification_form': certification_form,
        'certifications': certifications
    })
