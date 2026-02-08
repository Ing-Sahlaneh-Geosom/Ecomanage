from django.conf.urls.static import static
from django.urls import path
from Ecole_admin import views
from Ecole_admin.views import  AjouterAnnee , AjouterDesEleves , ElevesUpdateView , ListeDesUtilisateur , SupprimerEleve , UpdateUser , SupprimerUser,EleveListView, CreateUtilisateur
from Ecomanage import settings
from Absences.views import AjouterDesAbsences

urlpatterns = [
    path('listeDesEleves/', EleveListView.as_view() , name='les_eleves'),
    path('AjouteDesEleves/', AjouterDesEleves.as_view() , name='Ajouter'),
    path('UserFormillaire/', CreateUtilisateur.as_view()  , name='AjouteUtilisateur'),
    path('ListeDesUtilisateur/', ListeDesUtilisateur.as_view() , name='Les_Utlisateur'),
    path('Deconnection/', views.deconnection,name='deconnection'),
    path('Connection/', views.connectionDesUtilisateur, name="Connection"),
    path('listeDesEleves/<int:id>/', views.DetailsDesEleves , name="detaille"),
    path('eleves/<int:eleve_id>/ajouter-absence', AjouterDesAbsences.as_view(), name="Ajoute_apsence"),
    path('AjouteDesEleves/<int:pk>/modifier/', ElevesUpdateView.as_view(), name="EditView"),
    path("profil/changer-mot-de-passe/", views.changer_mot_de_passe, name="changer_mdp"),
    path('SuppresionDesEleves/<int:pk>/Supprimer/', SupprimerEleve.as_view(), name="Supprimer"),
    path('ModifierUser/<int:pk>/Modifier/', UpdateUser.as_view()  , name="ModifierDesUtilisateur"),
    path('SupprimerUser/<int:pk>/Supprimer', SupprimerUser.as_view() , name="SupprimerUser"),
    path('AjouteAnnee/', AjouterAnnee.as_view() , name='AjouteAnnee'),
    path('Parametre/',views.Parametre,name='parametre'),
    path('Parametre/annee/', views.Annee , name='parametre_annee'),
    path('Parametre/A_propos/', views.A_propos , name='parametre_a_propos'),
    path("certificat-scolarite/", views.certificat_scolarite, name="certificat_scolarite"),

    # AJAX
    path("ajax-classes/", views.ajax_classes_by_niveau, name="ajax_classes_by_niveau_scolarite"),
    path("ajax-eleves/", views.ajax_eleves_by_classe, name="ajax_eleves_by_classe_scolarite"),
    path("ajax-eleve-info/", views.ajax_eleve_info, name="ajax_eleve_info_scolarite"),

]