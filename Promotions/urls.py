from django.urls import path
from . import views
from .views import EleveDiplomeListView , PromouvoirElevesEnAttenteView , VoirElevesEnPromotionListView , PromotionsParClasseView , PromotionsParNiveauxView , ChangementClasseEleveView , AfficherDecisionFinaleView

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
    path(
        "promotions/eleves-diplomes/",
        EleveDiplomeListView.as_view(),
        name="eleve_diplome_list",
    ),
    path(
        "promotions/promouvoir-eleves-attente/",
        PromouvoirElevesEnAttenteView.as_view(),
        name="promouvoir_eleves_attente",
    ),
    path(
        "promotions/voir-eleves-en-promotion/",
        VoirElevesEnPromotionListView.as_view(),
        name="voir_eleves_promotion",
    ),
    path(
        "promotions/promotions-par-classe/",
        PromotionsParClasseView.as_view(),
        name="promotions_par_classe",
    ),
    path(
        "promotions/promotions-par-niveaux/",
        PromotionsParNiveauxView.as_view(),
        name="promotions_par_niveaux",
    ),
    path(
        "promotions/changement-classe-eleve/",
        ChangementClasseEleveView.as_view(),
        name="changement_classe_eleve",
    ),
    path(
        "promotions/afficher-decision-finale/",
        AfficherDecisionFinaleView.as_view(),
        name="afficher_decision_finale",
    ),
]