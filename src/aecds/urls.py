from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from utilisateur import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include('page.urls')),
    path("glossaire/", include('glossaire.urls')),
    path('journal/', include('journal.urls')),
]

url_users = [
    path('login/', user_views.LoginView.as_view(template_name="utilisateur/login.html"), name="login"),
    path('logout/', user_views.LogoutView.as_view(template_name="utilisateur/logout.html"), name="logout"),
    path('password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name="utilisateur/password_reset.html"
            ),
        name="password_reset"),
    path('password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name="utilisateur/password_reset_done.html"
            ),
        name="password_reset_done"),
    path('password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name="utilisateur/password_reset_confirm.html"
            ),
        name="password_reset_confirm"),
    path('password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name="utilisateur/password_reset_complete.html"
            ),
        name="password_reset_complete"),
    path('profile/', user_views.profile, name="profile"),
    path('register/', user_views.register, name="register"),
]

urlpatterns += url_users

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)