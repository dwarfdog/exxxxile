from django.apps import AppConfig


class ExileConfig(AppConfig):
    name = 'exile'
    universe = 's03'
    registration = {
        'enabled': True,
        'until': None
    }
    allowedOrientations = [1,2,3]
    allowedRetry = True
    allowedHolidays = True
    allowMercenary = True
    hasAdmins = False # allow to send messages to administrators or not
    maintenance = False # enable/disable maintenance
    maintenance_msg = "Maintenance serveur ..." #"Mise à jour logiciel ..." #"Maintenance serveur" #"Migration de la base de donnée"
    supportMail = "support@exxxxile.ovh"
    senderMail = "exile.s03<noreply@exxxxile.ovh>"
    adExecuteNoRecords = 128

    # Players relationships constants (pas touche !)
    rUninhabited = -3
    rWar = -2
    rHostile = -1
    rFriend = 0
    rAlliance = 1
    rSelf = 2

    # Session constant names
    sUser = "sUser"
    sPlanet = "sPlanet"
    sLastLogin = "lastlogin"
    sPlanetList = "planetlist"
    sPlanetListCount = "planetlistcount"
    sPrivilege = "sPrivilege"
    sLogonUserID = "sLogonUserID"

    onlineusers_refreshtime = 60