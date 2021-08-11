from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.messages.views import SuccessMessageMixin
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm

class LogoutView(SuccessMessageMixin,LogoutView):
    template_name = 'utilisateur/logout.html'
    success_message = "Salut et merci pour les poissons"

class LoginView(LoginView):
    template_name = 'utilisateur/login.html'

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Vous pouvez maintenant vous connecter.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'utilisateur/register.html', {'form':form})

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, \
        instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Vos informations ont été mises à jour.')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    context = {'u_form':u_form,'p_form':p_form}
    return render(request, 'utilisateur/profile.html', context)
