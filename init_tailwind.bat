@echo off
echo ================================
echo  Nettoyage du projet Tailwind
echo ================================

:: Supprimer node_modules et package-lock.json s'ils existent
IF EXIST node_modules (
    rd /s /q node_modules
    echo - node_modules supprimé
)

IF EXIST package-lock.json (
    del package-lock.json
    echo - package-lock.json supprimé
)

:: Nettoyer le cache npm
echo Nettoyage du cache npm...
npm cache clean --force

:: Réinstaller Tailwind CSS
echo Installation de Tailwind CSS...
npm install -D tailwindcss

:: Initialiser Tailwind
echo Initialisation de tailwind.config.js...
npx tailwindcss init

echo ================================
echo ✅ Installation terminée !
echo ================================

pause

