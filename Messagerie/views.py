from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, UpdateView , DetailView
from Ecole_admin.form import MessageForm , RessourceForm
from Ecole_admin.models import Message, User , Ressource , Proffeseur , MessageDestinataire 
from Ecole_admin.utils.mixins import ActiveYearMixin, EcoleAssignMixin
from Ecole_admin.utils.utils import get_annee_active , build_username, unique_username
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.html import escape
from django.contrib import messages

from django.views.decorators.http import require_GET

from django.views.generic import TemplateView


from Ecole_admin.models import Eleve, Classe , Niveau 


from django.shortcuts import render
from django.http import JsonResponse

from django.contrib.auth.decorators import login_required





class InboxView(ListView):
    model = Message
    template_name = 'liste_des_messages.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        queryset = Message.objects.filter(
            annee_scolaire = get_annee_active(self.request),
            ecole = self.request.user.ecole,
            receiver = self.request.user
        ).order_by('-date_envoi')

        titre = self.request.GET.get("titre")
        destinateur = self.request.GET.get('destinateur')
        lu = self.request.GET.get('lu')

        if titre and titre != "":
            queryset = queryset.filter(titre__icontains = titre)
        if destinateur and destinateur != "":
            queryset = queryset.filter(destinateur__id = destinateur)
        if lu and lu != "":
            queryset = queryset.filter(lu__icontains = lu)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        return context


class SentMessagesView(ListView):
    model = Message
    template_name = 'sent.html'
    context_object_name = 'messages'

    def get_queryset(self):
        queryset = Message.objects.filter(
            annee_scolaire = get_annee_active(self.request),
            ecole = self.request.user.ecole,
            receiver = self.request.user
        ).order_by('-date_envoi')
        return queryset


class MessageDetailVeiw(DetailView):
    model = Message
    template_name = 'Message_detail.html'
    context_object_name = 'message'

    def get_object(self, queryset = None):
        obj = super().get_object(queryset)
        if obj.receiver == self.request.user and not obj.lu:
            obj.lu = True
            obj.save()
        return obj

class MessageCreateView(ActiveYearMixin , EcoleAssignMixin , CreateView):
    model = Message
    template_name = 'envoiyer_de_message.html'
    form_class = MessageForm
    success_url = reverse_lazy('inbox')

    def get_initial(self):
        initial = super().get_initial()
        eleve_id = self.kwargs.get("eleve_id")
        if eleve_id:
            initial["eleve"] = eleve_id
        return initial

    # def form_valid(self, form):
    #     eleve_id = self.kwargs.get('eleve_id')
    #     if eleve_id:
    #         form.instance.eleve_id = eleve_id
    #     return super().form_valid(form)

    

    def form_valid(self, form):
        form.instance.sender = self.request.user
        return super().form_valid(form)
    


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        context['Title'] = "Envoiyer une message"
        context['submit_text'] = "Envoiyer"
        return context



class MessageUpdateView(UpdateView):
    model = Message
    template_name = 'envoiyer_de_message.html'
    fields = [
        'titre',
        'contenu',
        'destinateur',
        'lu'
    ]
    success_url = reverse_lazy('liste_des_messages')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        context['Title'] = "Modiffier une message"
        context['submit_text'] = "Modiffier"
        return context


class MessageDeleteView(DeleteView):
    model = Message
    template_name = 'supprimer_de_message.html'
    success_url = reverse_lazy('liste_des_messages')




class RessourceCreateAjaxView(ActiveYearMixin , EcoleAssignMixin , CreateView):
    model = Ressource
    form_class = RessourceForm
    template_name = "create_ajax.html"
    success_url = reverse_lazy("ressources")  # reste sur la même page après save

    def get(self, request, *args, **kwargs):
        # ✅ AJAX : retourne options matières
        if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.GET.get("ajax") == "matieres":
            return self._ajax_matieres(request)
        return super().get(request, *args, **kwargs)

    def _ajax_matieres(self, request):
        professeur_id = (request.GET.get("professeur_id") or "").strip()

        if not professeur_id.isdigit():
            return HttpResponse('<option value="">Sélectionner...</option>')

        prof = (
            Proffeseur.objects
            .select_related("matieres")  # ton FK Professeur -> Matier = "matieres"
            .filter(id=int(professeur_id))
            .first()
        )

        if not prof or not prof.matieres_id:
            return HttpResponse('<option value="">Aucune matière</option>')

        m = prof.matieres
        return HttpResponse(
            '<option value="">Sélectionner...</option>'
            f'<option value="{m.id}">{escape(str(m))}</option>'
        )
    
    


class RessourceListCreateView(ListView):
    model = Ressource
    template_name = "ressources_page.html"
    context_object_name = "ressources"
    paginate_by = 10  # optionnel

    def get_queryset(self):
        return Ressource.objects.select_related("professeur", "matier").order_by("-id")

    # ✅ GET normal = page + form
    # ✅ GET AJAX = options matières
    def get(self, request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest" and request.GET.get("action") == "matieres":
            return self._ajax_matieres(request)
        return super().get(request, *args, **kwargs)

    def _ajax_matieres(self, request):
        professeur_id = (request.GET.get("professeur_id") or "").strip()

        if not professeur_id.isdigit():
            return HttpResponse('<option value="">Sélectionner...</option>')

        prof = (
            Proffeseur.objects
            .select_related("matieres")  # ton FK s'appelle "matieres"
            .filter(id=int(professeur_id))
            .first()
        )

        if not prof or not prof.matieres_id:
            return HttpResponse('<option value="">Aucune matière</option>')

        m = prof.matieres
        html = (
            '<option value="">Sélectionner...</option>'
            f'<option value="{m.id}">{escape(str(m))}</option>'
        )
        return HttpResponse(html)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = ctx.get("form") or RessourceForm()
        return ctx

    # ✅ POST = create
    def post(self, request, *args, **kwargs):
        form = RessourceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Ressource enregistrée.")
            return redirect("ressources")

        # si erreur, on réaffiche la page + modal (tu peux l'ouvrir automatiquement avec JS)
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))







@login_required
def cartes_scolaires_view(request):
    ecole = request.user.ecole
    niveaux = Niveau.objects.filter(ecole=ecole, actif=True).order_by("ordre", "nom")

    niveau_id = request.GET.get("niveau") or ""
    classe_id = request.GET.get("classe") or ""
    eleve_id  = request.GET.get("eleve") or ""

    # Pour remplir "Classe" et "Élève" au rechargement (quand on filtre)
    classes = Classe.objects.none()
    eleves  = Eleve.objects.none()

    if niveau_id:
        classes = Classe.objects.filter(ecole=ecole, actif=True, niveau_id=niveau_id).order_by("nom")

        # Construire queryset élèves selon classe
        if classe_id == "all" or classe_id == "":
            eleves = Eleve.objects.filter(ecole=ecole, classe__niveau_id=niveau_id)
        else:
            eleves = Eleve.objects.filter(ecole=ecole, classe_id=classe_id)

        # Filtre élève précis
        if eleve_id and eleve_id != "all":
            eleves = eleves.filter(id=eleve_id)

        eleves = eleves.select_related("ecole", "classe", "annee_scolaire").order_by("nom")

    return render(request, "cartes_scolaire.html", {
        "niveaux": niveaux,
        "classes": classes,
        "eleves": eleves,

        # garder sélection
        "selected_niveau": str(niveau_id),
        "selected_classe": str(classe_id),
        "selected_eleve": str(eleve_id),
    })


@login_required
def ajax_classes_par_niveau(request):
    ecole = request.user.ecole
    niveau_id = request.GET.get("niveau_id")

    if not niveau_id:
        return JsonResponse([], safe=False)

    classes = Classe.objects.filter(ecole=ecole, actif=True, niveau_id=niveau_id).order_by("nom")
    data = [{"id": c.id, "nom": c.nom} for c in classes]
    return JsonResponse(data, safe=False)


@login_required
def ajax_eleves_par_classe(request):
    ecole = request.user.ecole
    classe_id = request.GET.get("classe_id")
    niveau_id = request.GET.get("niveau_id")  # ✅ pour le cas "all"

    if not classe_id:
        return JsonResponse([], safe=False)

    if classe_id == "all":
        # ✅ IMPORTANT : "all" doit retourner les élèves du NIVEAU sélectionné, pas toute l'école
        if niveau_id:
            qs = Eleve.objects.filter(ecole=ecole, classe__niveau_id=niveau_id)
        else:
            qs = Eleve.objects.filter(ecole=ecole)  # fallback
    else:
        qs = Eleve.objects.filter(ecole=ecole, classe_id=classe_id)

    qs = qs.order_by("nom")
    data = [{"id": e.id, "nom": e.nom} for e in qs]
    return JsonResponse(data, safe=False)






from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils.timezone import localtime
from django.contrib.auth import get_user_model


User = get_user_model()

def role_is(user, *roles):
    r = (getattr(user, "role", "") or "").lower().strip()
    return r in [x.lower() for x in roles]


def unread_qs(user, ecole, annee):
    return Message.objects.filter(
        receiver=user,
        ecole=ecole,
        annee_scolaire=annee,
        lu=False,
        deleted_by_receiver=False
    )


@login_required(login_url="Connection")
def messagerie_home(request):
    ecole = request.user.ecole
    if not ecole:
        return HttpResponseForbidden("Aucune école associée.")

    annee = get_annee_active(request)

    # Inbox (affiche seulement non supprimés par receiver)
    messages_recus = Message.objects.filter(
        receiver=request.user,
        ecole=ecole,
        annee_scolaire=annee,
        deleted_by_receiver=False
    ).order_by("-date_envoi")

    # filtres
    niveaux = Niveau.objects.filter(ecole=ecole).order_by("ordre", "nom")

    # classes du prof (si prof)
    prof_classes = Classe.objects.none()
    if role_is(request.user, "proffesseur"):
        prof = getattr(request.user, "proffeseur", None)
        if prof:
            prof_classes = Classe.objects.filter(ecole=ecole, professeurs=prof).distinct().order_by("nom")

    # ENVOI
    if request.method == "POST":
        # parent ne peut pas envoyer
        if role_is(request.user, "parent"):
            return HttpResponseForbidden("Accès refusé")

        receiver_group = request.POST.get("receiver_group")  # parents/profs/eleves (admin)
        target = request.POST.get("target")

        sujet = (request.POST.get("sujet") or "").strip()
        contenu = (request.POST.get("contenu") or "").strip()

        if not receiver_group or not target:
            messages.error(request, "Choisir le type de destinataire et le filtre.")
            return redirect("messagerie_home")

        if not sujet or not contenu:
            messages.error(request, "Sujet et contenu sont obligatoires.")
            return redirect("messagerie_home")

        receivers = []

        # ==========================
        # ADMIN/SECRETAIRE
        # ==========================
        if role_is(request.user, "admin", "secretaire"):
            # ✅ admin/sec envoie à: parents OU profs
            # (si tu veux aussi eleves → il faut créer des users élèves, sinon impossible)
            if receiver_group == "parents":
                if target == "one":
                    parent_id = request.POST.get("parent_id")
                    if not parent_id:
                        messages.error(request, "Choisir un parent.")
                        return redirect("messagerie_home")
                    parent = get_object_or_404(User, id=parent_id, ecole=ecole, role="parent")
                    receivers = [parent]

                elif target == "classe":
                    classe_id = request.POST.get("classe_id")
                    if not classe_id:
                        messages.error(request, "Choisir une classe.")
                        return redirect("messagerie_home")
                    eleves = Eleve.objects.filter(ecole=ecole, annee_scolaire=annee, classe_id=classe_id).select_related("parent_user")
                    receivers = [e.parent_user for e in eleves if e.parent_user]

                elif target == "niveau":
                    niveau_id = request.POST.get("niveau_id")
                    if not niveau_id:
                        messages.error(request, "Choisir un niveau.")
                        return redirect("messagerie_home")
                    eleves = Eleve.objects.filter(ecole=ecole, annee_scolaire=annee, classe__niveau_id=niveau_id).select_related("parent_user")
                    receivers = [e.parent_user for e in eleves if e.parent_user]

                elif target == "tous":
                    eleves = Eleve.objects.filter(ecole=ecole, annee_scolaire=annee).select_related("parent_user")
                    receivers = [e.parent_user for e in eleves if e.parent_user]
                else:
                    messages.error(request, "Filtre parent invalide.")
                    return redirect("messagerie_home")

            elif receiver_group == "profs":
                if target == "one":
                    prof_id = request.POST.get("prof_id")
                    if not prof_id:
                        messages.error(request, "Choisir un professeur.")
                        return redirect("messagerie_home")
                    prof = get_object_or_404(Proffeseur, id=prof_id, ecole=ecole)
                    if not prof.user:
                        messages.error(request, "Ce professeur n'a pas de compte utilisateur.")
                        return redirect("messagerie_home")
                    receivers = [prof.user]

                elif target == "classe":
                    classe_id = request.POST.get("classe_id")
                    if not classe_id:
                        messages.error(request, "Choisir une classe.")
                        return redirect("messagerie_home")
                    profs = Proffeseur.objects.filter(ecole=ecole, classes__id=classe_id).select_related("user").distinct()
                    receivers = [p.user for p in profs if p.user]

                elif target == "tous":
                    profs = Proffeseur.objects.filter(ecole=ecole).select_related("user")
                    receivers = [p.user for p in profs if p.user]
                else:
                    messages.error(request, "Filtre prof invalide.")
                    return redirect("messagerie_home")

            else:
                messages.error(request, "Groupe destinataire invalide.")
                return redirect("messagerie_home")

        # ==========================
        # PROF
        # ==========================
        elif role_is(request.user, "proffesseur"):
            # prof peut envoyer aux parents, et aussi recevoir/repondre aux admin/sec
            if receiver_group != "parents":
                messages.error(request, "Le professeur peut envoyer seulement aux parents.")
                return redirect("messagerie_home")

            if target == "eleve":
                eleve_id = request.POST.get("eleve_id")
                if not eleve_id:
                    messages.error(request, "Choisir un élève.")
                    return redirect("messagerie_home")
                eleve = get_object_or_404(Eleve, id=eleve_id, ecole=ecole, annee_scolaire=annee)
                if not eleve.parent_user:
                    messages.error(request, "Cet élève n'a pas de compte parent.")
                    return redirect("messagerie_home")
                receivers = [eleve.parent_user]

            elif target == "classe":
                classe_id = request.POST.get("classe_id")
                if not classe_id:
                    messages.error(request, "Choisir une classe.")
                    return redirect("messagerie_home")
                if not prof_classes.filter(id=classe_id).exists():
                    return HttpResponseForbidden("Classe non autorisée")

                eleves = Eleve.objects.filter(ecole=ecole, annee_scolaire=annee, classe_id=classe_id).select_related("parent_user")
                receivers = [e.parent_user for e in eleves if e.parent_user]

            elif target == "toutes":
                eleves = Eleve.objects.filter(ecole=ecole, annee_scolaire=annee, classe__in=prof_classes).select_related("parent_user")
                receivers = [e.parent_user for e in eleves if e.parent_user]
            else:
                messages.error(request, "Filtre invalide.")
                return redirect("messagerie_home")

        else:
            return HttpResponseForbidden("Accès refusé")

        # dedoublonnage
        receivers = list({u.id: u for u in receivers}.values())

        count = 0
        for r in receivers:
            Message.objects.create(
                sender=request.user,
                receiver=r,
                sujet=sujet,
                contenu=contenu,
                lu=False,
                annee_scolaire=annee,
                ecole=ecole
            )
            count += 1

        messages.success(request, f"Message envoyé ✅ ({count} destinataire(s))")
        return redirect("messagerie_home")

    unread_count = unread_qs(request.user, ecole, annee).count()

    return render(request, "messagerie_page.html", {
        "messages_recus": messages_recus,
        "niveaux": niveaux,
        "prof_classes": prof_classes,
        "unread_count": unread_count,
    })


@login_required(login_url="Connection")
def message_ajax_detail(request, pk):
    ecole = request.user.ecole
    annee = get_annee_active(request)

    msg = get_object_or_404(
        Message,
        pk=pk,
        receiver=request.user,
        ecole=ecole,
        annee_scolaire=annee,
        deleted_by_receiver=False
    )

    if not msg.lu:
        msg.lu = True
        msg.save(update_fields=["lu"])

    return JsonResponse({
        "ok": True,
        "id": msg.id,
        "sujet": msg.sujet,
        "from": (msg.sender.nom_complet or msg.sender.username),
        "date": localtime(msg.date_envoi).strftime("%d/%m/%Y %H:%M"),
        "contenu": msg.contenu
    })


@login_required(login_url="Connection")
def ajax_classes(request):
    ecole = request.user.ecole
    classes = Classe.objects.filter(ecole=ecole).order_by("niveau", "nom")
    return JsonResponse({"ok": True, "items": [{"id": c.id, "text": str(c)} for c in classes]})


@login_required(login_url="Connection")
def ajax_eleves_by_classe(request):
    ecole = request.user.ecole
    annee = get_annee_active(request)
    classe_id = request.GET.get("classe_id")

    if not classe_id:
        return JsonResponse({"ok": True, "items": []})

    eleves = Eleve.objects.filter(ecole=ecole, annee_scolaire=annee, classe_id=classe_id).select_related("parent_user").order_by("nom")
    items = [{"id": e.id, "text": f"{e.nom} ({e.classe})"} for e in eleves if e.parent_user]
    return JsonResponse({"ok": True, "items": items})


@login_required(login_url="Connection")
def ajax_parents_by_scope(request):
    if not role_is(request.user, "admin", "secretaire"):
        return JsonResponse({"ok": False, "items": []})

    ecole = request.user.ecole
    annee = get_annee_active(request)

    scope = request.GET.get("scope")
    classe_id = request.GET.get("classe_id")
    niveau_id = request.GET.get("niveau_id")

    eleves = Eleve.objects.filter(ecole=ecole, annee_scolaire=annee).select_related("parent_user", "classe", "classe__niveau")
    if scope == "classe" and classe_id:
        eleves = eleves.filter(classe_id=classe_id)
    if scope == "niveau" and niveau_id:
        eleves = eleves.filter(classe__niveau_id=niveau_id)

    parents = [e.parent_user for e in eleves if e.parent_user]
    parents = list({p.id: p for p in parents}.values())

    items = [{"id": p.id, "text": (p.nom_complet or p.username)} for p in parents]
    return JsonResponse({"ok": True, "items": items})


@login_required(login_url="Connection")
def ajax_profs_by_scope(request):
    if not role_is(request.user, "admin", "secretaire"):
        return JsonResponse({"ok": False, "items": []})

    ecole = request.user.ecole
    scope = request.GET.get("scope")
    classe_id = request.GET.get("classe_id")

    profs = Proffeseur.objects.filter(ecole=ecole).select_related("user")
    if scope == "classe" and classe_id:
        profs = profs.filter(classes__id=classe_id).distinct()

    items = [{"id": p.id, "text": p.nom_conplet} for p in profs if p.user]
    return JsonResponse({"ok": True, "items": items})


@login_required(login_url="Connection")
def ajax_notifications(request):
    user = request.user
    ecole = getattr(user, "ecole", None)
    if not ecole:
        return JsonResponse({"ok": True, "count": 0, "items": []})

    annee = get_annee_active(request)
    qs = unread_qs(user, ecole, annee).order_by("-date_envoi")

    items = []
    for m in qs[:6]:
        items.append({
            "id": m.id,
            "titre": m.sujet,
            "message": (m.contenu[:60] + "…") if len(m.contenu) > 60 else m.contenu,
            "url": f"/messagerie/?open={m.id}"
        })

    return JsonResponse({"ok": True, "count": qs.count(), "items": items})


@login_required(login_url="Connection")
def ajax_unread_count(request):
    user = request.user
    ecole = getattr(user, "ecole", None)
    if not ecole:
        return JsonResponse({"ok": True, "count": 0})

    annee = get_annee_active(request)
    return JsonResponse({"ok": True, "count": unread_qs(user, ecole, annee).count()})


@require_POST
@login_required(login_url="Connection")
def delete_message(request, pk):
    msg = get_object_or_404(Message, pk=pk)

    # ✅ l'utilisateur ne supprime que ce qu'il possède
    if msg.receiver_id == request.user.id:
        msg.deleted_by_receiver = True
        msg.save(update_fields=["deleted_by_receiver"])
        return JsonResponse({"ok": True})

    if msg.sender_id == request.user.id:
        msg.deleted_by_sender = True
        msg.save(update_fields=["deleted_by_sender"])
        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False, "error": "Non autorisé"}, status=403)


from django.urls import reverse


@login_required(login_url="Connection")
def ajax_popup_unread(request):
    user = request.user
    ecole = getattr(user, "ecole", None)
    if not ecole:
        return JsonResponse({"ok": True, "count": 0, "items": []})

    annee = get_annee_active(request)

    qs = Message.objects.filter(
        receiver=user,
        ecole=ecole,
        annee_scolaire=annee,
        lu=False,
        deleted_by_receiver=False
    ).order_by("-date_envoi")

    items = []
    for m in qs[:3]:
        items.append({
            "id": m.id,
            "titre": m.sujet,
            "message": (m.contenu[:90] + "…") if len(m.contenu) > 90 else m.contenu,
            "date": localtime(m.date_envoi).strftime("%d/%m/%Y %H:%M"),
        })

    return JsonResponse({
        "ok": True,
        "count": qs.count(),
        "items": items,
        "url_inbox": reverse("messagerie_home")
    })
