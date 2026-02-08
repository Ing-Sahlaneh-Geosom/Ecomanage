from django.urls import path
from . import views
from Absences.views import ListDesAbsences , DetailleDesAbsence , AjouterDesAbsences, ModiferDesAbsences,SupprimerDesAbsences  , EmploiDuTempsListView, EmploiDuTempsGrilleView , EmploiDuTempsSoirGrilleView , SaisieAbsencesEDTView , ajax_prof_data

urlpatterns = [
    path('AbsencesListe/', ListDesAbsences.as_view(), name='ListeDesAbsences'),
    
    path("absences/edt/", SaisieAbsencesEDTView.as_view(), name="absences_edt"),
    path("absences/edt/ajax-prof-data/", ajax_prof_data, name="ajax_prof_data"),
    path('AjouterAbsences/', AjouterDesAbsences.as_view(), name='AjouterAbsences'),

    path("absences/enseignants/", views.saisie_absences_enseignants, name="absences_enseignants"),
    path("absences/enseignants/suivi/", views.suivi_absences_enseignants, name="suivi_absences_enseignants")
,
    path('eleve/<int:eleve_id>/add/', AjouterDesAbsences.as_view(), name='addEleveAbsence'),
    path('AbsenceDetaille/<int:pk>/Detaille/' , DetailleDesAbsence.as_view(), name='AbsenceDetaille'),
    path('AbsencesModifier/<int:pk>/Modifier/', ModiferDesAbsences.as_view(), name='AbsencesModifier'),
    path('AbsenceSupprimer/<int:pk>/Supprimer/', SupprimerDesAbsences.as_view(), name="AbsenceSupprimer"),
    path('ListeDesEmplois/', EmploiDuTempsListView.as_view(),name='Liste_des_emplois'),
    path('ListeDesEmploisGrille/', EmploiDuTempsGrilleView.as_view(),name='Liste_des_emplois_grille'),
    path('ListeDesEmploisSoireGrille/', EmploiDuTempsSoirGrilleView.as_view(),name='Liste_des_emplois_soire_grille'),
    path("suivi-absences/", views.suivi_absences_par_mois, name="suivi_absences_par_mois"),
    path("emploi/grille/", views.EmploiDuTempsGrilleView.as_view(), name="emploi_grille"),

    path("emploi/", views.emploi_list, name="emploi_list"),
    path("emploi/ajouter-auto/", views.emploi_create_auto, name="emploi_create_auto"),
    path("emploi/<int:pk>/modifier-auto/", views.emploi_update_auto, name="emploi_update_auto"),
    path("emploi/<int:pk>/supprimer/", views.emploi_delete, name="emploi_delete"),

    # APIs
    path("emploi/api/niveaux/", views.api_niveaux, name="api_niveaux"),
    path("emploi/api/classes/", views.api_classes, name="api_classes"),
    path("emploi/api/slots/", views.api_slots, name="api_slots"),
    path("emploi/api/resources-free/", views.api_resources_free, name="api_resources_free"),
    path("emploi/api/matieres-by-prof/", views.api_matieres_by_prof, name="api_matieres_by_prof"),
]