from django.urls import path
from Messagerie import views
from Messagerie.views import (  MessageCreateView , MessageDeleteView , 
                                MessageUpdateView , InboxView , SentMessagesView , 
                                MessageDetailVeiw , RessourceListCreateView , RessourceCreateAjaxView , 
                                
                                )
 
urlpatterns = [
    path('ListeDesMessages/', InboxView.as_view(), name='inbox'),
    path('sent/', SentMessagesView.as_view(), name='sent'),
    path('new/', MessageCreateView.as_view(), name='new_message'),

    path("enseignant/ressources/", RessourceListCreateView.as_view(), name="ressources"),
    path("ressource/ajouter/", RessourceCreateAjaxView.as_view(), name="ressource_create"),
    
    path("", views.messagerie_home, name="messagerie_home"),

    # modal read
    path("ajax/message/<int:pk>/", views.message_ajax_detail, name="message_ajax_detail"),

    # selects
    path("ajax/classes/", views.ajax_classes, name="ajax_classes"),
    path("ajax/eleves/", views.ajax_eleves_by_classe, name="ajax_eleves_by_classe"),
    path("ajax/parents/", views.ajax_parents_by_scope, name="ajax_parents_by_scope"),
    path("ajax/profs/", views.ajax_profs_by_scope, name="ajax_profs_by_scope"),

    # notifications
    path("ajax/notifications/", views.ajax_notifications, name="ajax_notifications"),
    path("ajax/unread-count/", views.ajax_unread_count, name="ajax_unread_count"),
    path("ajax/popup-unread/", views.ajax_popup_unread , name="ajax_popup_unread"),  # ✅ NEW

    # delete
    path("ajax/delete/<int:pk>/", views.delete_message, name="delete_message"),

    path('<int:pk>/', MessageDetailVeiw.as_view(), name='message_detail'),
    path('eleve/<int:eleve_id>/envoiyer/', MessageCreateView.as_view(), name='messageParEleve'),
    path('SupprimerDeMessage/<int:pk>/Supprimer/', MessageDeleteView.as_view(), name='supprimer_de_message'),
    path('ModifierDeMessage/<int:pk>/Modifier/', MessageUpdateView.as_view() , name='modiffier_de_message'),
    path("cartes-scolaires/", views.cartes_scolaires_view, name="cartes_scolaires"),

    path("ajax/classes-par-niveau/", views.ajax_classes_par_niveau, name="ajax_classes_par_niveau"),
    path("ajax/eleves-par-classe/", views.ajax_eleves_par_classe, name="ajax_eleves_par_classe"),
]