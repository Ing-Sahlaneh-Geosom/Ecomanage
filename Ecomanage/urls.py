from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from Ecole_admin.views import changer_annee
from Ecomanage import views, settings

urlpatterns = [
    path('', views.page_acceuil , name='Acceuil'),
    path('changer-annee/', changer_annee , name='changer_annee'),
    path('EcoAdmin/', admin.site.urls),
    path('ecoadmin/', include('Ecole_admin.urls')),
    path('classeadmin/', include('classe.urls')),
    path('profAdmin/', include('Proffesseur.urls')),
    path('matieradmin/' ,include('Matier.urls')),
    path('Absenceadmin/', include('Absences.urls')),
    path('noteadmin/', include('Note.urls')),
    path('PaimentAdmin/', include('Paiment.urls')),
    path('MessagerieAdmin/', include('Messagerie.urls')),
    path('Administration/', include('Administration.urls')), 
] + static(settings.MEDIA_URL , document_root=settings.MEDIA_ROOT)

