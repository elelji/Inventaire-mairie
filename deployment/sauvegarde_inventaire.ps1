# Configuration
$source = "C:\Users\elouisy\stage\app\database.db"
$dossierSauvegarde = "C:\Sauvegardes_Inventaire"
$retentionJours = 30
$logFile = "$dossierSauvegarde\backup_log.txt"

# Créer le dossier de sauvegarde s'il n'existe pas
if (-not (Test-Path $dossierSauvegarde)) {
    New-Item -Path $dossierSauvegarde -ItemType Directory | Out-Null
}

# Construire le nom du fichier de destination avec la date du jour
$dateStr = Get-Date -Format "yyyyMMdd"
$destination = "$dossierSauvegarde\database_$dateStr.db"

try {
    # Copier le fichier
    Copy-Item -Path $source -Destination $destination -Force

    # Nettoyer les sauvegardes plus vieilles que la rétention définie
    $dateLimite = (Get-Date).AddDays(-$retentionJours)
    Get-ChildItem -Path $dossierSauvegarde -Filter "database_*.db" | Where-Object {
        $_.LastWriteTime -lt $dateLimite
    } | Remove-Item -Force

    # Logger le succès
    Add-Content -Path $logFile -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Sauvegarde réussie : $destination"
}
catch {
    # Logger l'échec
    Add-Content -Path $logFile -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - ERREUR : $_"
}