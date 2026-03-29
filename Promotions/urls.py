from django.urls import path
from . import views

app_name = "promotion"

urlpatterns = [
    path(
        "promotion/en-attente/",
        views.promotion_liste_attente,
        name="promotion_liste_attente"
    ),
    path(
        "promotion/evaluations/",
        views.promotion_liste_evaluation,
        name="promotion_liste_evaluation"
    ),
    path(
        "promotion/decisions-finales/",
        views.promotion_liste_decisions_finales,
        name="promotion_liste_decisions_finales"
    ),
    path(
        "promotion/<int:pk>/evaluer/",
        views.promotion_evaluer,
        name="promotion_evaluer"
    ),
    path(
        "promotion/<int:pk>/valider/",
        views.promotion_valider_decision,
        name="promotion_valider_decision"
    ),
    path(
        "promotion/<int:pk>/decision-finale/",
        views.promotion_afficher_decision_finale,
        name="promotion_afficher_decision_finale"
    ),
    path(
        "promotion/<int:pk>/executer/",
        views.promotion_executer,
        name="promotion_executer"
    ),
]