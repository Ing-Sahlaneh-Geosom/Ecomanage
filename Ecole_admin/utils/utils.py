from Ecole_admin.models import AnneeScolaire

def get_annee_active(request):
    try:
        annee_id = request.session.get('annee_scolaire_id')
        return AnneeScolaire.objects.get(id=annee_id)
    except:
        return AnneeScolaire.objects.filter(est_active=True).first()
    

# utils_accounts.py
import re

def slug_name(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s or "user"

def unique_username(UserModel, base: str) -> str:
    username = base
    i = 1
    while UserModel.objects.filter(username=username).exists():
        i += 1
        username = f"{base}{i}"
    return username

def build_username(nom: str, suffix: str) -> str:
    # suffix: "prof" / "parent"
    return f"{slug_name(nom)}@{suffix}"







