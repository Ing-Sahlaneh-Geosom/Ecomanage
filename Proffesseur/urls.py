from django.urls import path
from . import views
from Proffesseur.views import ProffeseurList , ProffeseurDeataille , ProffesseurDelete ,AjouterProfesseur , ProffesseurMessagerie  , ModifieProfesseur
from django.views.i18n import JavaScriptCatalog


urlpatterns = [
    path('LesProffeseur/',ProffeseurList.as_view(), name="Lesensiegnants"),
    path('LeMessagerie/',ProffesseurMessagerie.as_view(), name="LesMessagerie"),
    path('LesDetailleDeProf/<int:pk>/',ProffeseurDeataille.as_view(), name='LesDetailleDeProf'),
    path('DeleteProf/<int:pk>/Supprimer/', ProffesseurDelete.as_view(), name='DeleteProf'),
    path("professeurs/ajouter/", AjouterProfesseur.as_view(), name="AjouterProfesseur"),
    path("professeurs/<int:pk>/modifier/", ModifieProfesseur.as_view(), name="ModifieProfesseur"),

    path("violence/", views.violence_list, name="violence_list"),
    path("violence/save/", views.violence_save, name="violence_save"),   # create/update ajax
    path("violence/<int:pk>/json/", views.violence_json, name="violence_json"),
    path("violence/<int:pk>/delete/", views.violence_delete, name="violence_delete"),

    # endpoints pour selects dépendants
    path("ajax/classes/", views.ajax_classes_by_niveau, name="ajax_classes_by_niveau_violence"),
    path("ajax/eleves/", views.ajax_eleves_by_classe, name="ajax_eleves_by_classe_violence"),
     path("degradations/", views.degradation_page, name="degradation_page"),

    path("degradations/save/", views.degradation_save, name="degradation_save"),
    path("degradations/<int:pk>/json/", views.degradation_json, name="degradation_json"),
    path("degradations/<int:pk>/delete/", views.degradation_delete, name="degradation_delete"),

    # selects dépendants (niveau -> classes -> élèves)
    path("ajax/classes/", views.ajax_classes_by_niveau, name="ajax_classes_by_niveau_degradation"),
    path("ajax/eleves/", views.ajax_eleves_by_classe, name="ajax_eleves_by_classe_degradation"),
    path("degradations/export/excel/", views.degradation_export_excel, name="degradation_export_excel"),
    path("degradations/export/pdf/", views.degradation_export_pdf, name="degradation_export_pdf"),


]

urlpatterns += [
    path("violences/export/excel/", views.violence_export_excel, name="violence_export_excel"),
    path("violences/", views.violence_list, name="violence_list"),

    path("violences/pdf/", views.violence_export_pdf, name="violence_export_pdf"),

    path("violences/ajax/classes/", views.ajax_classes_by_niveau_violence, name="ajax_classes_by_niveau_violence"),
    path("violences/ajax/eleves/", views.ajax_eleves_by_classe_violence, name="ajax_eleves_by_classe_violence"),

    path("violences/json/<int:pk>/", views.violence_json, name="violence_json"),
    path("violences/save/", views.violence_save, name="violence_save"),
    path("violences/delete/<int:pk>/", views.violence_delete, name="violence_delete"),
]