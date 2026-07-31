# Configuration des logs
$logFile = "C:\ProgramData\InventaireDSI\agent_log.txt"
$logDir = Split-Path $logFile

if (-not (Test-Path $logDir)) {
    New-Item -Path $logDir -ItemType Directory -Force | Out-Null
}

try {
    # Infos matériel via WMI
    $infosPoste = Get-CimInstance -ClassName Win32_ComputerSystem
    $infosBios = Get-CimInstance -ClassName Win32_BIOS
    $infosOs = Get-CimInstance -ClassName Win32_OperatingSystem

    $numero_serie = $infosBios.SerialNumber
    $marque = $infosPoste.Manufacturer
    $modele = $infosPoste.Model
    $version_os = $infosOs.Caption
    $usager = $infosPoste.UserName

    # Infos Active Directory
    $computerName = $env:COMPUTERNAME
    $searcher = New-Object System.DirectoryServices.DirectorySearcher
    $searcher.Filter = "(&(objectCategory=computer)(cn=$computerName))"
    $result = $searcher.FindOne()

    # Extraction lieu depuis le distinguishedName
    $dn = $result.Properties["distinguishedname"][0]
    $parties = $dn.Split(",")
    $lieu = ($parties | Where-Object { $_ -match "^OU=" } | Select-Object -First 1) -replace "^OU=", ""

    # Extraction salle depuis la description (optionnel)
    $descriptionBrute = $result.Properties["description"]
    if ($descriptionBrute -ne $null -and $descriptionBrute.Count -gt 0) {
        $salle = $descriptionBrute[0]
    } else {
        $salle = ""
    }

    # Création de l'objet
    $Poste = @{
        numero_serie = $numero_serie
        marque = $marque
        modele = $modele
        version_os = $version_os
        usager = $usager
        lieu = $lieu
        salle = $salle
    }

    # Conversion en JSON
    $json = $Poste | ConvertTo-Json

    # Requête HTTP POST
    # Ne jamais committer la vraie clé ici : elle est renseignée uniquement sur les copies
    # déployées sur les postes (voir README, section clé API agent).
    $apiKey = "clé API"
    $response = Invoke-RestMethod -Uri "http://localhost:8000/script" -Method Post -Body $json -ContentType "application/json" -Headers @{"X-API-Key" = $apiKey}

    # Log succès
    Add-Content -Path $logFile -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Succès : $($response.statut) - numero_serie=$numero_serie"
}
catch {
    # Log échec
    Add-Content -Path $logFile -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - ERREUR : $_"
}
