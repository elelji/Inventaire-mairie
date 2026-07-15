#script powershell -- récupération de données

$infosPoste = Get-CimInstance -ClassName Win32_ComputerSystem
$infosBios = Get-CimInstance -ClassName Win32_BIOS
$infosOs = Get-CimInstance -ClassName Win32_OperatingSystem

$numero_serie = $infosBios.SerialNumber
$marque = $infosPoste.Manufacturer
$modele = $infosPoste.Model
$os = $infosOs.Caption
$user = $infosPoste.UserName

#création de l'objet
$Poste = @{
    numero_serie = $numero_serie;
    marque = $marque;
    modele = $modele;
    version_os = $os;
    usager = $user;
}

#Conversion 
$json = $Poste | ConvertTo-Json

#requête http poost
Invoke-RestMethod -Uri "http://localhost:8000/api/agent/rapport" -Method Post -Body $json -ContentType "application/json" -Headers @{"X-API-Key" = "__pG40gvRAmqN3D_MGfxoG-UFlShVSBYfLdGGOys9Z0
"}
