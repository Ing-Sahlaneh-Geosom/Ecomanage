from django.urls import path
from . import views
from classe.views import ClasseCreateView, ListeDesClasse , ClasseUpdateView , ClasseDeleteView , ClasseDetailView , SpecialiteCreateView, NiveauCreateView

urlpatterns = [
    path('lesclasse/', ListeDesClasse.as_view() , name="ListeDesClasse"),
    path('AjouterUneClasse/' , ClasseCreateView.as_view(), name="CreeDesClasses"),
    path('AjouterUneSpecialite/' , SpecialiteCreateView.as_view(), name="CreeDesSpecialite"),
    path('AjouterUneNiveau/' , NiveauCreateView.as_view(), name="CreeDesNiveau"),

    path('ModifierUneClasse/<int:pk>/Modifier/' , ClasseUpdateView.as_view(), name="ModifierDesClasses"),
    path('SupprimerUneClasse/<int:pk>/Supprimer/' , ClasseDeleteView.as_view() , name="SupprimerDesClasses"),
    path('DetailleDesClasse/<int:pk>/Detaille/',ClasseDetailView.as_view(), name="Detaille_d_une_classe"),
   

    path("convocation-parent/", views.convocation_parent, name="convocation_parent"),

    # AJAX
    path("ajax/classes/", views.ajax_classes_by_niveau, name="ajax_classes_by_niveau_conv"),
    path("ajax/eleves/", views.ajax_eleves_by_classe, name="ajax_eleves_by_classe_conv"),
    path("ajax/raisons/create/", views.ajax_raisons_create, name="ajax_raisons_create"),

   
]

