from django.urls import path

from Note.views import NoteListeView , NoteCreateView , NoteUpdateView , NoteDeleteView
from Note import views

urlpatterns = [
    path('ListeDesNotes/', NoteListeView.as_view() , name='ListeDesNotes'),
    path('CreationdesNotes/', NoteCreateView.as_view(), name='CreationdesNotes'),
    path('bulletin/selection/' , views.selectionner_bulletin, name='choisir_bulletin'),
    path('CreationdesNotes/<int:eleve_id>/', NoteCreateView.as_view(), name='Notes_eleve'),
    path('ModificationdeNote/<int:pk>/Modifier/' , NoteUpdateView.as_view(), name='ModificationdeNote'),
    path('SupprimmationdeNote/<int:pk>/Supprimer/' , NoteDeleteView.as_view() , name='SupprimmationdeNote'),
  
    path("periodes/", views.periode_list, name="periode_list"),
    path("periodes/<int:pk>/active/", views.periode_toggle_active, name="periode_toggle_active"),

    # devoirs
    path("devoirs/", views.devoir_list, name="devoir_list"),
    path("devoirs/create/", views.devoir_create, name="devoir_create"),
    path("devoirs/<int:pk>/", views.devoir_detail, name="devoir_detail"),

    # notes
    path("notes/", views.notes_gestion, name="notes_gestion"),
    path("notes/saisie/", views.note_saisie_setup, name="note_saisie_setup"),
    path("notes/saisie/<int:devoir_id>/<int:classe_id>/", views.note_saisie, name="note_saisie"),
    path("notes/import/", views.note_import, name="note_import"),
    path("notes/import/template/", views.note_import_template_xlsx, name="note_import_template_csv"),

    # dispenses
    path("dispenses/", views.dispense_list, name="dispense_list"),

    # bulletins
    path("bulletins/", views.bulletin_list, name="bulletin_list"),
    path("bulletins/visual/", views.bulletins_visual, name="bulletins_visual"),
    
    path("rapport-conseil/", views.rapport_conseil_classe, name="rapport_conseil_classe"),


]