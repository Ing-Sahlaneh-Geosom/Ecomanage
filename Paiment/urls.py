from django.urls import path
from Paiment import views
from Paiment.views import PaimentListView , PaimentCreateView , PaimentDeleteView , PaimentUpdateView , ConfigPaiementView , FraisNiveauView , PaiementFraisView , export_paiement_csv , CaisseView , ajax_classes_by_niveau , ajax_eleves_by_classe  , JournalCaisseView , HistoriqueEleveView , ClotureCaisseView , annuler_recu

urlpatterns = [
    path('ListeDePaiment/', PaimentListView.as_view(), name='liste_de_paiment'),
    path('ConfDePaiment/', ConfigPaiementView.as_view() , name='ConfDePaiment' ),
    path('CreationDePaiment/', PaimentCreateView.as_view(), name='creation_de_paiment'),
    path("finance/frais/", FraisNiveauView.as_view(), name="finance_frais"),
    path("finance/paiement-frais/", PaiementFraisView.as_view(), name="paiement_frais"),
    path("finance/caisse/", CaisseView.as_view(), name="caisse"),
    path("finance/caisse/ajax-classes/", ajax_classes_by_niveau, name="ajax_classes_by_niveau_paiment"),
    path("finance/caisse/ajax-eleves/", ajax_eleves_by_classe, name="ajax_eleves_by_classe_paiment"),
    path("finance/caisse/recu/<uuid:pk>/", views.recu_print, name="recu_print"),
    path("finance/paiement-frais/export/", export_paiement_csv, name="paiement_frais_export"),
    path("finance/caisse/historique/", JournalCaisseView.as_view(), name="journal_caisse"),
    path("finance/caisse/cloture/", ClotureCaisseView.as_view(), name="cloture_caisse"),
    path("finance/caisse/recu/<uuid:recu_id>/annuler/", annuler_recu, name="annuler_recu"),
    path("finance/caisse/historique/eleve/<int:eleve_id>/", HistoriqueEleveView.as_view(), name="historique_eleve"),
    path('CreationDePaiment/<int:eleve_id>/Ajoute', PaimentCreateView.as_view(), name='paiment_par_eleve'),
    path('SuppressionDePaiment/<int:pk>/Supprimer/', PaimentDeleteView.as_view(), name='suppression_de_paiment'),
    path('ModificationDePaiment/<int:pk>/Modifiee/', PaimentUpdateView.as_view(), name='modification_de_paiment')
]
