from django.urls import path
from .views import (
    RapportCentreView,
    RapportElevesParClasseView,
    RapportEffectifNiveauClasseView,
    RapportNotesClasseView,
    RapportDevoirsProfesseurView,
    RapportDispensesMatiereView,
    RapportAbsencesElevesView,
    RapportAbsencesProfesseursView,
    RapportAbsencesEmployesView,
    RapportPaiementsElevesView,
    RapportFraisDusView,
    RapportRecusCaisseView,
    RapportConvocationsParentsView,
    RapportViolenceView,
    RapportDegradationsView,
    RapportEmployesView,
    RapportEmploiTempsClasseView,
    RapportRessourcesPedagogiquesView,
    RapportBatimentsSallesView,
)

urlpatterns = [
    path("rapport-centre/", RapportCentreView.as_view(), name="rapport_centre"),

    path("rapport/eleves/classe/", RapportElevesParClasseView.as_view(), name="rapport_eleves_par_classe"),
    path("rapport/effectif/niveau-classe/", RapportEffectifNiveauClasseView.as_view(), name="rapport_effectif_niveau_classe"),
    path("rapport/notes/classe/", RapportNotesClasseView.as_view(), name="rapport_notes_classe"),
    path("rapport/devoirs/professeur/", RapportDevoirsProfesseurView.as_view(), name="rapport_devoirs_professeur"),
    path("rapport/dispenses/matiere/", RapportDispensesMatiereView.as_view(), name="rapport_dispenses_matiere"),

    path("rapport/absences/eleves/", RapportAbsencesElevesView.as_view(), name="rapport_absences_eleves"),
    path("rapport/absences/professeurs/", RapportAbsencesProfesseursView.as_view(), name="rapport_absences_professeurs"),
    path("rapport/absences/employes/", RapportAbsencesEmployesView.as_view(), name="rapport_absences_employes"),

    path("rapport/paiements/eleves/", RapportPaiementsElevesView.as_view(), name="rapport_paiements_eleves"),
    path("rapport/frais/dus/", RapportFraisDusView.as_view(), name="rapport_frais_dus"),
    path("rapport/recus/caisse/", RapportRecusCaisseView.as_view(), name="rapport_recus_caisse"),

    path("rapport/convocations/parents/", RapportConvocationsParentsView.as_view(), name="rapport_convocations_parents"),
    path("rapport/discipline/violence/", RapportViolenceView.as_view(), name="rapport_violence"),
    path("rapport/discipline/degradations/", RapportDegradationsView.as_view(), name="rapport_degradations"),

    path("rapport/employes/", RapportEmployesView.as_view(), name="rapport_employes"),
    path("rapport/emploi-temps/classe/", RapportEmploiTempsClasseView.as_view(), name="rapport_emploi_temps_classe"),
    path("rapport/ressources/pedagogiques/", RapportRessourcesPedagogiquesView.as_view(), name="rapport_ressources_pedagogiques"),
    path("rapport/infrastructure/salles/", RapportBatimentsSallesView.as_view(), name="rapport_batiments_salles"),
]