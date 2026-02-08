from django.urls import path
from . import views

urlpatterns = [
    path("employes/", views.employe_list, name="employe_list"),
    path("employes/create/", views.employe_create, name="employe_create"),
    path("employes/<int:pk>/get/", views.employe_get, name="employe_get"),
    path("employes/<int:pk>/update/", views.employe_update, name="employe_update"),
    path("employes/<int:pk>/delete/", views.employe_delete, name="employe_delete"),
    path("absences/employes/", views.saisie_absences_employes, name="absences_employes"),
    path("absences/employes/suivi/", views.suivi_absences_employes, name="suivi_absences_employes"),
    path("parents/", views.liste_parents, name="liste_parents"),
    path("batiments/", views.batiments_page, name="batiments_page"),

    path("batiments/api/list/", views.batiments_api_list, name="batiments_api_list"),
    path("batiments/api/create/", views.batiments_api_create, name="batiments_api_create"),
    path("batiments/api/<int:pk>/", views.batiments_api_detail, name="batiments_api_detail"),
    path("batiments/api/<int:pk>/update/", views.batiments_api_update, name="batiments_api_update"),
    path("batiments/api/<int:pk>/delete/", views.batiments_api_delete, name="batiments_api_delete"),


    path("salles/", views.salles_page, name="salles_page"),

    # API helpers
    path("salles/api/batiments/", views.salles_api_batiments, name="salles_api_batiments"),
    path("salles/api/etages/", views.salles_api_etages, name="salles_api_etages"),

    # API CRUD
    path("salles/api/list/", views.salles_api_list, name="salles_api_list"),
    path("salles/api/create/", views.salles_api_create, name="salles_api_create"),
    path("salles/api/<int:pk>/", views.salles_api_detail, name="salles_api_detail"),
    path("salles/api/<int:pk>/update/", views.salles_api_update, name="salles_api_update"),
    path("salles/api/<int:pk>/delete/", views.salles_api_delete, name="salles_api_delete"),
]