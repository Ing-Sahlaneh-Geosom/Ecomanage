import json

from django.http import HttpResponse , HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse , reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import ListView, UpdateView, DeleteView, CreateView, TemplateView , View
from django.contrib.auth  import login , logout , authenticate
from Ecole_admin.form import EleveForm, ConnectionForm, UserForm , ChangePasswordForm
from Ecole_admin.models import Eleve, User, AnneeScolaire, Classe
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from Ecole_admin.utils.mixins import ActiveYearMixin, EcoleAssignMixin, RoleRequiredMixin
from Ecole_admin.utils.utils import get_annee_active , build_username, unique_username
from django.contrib import messages


@login_required(login_url='Connection')
def changer_annee(request):
    if request.method == 'POST':
        annee_id = request.POST.get('annee_scolaire_id')
        if AnneeScolaire.objects.filter(id=annee_id).exists():
            request.session['annee_scolaire_id'] = int(annee_id)
    return redirect(request.META.get('HTTP_REFERER','/'))


class AjouterAnnee( LoginRequiredMixin , RoleRequiredMixin ,CreateView):
    model = AnneeScolaire
    fields = "__all__"
    template_name = 'AjouteAnneeScolaire.html'
    success_url = reverse_lazy('Acceuil')
    allowed_roles = ['admin',]
    login_url = 'Connection'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Title'] = 'Ajouter une annee'
        context['submit_text'] = 'Ajouter'
        return context

class EleveListView(LoginRequiredMixin , RoleRequiredMixin , ListView):
    model = Eleve
    template_name = 'eleve_list.html'
    context_object_name = 'eleves'
    paginate_by = 20
    allowed_roles = ["admin","proffesseur","eleve"]
    login_url = 'Connection'
    redirect_field_name = 'les_eleves'



    def get_queryset(self):
        queryset = Eleve.objects.filter(
            ecole=self.request.user.ecole,
            annee_scolaire = get_annee_active(self.request)
        )

        classe = self.request.GET.get("classe")
        nom = self.request.GET.get("nom")

        if classe and classe != "":
            queryset = queryset.filter(classe__id = classe)
        if nom and nom != "":
            queryset = queryset.filter(nom__icontains = nom)

        return queryset

    def get_context_data(self, **kwargs):
        context= super().get_context_data(**kwargs)
        annee = get_annee_active(self.request)
        queryset = self.get_queryset()
        context['nb_eleves'] = queryset.count()
        context['nb_femmes'] = queryset.filter(Sexe='F').count()
        context['nb_hommes'] = queryset.filter(Sexe='M').count()
        context['classes'] = self.request.user.ecole.classe_set.all()
        return context


class GenreStateView(TemplateView):
    template_name = 'eleve_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        annee = get_annee_active(self.request)

        nb_femmes = Eleve.objects.filter(Sexe='F', annee_scolaire=annee).count()
        nb_hommes = Eleve.objects.filter(Sexe='M', annee_scolaire=annee).count()

        context['labels'] = mark_safe(json.dumps(['Feminin','Musculin']))
        context['data'] = mark_safe(json.dumps([nb_femmes , nb_hommes]))
        return context

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.db.models import Sum
from django.db.models.functions import Coalesce
from decimal import Decimal

from .models import Eleve, FraisEleve, PaiementFraisEleve


@login_required(login_url='Connection')
def DetailsDesEleves(request, id):
    eleve = get_object_or_404(Eleve, id=id)

    # Frais (par type de paiement)
    frais_qs = (
        FraisEleve.objects
        .filter(eleve=eleve, ecole=eleve.ecole, annee_scolaire=eleve.annee_scolaire)
        .select_related("type_paiement")
    )

    # Paiements liés à ces frais
    paiements_qs = (
        PaiementFraisEleve.objects
        .filter(frais_eleve__eleve=eleve, ecole=eleve.ecole, annee_scolaire=eleve.annee_scolaire)
        .select_related("frais_eleve__type_paiement")
        .order_by("-date_paiement")
    )

    # Totaux globaux
    total_frais = frais_qs.aggregate(
        s=Coalesce(Sum("montant"), Decimal("0"))
    )["s"]

    total_paye = paiements_qs.aggregate(
        s=Coalesce(Sum("montant"), Decimal("0"))
    )["s"]

    total_reste = (total_frais or Decimal("0")) - (total_paye or Decimal("0"))

    # Résumé par type (tableau)
    # On calcule payé par type via paiements (paiement -> frais_eleve -> type_paiement)
    paye_par_type = {}
    for row in (
        paiements_qs.values("frais_eleve__type_paiement_id")
        .annotate(s=Coalesce(Sum("montant"), Decimal("0")))
    ):
        paye_par_type[row["frais_eleve__type_paiement_id"]] = row["s"]

    frais_par_type = []
    for f in frais_qs:
        paye = paye_par_type.get(f.type_paiement_id, Decimal("0"))
        reste = (f.montant or Decimal("0")) - (paye or Decimal("0"))
        frais_par_type.append({
            "type_label": str(f.type_paiement),  # nom dans la DB
            "montant": f.montant,
            "devise": f.devise,
            "paye": paye,
            "reste": reste,
            "frais_obj": f,
        })

    context = {
        "eleve": eleve,
        "frais_par_type": frais_par_type,
        "paiements": paiements_qs[:30],  # derniers paiements
        "total_frais": total_frais,
        "total_paye": total_paye,
        "total_reste": total_reste,
    }
    return render(request, "detaille.html", context)





class ElevesUpdateView( LoginRequiredMixin , RoleRequiredMixin , ActiveYearMixin, EcoleAssignMixin,UpdateView):
    model = Eleve
    template_name = 'Ajoute_eleve.html'
    form_class = EleveForm
    allowed_roles = ['admin',]
    login_url = 'Connection'

    def get_success_url(self):
        return reverse("les_eleves")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["Title"] = _("Modifier un eleve")
        context["Submit_text"] = _("Modifier")
        context['classes'] = Classe.objects.filter(ecole=self.request.user.ecole).all
        return context


class SupprimerEleve(LoginRequiredMixin, RoleRequiredMixin ,DeleteView):
    model = Eleve
    template_name = 'delete_eleve.html'
    success_url = reverse_lazy("les_eleves")
    allowed_roles = ['admin']
    login_url = 'Connection'




from django.contrib.auth.hashers import make_password

from django.db import transaction
from django.utils.translation import gettext_lazy as _



class AjouterDesEleves(LoginRequiredMixin, RoleRequiredMixin, ActiveYearMixin, EcoleAssignMixin, CreateView):
    model = Eleve
    template_name = 'Ajoute_eleve.html'
    form_class = EleveForm
    allowed_roles = ['admin']
    login_url = 'Connection'

    def get_queryset(self):
        annee = get_annee_active(self.request)
        return Eleve.objects.filter(annee_scolaire=annee)

    def form_valid(self, form):
        # ✅ remplir automatiquement
        form.instance.ecole = self.request.user.ecole
        form.instance.annee_scolaire = get_annee_active(self.request)

        # on prépare la création parent user après save eleve (car ecole/annee ok)
        parent_tel = (form.cleaned_data.get("telephone_parent") or "").strip()
        parent_nom = (form.cleaned_data.get("parent") or "").strip()
        parent_email = (form.cleaned_data.get("email_parent") or "").strip()

        response = super().form_valid(form)  # => self.object = eleve créé

        # ✅ créer / relier parent user
        created_parent_user = None
        if parent_tel and parent_nom:
            ecole = self.object.ecole

            # 1) réutiliser si même tel déjà enregistré comme parent dans cette école
            existing = User.objects.filter(ecole=ecole, role="parent", num_tel=parent_tel).first()
            if existing:
                self.object.parent_user = existing
                self.object.save(update_fields=["parent_user"])
            else:
                base = build_username(parent_nom, "parent")  # ali@parent
                username = unique_username(User, base)

                email = parent_email or f"{username}@parent.local"

                with transaction.atomic():
                    created_parent_user = User.objects.create(
                        username=username,
                        email=email,
                        nom_complet=parent_nom,
                        num_tel=parent_tel,
                        role="parent",
                        ecole=ecole,
                        password=make_password(parent_tel)  # mdp = tel
                    )
                    self.object.parent_user = created_parent_user
                    self.object.save(update_fields=["parent_user"])

        # ✅ messages (ID élève + identifiants parent si créé)
        msg = f"Élève ajouté avec succès ✅ | ID élève: {self.object.identifiant or self.object.id}"
        if created_parent_user:
            msg += f" | Parent login: {created_parent_user.username} | MDP: {parent_tel}"
        messages.success(self.request, msg)

        return response

    def get_success_url(self):
        return reverse("Ajouter")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["Title"] = _("Ajouter un eleve")
        context["Submit_text"] = _("Ajouter")
        context['classes'] = Classe.objects.filter(ecole=self.request.user.ecole)
        return context


# def AjouterDesEleves(request):
#     if request.method == 'POST':
#         form = EleveForm(request.POST , request.FILES)
#         if form.is_valid():
#             form.save()
#             return HttpResponseRedirect(reverse('Acceuil'))
#     else:
#         form = EleveForm()
#         return render(request,'Ajoute_eleve.html', {"form":form})
#     return render(request,'Ajoute_eleve.html', {"form":form})



class ListeDesUtilisateur(LoginRequiredMixin , RoleRequiredMixin ,ListView):
    model = User
    template_name = "Liste_utilisateur.html"
    context_object_name = "utilisateurs"
    paginate_by = 20
    allowed_roles = ["admin"]
    login_url = 'Connection'

    def get_queryset(self):
        queryset = User.objects.filter(ecole=self.request.user.ecole,)
        nom = self.request.GET.get("nom_complet")
        role = self.request.GET.get("role")
        sexe = self.request.GET.get("sexe")

        if nom and nom != "":
            queryset = queryset.filter(nom_complet__icontains = nom)
        if role and role != "":
            queryset = queryset.filter(role__icontains = role)
        if sexe and sexe != "":
            queryset = queryset.filter(sexe__icontains = sexe)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        return context





class UpdateUser( LoginRequiredMixin , RoleRequiredMixin ,UpdateView):
    model = User
    template_name = "Ajoute_user.html"
    form_class = UserForm
    success_url = reverse_lazy('Les_Utlisateur')
    allowed_roles = ['admin',]
    login_url = 'Connection'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Title'] = "Modifier User"
        context['Submit_text'] = "Modifier"
        return context

    


class CreateUtilisateur(CreateView):
    model = User
    template_name = 'Ajoute_user.html'
    form_class = UserForm
    success_url = reverse_lazy('Les_Utlisateur')
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Title'] = "Ajoute User"
        context['Submit_text'] = "Ajouter"
        return context



# @login_required(login_url='Connection')
# def AjouterDesUtilisateur(request):
#     if request.method == "POST":
#         form = UserForm(request.POST)
#         if form.is_valid():
#             utilisateur = form.save(commit=False)
#             utilisateur.password = make_password(form.cleaned_data['password'])
#             utilisateur.save()
#             return HttpResponseRedirect(reverse('Les_Utlisateur'))

#     else :
#         form = UserForm()
#         print("Le form ne plus valider")
#         return render(request,'Ajoute_user.html' , {'form' : form , 'erreur':"L'inscription a echoue"})

#     return render(request,'Ajoute_user.html' , {'form' : form})


# @login_required(login_url='Connection')
# def ModiffierDesUtilisateur(request, pk):
#     user = get_object_or_404(User, pk=pk)
#     if request.method == "POST":
#         form = UserForm(request.POST)
#         if form.is_valid():
#             utilisateur = form.save(commit=False)
#             utilisateur.password = make_password(form.cleaned_data['password'])
#             utilisateur.save()
#             return HttpResponseRedirect(reverse('Les_Utlisateur'))

#     else :
#         form = UserForm(instance=user)
#         return render(request,'modifier_les_user.html' , {'form' : form , 'erreur':"L'inscription a echoue"})

#     return render(request,'modifier_les_user.html' , {'form' : form})






from django.contrib.auth import authenticate, login


def connectionDesUtilisateur(request):
    form = ConnectionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        ident = form.cleaned_data["username"].strip()
        password = form.cleaned_data["password"]

        # si ident = tel, on convertit en username
        u = User.objects.filter(num_tel=ident).first()
        username = u.username if u else ident

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("Acceuil")

        messages.error(request, "Identifiant ou mot de passe incorrect.")

    return render(request, "connection.html", {"form": form})




def deconnection(request):
    logout(request)
    return HttpResponseRedirect(reverse('Connection'))


class SupprimerUser(LoginRequiredMixin , RoleRequiredMixin , DeleteView):
    model = User
    template_name = "DeleteUser.html"
    success_url = reverse_lazy('Les_Utlisateur')
    login_url = 'Connection'
    allowed_roles = ['admin',]


def Parametre(request):
    return render(request,'parametre.html')


def Annee(request):
    return render(request , 'parametre_annee.html')

def A_propos(request):
    return render(request , 'a_propos.html')



from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth import update_session_auth_hash



@login_required(login_url="Connection")
def changer_mot_de_passe(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.POST)

        if form.is_valid():
            old_password = form.cleaned_data["old_password"]
            new_password = form.cleaned_data["new_password1"]

            if not request.user.check_password(old_password):
                messages.error(request, "Ancien mot de passe incorrect.")
            else:
                request.user.set_password(new_password)
                request.user.save()

                # ✅ garder connecté
                update_session_auth_hash(request, request.user)

                messages.success(request, "Mot de passe modifié avec succès ✅")
                # ✅ rester sur la même page avec un form vide
                form = ChangePasswordForm()
    else:
        form = ChangePasswordForm()

    return render(request, "changer_mdp.html", {"form": form, "Title": "Changer le mot de passe"})

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import AnneeScolaire, Niveau, Classe, Eleve, User, Ecole


def _active_annee():
    try:
        return AnneeScolaire.get_active()
    except Exception:
        return AnneeScolaire.objects.order_by("-debut").first()


def _safe_get(obj, field_names, default=""):
    """Retourne le 1er champ existant/non vide parmi field_names."""
    for f in field_names:
        if hasattr(obj, f):
            v = getattr(obj, f, None)
            if v not in (None, ""):
                return v
    return default


@login_required
def certificat_scolarite(request):
    annee = _active_annee()
    ecole = getattr(request.user, "ecole", None)
    if ecole is None:
        ecole = Ecole.objects.first()

    # Niveaux
    niveaux = Niveau.objects.all()
    if hasattr(Niveau, "actif"):
        niveaux = niveaux.filter(actif=True)
    if ecole and hasattr(Niveau, "ecole_id"):
        niveaux = niveaux.filter(ecole=ecole)
    niveaux = niveaux.order_by("nom")

    # Chef d'établissement = admin + secretaire
    chefs = User.objects.filter(role__in=["admin", "secretaire"])
    if ecole and hasattr(User, "ecole_id"):
        chefs = chefs.filter(ecole=ecole)
    chefs = chefs.order_by("nom_complet", "username")

    return render(request, "certificat_scolarite.html", {
        "annee": annee,
        "ecole": ecole,
        "niveaux": niveaux,
        "chefs": chefs,
        "today": timezone.localdate(),
    })


@login_required
def ajax_classes_by_niveau(request):
    niveau_id = request.GET.get("niveau_id")
    if not niveau_id:
        return JsonResponse({"ok": True, "classes": []})

    ecole = getattr(request.user, "ecole", None)

    qs = Classe.objects.filter(niveau_id=niveau_id)
    if hasattr(Classe, "actif"):
        qs = qs.filter(actif=True)
    if ecole and hasattr(Classe, "ecole_id"):
        qs = qs.filter(ecole=ecole)

    data = [{"id": c.id, "label": c.nom} for c in qs.order_by("nom")]
    return JsonResponse({"ok": True, "classes": data})


@login_required
def ajax_eleves_by_classe(request):
    classe_id = request.GET.get("classe_id")
    if not classe_id:
        return JsonResponse({"ok": True, "eleves": []})

    ecole = getattr(request.user, "ecole", None)
    annee = _active_annee()

    qs = Eleve.objects.filter(classe_id=classe_id)
    if ecole and hasattr(Eleve, "ecole_id"):
        qs = qs.filter(ecole=ecole)
    if annee and hasattr(Eleve, "annee_scolaire_id"):
        qs = qs.filter(annee_scolaire=annee)
    if hasattr(Eleve, "actif"):
        qs = qs.filter(actif=True)

    data = [{"id": e.id, "label": e.nom} for e in qs.order_by("nom")]
    return JsonResponse({"ok": True, "eleves": data})


@login_required
def ajax_eleve_info(request):
    eleve_id = request.GET.get("eleve_id")
    if not eleve_id:
        return JsonResponse({"ok": False, "error": "eleve_id manquant"}, status=400)

    e = Eleve.objects.select_related("classe", "classe__niveau", "annee_scolaire", "ecole").get(id=eleve_id)

    # Matricule (chez toi c'est souvent identifiant)
    matricule = _safe_get(e, ["matricule", "identifiant"], default="")

    # Date naissance (tu avais date_naissancce)
    dn = _safe_get(e, ["date_naissance", "date_naissancce"], default=None)
    date_naissance = dn.strftime("%d-%m-%Y") if dn else ""

    # ✅ Lieu de naissance (maintenant présent chez toi)
    lieu_naissance = _safe_get(e, ["lieu_naissance", "lieu_de_naissance"], default="")

    classe = e.classe.nom if e.classe else ""
    niveau = e.classe.niveau.nom if (e.classe and e.classe.niveau) else ""

    data = {
        "nom": e.nom or "",
        "matricule": matricule,
        "date_naissance": date_naissance,
        "lieu_naissance": lieu_naissance,
        "classe": classe,
        "niveau": niveau,
        "annee": (e.annee_scolaire.nom if e.annee_scolaire else ""),
        "ecole": (e.ecole.nom if e.ecole else ""),
        "tel": (getattr(e.ecole, "telephone", "") if e.ecole else ""),
        "email": (getattr(e.ecole, "email", "") if e.ecole else ""),
        "type_etab": (getattr(e.ecole, "type_etablissement", "") if e.ecole else ""),
    }
    return JsonResponse({"ok": True, "eleve": data})
