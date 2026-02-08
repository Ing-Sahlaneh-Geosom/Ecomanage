from tkinter.font import names

from django.urls import path

from Matier.views import ListMetier , CreateMatiere , ModifierMatiere , SupprimerMatiere
from Matier import views

urlpatterns = [
    path('listesDesMetier/', ListMetier.as_view() , name='listesdesmetier'),
    path('CreeUneMatiere/', CreateMatiere.as_view(), name='AjouterDesMatiere'),
    path('bulletin/<int:eleve_id>/', views.bulletin_pdf , name='bulletin_bdf'),
    path('ModifierUneMatiere/<int:pk>/Modifier/', ModifierMatiere.as_view(), name='ModifierUneMatier'),
    path('SupprimerUneMatiere/<int:pk>/Supprimer/', SupprimerMatiere.as_view(), name='SupprimerUneMatiere'),
     path("appreciations/periodes/", views.appreciation_periode_list, name="periode_liste"),
    path("appreciations/periodes/create/", views.appreciation_periode_create, name="periode_create"),
    path("appreciations/periodes/<int:pk>/update/", views.appreciation_periode_update, name="periode_update"),
    path("appreciations/periodes/<int:pk>/delete/", views.appreciation_periode_delete, name="periode_delete"),

    # Annuelles
    path("appreciations/annuelles/", views.appreciation_annuelle_list, name="annuelle_list"),
    path("appreciations/annuelles/create/", views.appreciation_annuelle_create, name="annuelle_create"),
    path("appreciations/annuelles/<int:pk>/update/", views.appreciation_annuelle_update, name="annuelle_update"),
    path("appreciations/annuelles/<int:pk>/delete/", views.appreciation_annuelle_delete, name="annuelle_delete"),

    # Absences
    path("appreciations/absences/", views.appreciation_absence_list, name="absence_list"),
    path("appreciations/absences/create/", views.appreciation_absence_create, name="absence_create"),
    path("appreciations/absences/<int:pk>/update/", views.appreciation_absence_update, name="absence_update"),
    path("appreciations/absences/<int:pk>/delete/", views.appreciation_absence_delete, name="absence_delete"),

    # Config moyen (sans âge)
    path("config-moyenne/", views.config_moyenne_list, name="moyenne_list"),
    path("config-moyenne/create/", views.config_moyenne_create, name="moyenne_create"),
    path("config-moyenne/<int:pk>/update/", views.config_moyenne_update, name="moyenne_update"),
    path("config-moyenne/<int:pk>/delete/", views.config_moyenne_delete, name="moyenne_delete"),

    # Prolonger saisie
    path("prolonger-saisie-notes/", views.prolonger_saisie_notes, name="prolonger"),
    path("prolonger-saisie-notes/<int:pk>/update/", views.prolonger_saisie_notes_update, name="prolonger_update"),

     path("decisions-promotion/", views.decision_promotion_list, name="promotion_list"),
    path("decisions-promotion/create/", views.decision_promotion_create, name="promotion_create"),
    path("decisions-promotion/<int:pk>/update/", views.decision_promotion_update, name="promotion_update"),
    path("decisions-promotion/<int:pk>/delete/", views.decision_promotion_delete, name="promotion_delete"),

    # Decision absence
    path("decision-absence/", views.decision_absence_list, name="decision_absence_list"),
    path("decision-absence/create/", views.decision_absence_create, name="decision_absence_create"),
    path("decision-absence/<int:pk>/update/", views.decision_absence_update, name="decision_absence_update"),
    path("decision-absence/<int:pk>/delete/", views.decision_absence_delete, name="decision_absence_delete"),

    # Cloture periodes
    path("cloture-periodes/", views.cloture_periode_list, name="cloture_list"),
    path("cloture-periodes/create/", views.cloture_periode_create, name="cloture_create"),
    path("cloture-periodes/<int:pk>/toggle/", views.cloture_periode_toggle, name="cloture_toggle"),
    path("cloture-periodes/<int:pk>/delete/", views.cloture_periode_delete, name="cloture_delete"),

    path("config/periodes/prolongation/", views.prolongation_periode, name="prolongation_periode"),
    path("config/periodes/prolongation/<int:pk>/update/", views.prolongation_periode_update, name="prolongation_periode_update"),


]

