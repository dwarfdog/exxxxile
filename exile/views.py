import sys, string, random, time, math, datetime, re
from urllib.parse import urlencode
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.template import loader
from django.core.validators import validate_email, URLValidator
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.utils.html import strip_tags
from django.db import connection
from .apps import ExileConfig
from django.apps import apps

from exile.models import *

config = apps.get_app_config('exile')

def retrieveAllianceChat(id):
    if not cache.get('alliances_chat') or not id in cache.get('alliances_chat').keys():
        with connection.cursor() as cursor:
            cursor.execute('SELECT id,chatid FROM alliances ORDER BY id')
            res = cursor.fetchall()
            gs = {}
            for re in res:
                gs[re[0]] = re[1]
            if res:
                cache.add('alliances_chat', gs.copy(), None)
    try:
        return cache.get('alliances_chat')[id]
    except(KeyError,Exception):
        return 0

def retrieveGalaxyCache():
    cache.add('galaxies_last_retrieve', time.time(), None)
    if not cache.get('galaxies'):
        # retrieve general Ships info
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM nav_galaxies ORDER BY id')
            res = cursor.fetchall()
            gs = {}
            for re in res:
                gs[re[0]] = re
            if res:
                cache.add('galaxies', gs, None)
                cache.add('galaxies_retrieved', time.time(), None)
            else:
                cache.add('galaxies', {}, 300)
    return cache.get('galaxies')

def retrieveBuildingsCache():
    cache.add('db_buildings_last_retrieve', time.time(), None)
    if not cache.get('db_buildings'):
        # retrieve general buildings info
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, storage_workers, energy_production, storage_ore, storage_hydrocarbon, workers, storage_scientists, storage_soldiers, label, description, energy_consumption, workers*maintenance_factor/100, upkeep FROM db_buildings')
            res = cursor.fetchall()
            if res:
                cache.add('db_buildings', res.copy(), None)
                cache.add('db_buildings_retrieved', time.time(), None)
            else:
                cache.add('db_buildings', {}, 300)
    return cache.get('db_buildings')

def retrieveBuildingsReqCache():
    cache.add('db_buildings_req_last_retrieve', time.time(), None)
    if not cache.get('db_buildings_req'):
        # retrieve buildings requirements
        # planet elements can't restrict the destruction of a building that made their construction possible
        with connection.cursor() as cursor:
            cursor.execute('SELECT buildingid, required_buildingid ' +
                ' FROM db_buildings_req_building ' +
                '   INNER JOIN db_buildings ON (db_buildings.id=db_buildings_req_building.buildingid) ' +
                ' WHERE db_buildings.destroyable')
            res = cursor.fetchall()
            if res:
                cache.add('db_buildings_req', res.copy(), None)
                cache.add('db_buildings_req_retrieved', time.time(), None)
            else:
                cache.add('db_buildings_req', {}, 300)
    return cache.get('db_buildings_req')

def retrieveBuildingsReqRCache():
    cache.add('db_buildings_req_r_last_retrieve', time.time(), None)
    if not cache.get('db_buildings_req_r'):
        # retrieve buildings requirements
        # planet elements can't restrict the destruction of a building that made their construction possible
        with connection.cursor() as cursor:
            cursor.execute('SELECT buildingid, required_researchid, required_researchlevel FROM db_buildings_req_research')
            res = cursor.fetchall()
            if res:
                cache.add('db_buildings_req_r', res.copy(), None)
                cache.add('db_buildings_req_r_retrieved', time.time(), None)
            else:
                cache.add('db_buildings_req_r', {}, 300)
    return cache.get('db_buildings_req_r')

def retrieveShipsCache():
    cache.add('db_ships_last_retrieve', time.time(), None)
    if not cache.get('db_ships'):
        # retrieve general Ships info
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, label, description FROM db_Ships ORDER BY category, id')
            res = cursor.fetchall()
            if res:
                cache.add('db_ships', res.copy(), None)
                cache.add('db_ships_retrieved', time.time(), None)
            else:
                cache.add('db_ships', {}, 300)
    return cache.get('db_ships')

def retrieveShipsReqCache():
    cache.add('db_ships_req_last_retrieve', time.time(), None)
    if not cache.get('db_ships_req'):
        # retrieve buildings requirements for ships
        with connection.cursor() as cursor:
            cursor.execute('SELECT shipid, required_buildingid FROM db_ships_req_building')
            res = cursor.fetchall()
            if res:
                cache.add('db_ships_req', res.copy(), None)
                cache.add('db_ships_req_retrieved', time.time(), None)
            else:
                cache.add('db_ships_req', {}, 300)
    return cache.get('db_ships_req')

def retrieveShipsReqRCache():
    cache.add('db_ships_req_r_last_retrieve', time.time(), None)
    if not cache.get('db_ships_req_r'):
        # retrieve buildings requirements for ships
        with connection.cursor() as cursor:
            cursor.execute('SELECT shipid, required_researchid, required_researchlevel FROM db_ships_req_research')
            res = cursor.fetchall()
            if res:
                cache.add('db_ships_req_r', res.copy(), None)
                cache.add('db_ships_req_r_retrieved', time.time(), None)
            else:
                cache.add('db_ships_req_r', {}, 300)
    return cache.get('db_ships_req_r')

def retrieveResearchCache():
    cache.add('db_research_last_retrieve', time.time(), None)
    if not cache.get('db_research'):
        # retrieve Research info
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, label, description FROM db_Research')
            res = cursor.fetchall()
            if res:
                cache.add('db_research', res.copy(), None)
                cache.add('db_research_retrieved', time.time(), None)
            else:
                cache.add('db_research', {}, 300)
    return cache.get('db_research')

def planetimg(id,floor):
    planetimg = 1 + (floor + id) % 21
    if planetimg < 10:
        planetimg = "0" + str(planetimg)
    return str(planetimg)

def checkVWPlanetListCache(request, force=False):
    gcontext = request.session.get('gcontext',{})
    if force or not request.session.get("vwplanetlist", {}):
        # retrieve Research info
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, name, galaxy, sector, planet, commanderid, floor, floor_occupied, space, space_occupied, ceiling(ore/1000), ore*100/ore_capacity, ceiling(hydrocarbon/1000), hydrocarbon*100/hydrocarbon_capacity FROM vw_planets WHERE ownerid=%s ORDER BY id', [gcontext['exile_user'].id])
            res = cursor.fetchall()
            if res:
                tmp = []
                for re in res:
                    re = re + (planetimg(re[0],re[6]),)
                    tmp.append(re)
                request.session["vwplanetlist"] = tmp
            else:
                request.session["vwplanetlist"] = {}
    return request.session.get("vwplanetlist")

def checkPlanetListCache(request, force=False):
    gcontext = request.session.get('gcontext',{})
    if force or not request.session.get("planetlist", {}):
        # retrieve Research info
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, name, galaxy, sector, planet, commanderid, floor, floor_occupied, space, space_occupied, ceiling(ore/1000), ore*100/ore_capacity, ceiling(hydrocarbon/1000), hydrocarbon*100/hydrocarbon_capacity FROM nav_planet WHERE planet_floor > 0 AND planet_space > 0 AND ownerid=%s ORDER BY id', [gcontext['exile_user'].id])
            res = cursor.fetchall()
            if res:
                tmp = []
                for re in res:
                    re = re + (planetimg(re[0],re[6]),)
                    tmp.append(re)
                request.session["planetlist"] = tmp
            else:
                request.session["planetlist"] = {}
    return request.session.get("planetlist")

def getAllianceTag(allianceid):
    if not allianceid:
        return ''
    if not cache.get("AllianceTag_" + str(allianceid)):
        with connection.cursor() as cursor:
            cursor.execute('SELECT tag FROM alliances WHERE id=%s', [allianceid])
            res = cursor.fetchone()
            if res:
                cache.set("AllianceTag_" + str(allianceid), res[0], None)
            else:
                cache.set("AllianceTag_" + str(allianceid), '', None)
    return cache.get("AllianceTag_" + str(allianceid))

def getBuildingLabel(buildingid):
    for building in retrieveBuildingsCache():
        if buildingid == building[0]:
            return building[8]
    return ''

def getBuildingDescription(buildingid):
    for building in retrieveBuildingsCache():
        if buildingid == building[0]:
            return building[9]
    return ''

def getShipLabel(ShipId):
    for ship in retrieveShipsCache():
        if ShipId == ship[0]:
            return ship[1]
    return ''

def getShipDescription(ShipId):
    for ship in retrieveShipsCache():
        if ShipId == ship[0]:
            return ship[2]
    return ''

def getResearchLabel(ResearchId):
    for research in retrieveResearchCache():
        if ResearchId == research[0]:
            return research[1]
    return ''

def getResearchDescription(ResearchId):
    for research in retrieveResearchCache():
        if ResearchId == research[0]:
            return research[2]
    return ''

def getPlanetName(request,relation, radar_strength, ownerName, planetName):
    global config
    gcontext = request.session.get('gcontext',{})
    if relation == config.rSelf:
        getPlanetName = planetName
    elif relation == config.rAlliance:
        if gcontext['exile_user'].display_alliance_planet_name:
            getPlanetName = planetName
        else:
            getPlanetName = ownerName
    elif relation == config.rFriend:
        getPlanetName = ownerName
    else:
        if radar_strength > 0 and ownerName:
            getPlanetName = ownerName
        else:
            getPlanetName = ''
    return getPlanetName

def getpercent(current, max, slice):
    if current >= max or max == 0:
        return 100
    else:
        return slice*int(100 * current / max / slice)

def isValidName(myName,limit=12):
    if len(myName) < 2 or len(myName) > limit:
        return False
    pattern = re.compile("^[a-zA-Z0-9-_]+[a-zA-Z0-9-_ ]+[a-zA-Z0-9-_]+$")
    return pattern.match(myName)

"""
function SetCurrentPlanet(planetid)
    dim oRs, galaxyid, sectorid
    SetCurrentPlanet = False
    '
    ' Check if a parameter is given and if different than the current planet
    ' In that case, try to set it as the new planet : check that this planet belongs to the player
    '
    if (planetid != "") and (planetid != CurrentPlanet):
        ' check that the new planet belongs to the player
        set oRs = oConn.Execute("SELECT galaxy, sector FROM nav_planet WHERE planet_floor > 0 AND planet_space > 0 AND id=" & planetid & " and ownerid=" & UserID)
        if not oRs.EOF:
            CurrentPlanet = planetid
            CurrentGalaxyId = re[0]
            CurrentSectorId = re[1]
            Session.Contents(sPlanet) = planetid
            oRs.Close
            set oRs = Nothing
            ' save the last planetid
            if not IsImpersonating:
                on error resume next
                oConn.Execute "UPDATE users SET lastplanetid=" & planetid & " WHERE id=" & UserId, , adExecuteNoRecords
                on error goto 0
            end if
            SetCurrentPlanet = True
            exit function
        end if
        InvalidatePlanetList()
    end if
    ' 
    ' retrieve current planet from session
    '
    CurrentPlanet = Session(sPlanet)
    if CurrentPlanet != "":
        ' check if the planet still belongs to the player
        set oRs = oConn.Execute("SELECT galaxy, sector FROM nav_planet WHERE planet_floor > 0 AND planet_space > 0 AND id=" & CurrentPlanet & " AND ownerid=" & UserID)
        if not oRs.EOF:
            ' the planet still belongs to the player, exit
            CurrentGalaxyId = re[0]
            CurrentSectorId = re[1]
            SetCurrentPlanet = True
            oRs.Close
            set oRs = Nothing
            exit function
        end if
        InvalidatePlanetList()
    end if
    ' there is no active planet, select the first planet available
    set oRs = oConn.Execute("SELECT id, galaxy, sector FROM nav_planet WHERE planet_floor > 0 AND planet_space > 0 AND ownerid=" & UserID & " LIMIT 1")
    ' if player owns no planets: the game is over
    if oRs.EOF:
        if IsPlayerAccount():
            RedirectTo "game-over.asp"
        else
            CurrentPlanet = 0
            CurrentGalaxyId = 0
            CurrentSectorId = 0
            SetCurrentPlanet = True
            exit function
        end if
    end if
    ' assign planet id
    CurrentPlanet = re[0]
    CurrentGalaxyId = re[1]
    CurrentSectorId = re[2]
    Session.Contents(sPlanet) = CurrentPlanet
    oRs.Close
    set oRs = Nothing
    ' save the last planetid
    if not IsImpersonating:
        on error resume next
        oConn.Execute "UPDATE users SET lastplanetid=" & CurrentPlanet & " WHERE id=" & UserId, , adExecuteNoRecords
        on error goto 0
    end if
    ' a player may wish to destroy a building on a planet that belonged to him
    ' if the planet doesn't belong to him anymore, the action may be performed on another planet
    ' so we redirect the user to the overview to prevent executing an order on another planet
    Response.Redirect "/game/overview.asp"
    Response.End
    SetCurrentPlanet = True
end function
"""
def hasRight(request,right):
    gcontext = request.session.get('gcontext',{})
    if not gcontext['hasRight']:
        return True
    else:
        return gcontext['hasRight'][0]["leader"] or gcontext['hasRight'][0][right]

def dictfetchall(cursor):
    # Return all rows from a cursor as a dict
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

def IsPlayerAccount(request):
    return request.session.get('sPrivilege', -100) > -50 and request.session.get('sPrivilege') < 50

def log_notice(request, title, details, level):
    gcontext = request.session.get('gcontext',{})
    with connection.cursor() as cursor:
        cursor.execute('INSERT INTO log_notices (username, title, details, url, level) VALUES( %s, %s, %s, %s ,%s)', [gcontext['exile_user'].login, title, details, request.path , level])

def logout(request):
    request.session.flush()
    return HttpResponseRedirect(reverse('nexus:logout'))

def menu(request):
    gcontext = request.session.get('gcontext',{})
    t = loader.get_template('exile/menu.html')
    return t.render(gcontext, request)

def fleetheader(request):
    gcontext = request.session.get('gcontext',{})
    if gcontext['CurrentFleet'] == 0:
        return ''
    with connection.cursor() as cursor:
        cursor.execute('SELECT fleetid, fleets_ships.shipid, quantity' +
            ' FROM fleets' +
            ' INNER JOIN fleets_ships ON (fleets.id=fleets_ships.fleetid)' +
            ' WHERE ownerid=%s' +
            ' ORDER BY fleetid, fleets_ships.shipid', [gcontext['exile_user'].id])
        res = cursor.fetchall()
        if not res:
            ShipListCount = -1
        else:
            ShipListArray = res
            ShipListCount = len(res)
        cursor.execute('SELECT id, name, attackonsight, engaged, size, signature, speed, remaining_time, commanderid, commandername,' + # 0 1 2 3 4 5 6 7 8 9
            ' planetid, planet_name, planet_galaxy, planet_sector, planet_planet, planet_ownerid, planet_owner_name, planet_owner_relation,' + # 10 11 12 13 14 15 16 17
            ' destplanetid, destplanet_name, destplanet_galaxy, destplanet_sector, destplanet_planet, destplanet_ownerid, destplanet_owner_name, destplanet_owner_relation,' + # 18 19 20 21 22 23 24 25
            ' cargo_capacity, cargo_ore, cargo_hydrocarbon, cargo_scientists, cargo_soldiers, cargo_workers,' + # 26 27 28 29 30 31
            ' recycler_output, orbit_ore > 0 OR orbit_hydrocarbon > 0, action,' + # 32 33 34
            '( SELECT int4(COALESCE(max(nav_planet.radar_strength), 0)) FROM nav_planet WHERE nav_planet.galaxy = f.planet_galaxy AND nav_planet.sector = f.planet_sector AND nav_planet.ownerid IS NOT NULL AND EXISTS ( SELECT 1 FROM vw_friends_radars WHERE vw_friends_radars.friend = nav_planet.ownerid AND vw_friends_radars.userid = %(UserId)s)) AS from_radarstrength, ' + # 35
            '( SELECT int4(COALESCE(max(nav_planet.radar_strength), 0)) FROM nav_planet WHERE nav_planet.galaxy = f.destplanet_galaxy AND nav_planet.sector = f.destplanet_sector AND nav_planet.ownerid IS NOT NULL AND EXISTS ( SELECT 1 FROM vw_friends_radars WHERE vw_friends_radars.friend = nav_planet.ownerid AND vw_friends_radars.userid = %(UserId)s)) AS to_radarstrength,' + # 36
            ' categoryid' + # 37
            ' FROM vw_fleets as f WHERE ownerid = %(UserId)s ORDER BY name ASC', {'UserId': gcontext['exile_user'].id})
        res = cursor.fetchall()
        tpl_header = {'fleetlist':{}}
        if not res:
            pass
        else:
            for re in res:
                fleet = {}
                fleet['ship'] = {}
                fleet['resource'] = {1:{},2:{},3:{},4:{},5:{}}
                fleet['id'] = re[0]
                fleet['name'] = re[1]
                fleet['category'] = re[37]
                fleet['size'] = re[4]
                fleet['signature'] = re[5]
                fleet['speed'] = re[6]
                fleet['remaining_time'] = re[7]
                fleet['cargo_load'] = re[27]+re[28]+re[29]+re[30]+re[31]
                fleet['cargo_capacity'] = re[26]
                fleet['cargo_ore'] = re[27]
                fleet['cargo_hydrocarbon'] = re[28]
                fleet['cargo_scientists'] = re[29]
                fleet['cargo_soldiers'] = re[30]
                fleet['cargo_workers'] = re[31]
                fleet['commanderid'] = re[8]
                fleet['commandername'] = re[9]
                fleet['action'] = abs(re[34])
                if re[3]:
                    fleet['action'] = "x"
                if re[2]:
                    fleet['stance'] = 1
                else:
                    fleet['stance'] = 0
                if re[7]:
                    fleet['time'] = re[7]
                else:
                    fleet['time'] = 0
                # Assign fleet current planet
                fleet['planetid'] = 0
                fleet['g'] = 0
                fleet['s'] = 0
                fleet['p'] = 0
                fleet['relation'] = 0
                fleet['planetname'] = ""
                if re[10]:
                    fleet['planetid'] = re[10]
                    fleet['g'] = re[12]
                    fleet['s'] = re[13]
                    fleet['p'] = re[14]
                    fleet['relation'] = re[17]
                    fleet['planetname'] = getPlanetName(request,re[17], re[35], re[16], re[11])
                    if not fleet['planetname']:
                        fleet['planetname'] = re[16]
                # Assign fleet destination planet
                fleet['t_planetid'] = 0
                fleet['t_g'] = 0
                fleet['t_s'] = 0
                fleet['t_p'] = 0
                fleet['t_relation'] = 0
                fleet['t_planetname'] = ""
                if re[18]:
                    fleet['t_planetid'] = re[18]
                    fleet['t_g'] = re[20]
                    fleet['t_s'] = re[21]
                    fleet['t_p'] = re[22]
                    fleet['t_relation'] = re[25]
                    fleet['t_planetname'] = getPlanetName(request,re[25], re[36], re[24], re[19])
                for i in range(0, ShipListCount):
                    if ShipListArray[i][0] == re[0]:
                        fleet['ship'][i] = {
                            'ship_label':getShipLabel(ShipListArray[i][1]),
                            'ship_quantity': ShipListArray[i][2],
                        }
                fleet['resource'][1]['res_id'] = 1
                fleet['resource'][1]['res_quantity'] = re[28]
                fleet['resource'][2]['res_id'] = 2
                fleet['resource'][2]['res_quantity'] = re[29]
                fleet['resource'][3]['res_id'] = 3
                fleet['resource'][3]['res_quantity'] = re[30]
                fleet['resource'][4]['res_id'] = 4
                fleet['resource'][4]['res_quantity'] = re[31]
                fleet['resource'][5]['res_id'] = 5
                fleet['resource'][5]['res_quantity'] = re[32]
                if gcontext['CurrentFleet'] == re[0]:
                    fleet['selected'] = True
                    tpl_header['fleet'] = fleet.copy()
                tpl_header['fleetlist'][re[0]] = fleet.copy()
    tmp = request.GET.copy()
    tmp.pop('fleet', None)
    tmp.pop('planet', None)
    url_extra_params = urlencode(tmp, doseq=True)
    if url_extra_params != "":
        tpl_header["urlf"] = "?" + url_extra_params + "&fleet="
    else:
        tpl_header["urlf"] = "?fleet="
    t = loader.get_template('exile/fleetheader.html')
    gcontext['tpl_fheader'] = tpl_header.copy()
    return t.render(tpl_header, request)

def header(request):
    gcontext = request.session.get('gcontext',{})
    if gcontext['CurrentPlanet'] == 0:
        return
    tpl_header = {
        "money": gcontext['exile_user'].credits,
        "pp": gcontext['exile_user'].prestige_points
    }
    # assign current planet ore, hydrocarbon, workers and energy
    with connection.cursor() as cursor:
        cursor.execute('SELECT ore, ore_production, ore_capacity, ' +
            ' hydrocarbon, hydrocarbon_production, hydrocarbon_capacity, ' +
            ' workers, workers_busy, workers_capacity, ' +
            ' energy_consumption, energy_production, ' +
            ' floor_occupied, floor, ' +
            ' space_occupied, space, workers_for_maintenance, ' +
            ' mod_production_ore, mod_production_hydrocarbon, energy, energy_capacity, soldiers, soldiers_capacity, scientists, scientists_capacity ' +
            ' FROM vw_planets WHERE id=%s', [gcontext['CurrentPlanet']])
        re = cursor.fetchone()
        tpl_header["ore"] = re[0]
        tpl_header["ore_production"] = re[1]
        tpl_header["ore_capacity"] = re[2]
        # compute ore level : ore / capacity
        ore_level = getpercent(re[0], re[2], 10)
        if ore_level >= 90:
            tpl_header["high_ore"] = True
        elif ore_level >= 70:
            tpl_header["medium_ore"] = True
        else:
            tpl_header["normal_ore"] = True
        tpl_header["hydrocarbon"] = re[3]
        tpl_header["hydrocarbon_production"] = re[4]
        tpl_header["hydrocarbon_capacity"] = re[5]
        hydrocarbon_level = getpercent(re[3], re[5], 10)
        if hydrocarbon_level >= 90:
            tpl_header["high_hydrocarbon"] = True
        elif hydrocarbon_level >= 70:
            tpl_header["medium_hydrocarbon"] = True
        else:
            tpl_header["normal_hydrocarbon"] = True
        tpl_header["workers"] = re[6]
        tpl_header["workers_capacity"] = re[8]
        tpl_header["workers_idle"] = re[6] - re[7]
        if re[6] < re[15]:
            tpl_header["workers_low"] = True
        tpl_header["soldiers"] = re[20]
        tpl_header["soldiers_capacity"] = re[21]
        if re[20]*250 < re[6]+re[22]:
            tpl_header["soldiers_low"] = True
        tpl_header["scientists"] = re[22]
        tpl_header["scientists_capacity"] = re[23]
        tpl_header["energy_consumption"] = re[9]
        tpl_header["energy_totalproduction"] = re[10]
        tpl_header["energy_production"] = re[10]-re[9]
        tpl_header["energy"] = re[18]
        tpl_header["energy_capacity"] = re[19]
        if re[9] > re[10]:
            tpl_header["energy_low"] = True
        if re[9] > re[10]:
            tpl_header["energy_production_minus"] = True
        else:
            tpl_header["energy_production_normal"] = True
        tpl_header["floor_occupied"] = re[11]
        tpl_header["floor"] = re[12]
        tpl_header["space_occupied"] = re[13]
        tpl_header["space"] = re[14]
        # ore/hydro production colors
        if re[16] >= 0 and re[6] >= re[15]:
            tpl_header["normal_ore_production"] = True
        else:
            tpl_header["medium_ore_production"] = True
        if re[17] >= 0 and re[6] >= re[15]:
            tpl_header["normal_hydrocarbon_production"] = True
        else:
            tpl_header["medium_hydrocarbon_production"] = True
        # Fill the planet list
        tmp = request.GET.copy()
        tmp.pop('planet', None)
        tmp.pop('fleet', None)
        url_extra_params = urlencode(tmp, doseq=True)
        if url_extra_params != "":
            tpl_header["url"] = "?" + url_extra_params + "&planet="
        else:
            tpl_header["url"] = "?planet="
        # cache the list of planets as they are not supposed to change unless a colonization occurs
        # in case of colonization, let the colonize script reset the session value
        planetListArray = checkPlanetListCache(request) #request.session.get('sPlanetList', {})
        planetListCount = len(planetListArray)
        #if planetListCount == 0:
        #    # retrieve planet list
        #    cursor.execute('SELECT id, name, galaxy, sector, planet FROM nav_planet ' +
        #            ' WHERE planet_floor > 0 AND planet_space > 0 AND ownerid=%s ' +
        #            ' ORDER BY id', [gcontext['exile_user'].id])
        #    res = cursor.fetchall()
        #    planetListArray = res.copy()
        #    planetListCount = len(planetListArray)
        #    request.session['sPlanetList'] = planetListArray.copy()
        #    request.session['sPlanetListCount'] = planetListCount
        tpl_header["planets"] = {}
        for planet in planetListArray:
            pla = {
                "id": planet[0],
                "name": planet[1],
                "g": planet[2],
                "s": planet[3],
                "p": planet[4],
            }
            if planet[0] == gcontext['CurrentPlanet']:
                pla['selected'] = True
            tpl_header["planets"][planet[0]] = pla.copy()
        cursor.execute('SELECT buildingid ' +
                ' FROM planet_buildings INNER JOIN db_buildings ON (db_buildings.id=buildingid AND db_buildings.is_planet_element) ' +
                ' WHERE planetid=%s ' +
                ' ORDER BY upper(db_buildings.label)', [gcontext['CurrentPlanet']])
        res = cursor.fetchall()
        i = 0
        tpl_header['special'] = {
            'special1': {},
            'special2': {},
            'special3': {},
        }
        for re in res:
            if i % 3 == 0:
                tpl_header['special']['special1'][i] = {'name':getBuildingLabel(re[0])}
            elif i % 3 == 1:
                tpl_header['special']['special2'][i] = {'name':getBuildingLabel(re[0])}
            else:
                tpl_header['special']['special3'][i] = {'name':getBuildingLabel(re[0])}
            i += 1
    t = loader.get_template('exile/header.html')
    gcontext['tpl_header'] = tpl_header.copy()
    return t.render(tpl_header, request)

def FillHeaderCredits(request):
    gcontext = request.session.get('gcontext',{})
    return
    #no more need with topbar
    #with connection.cursor() as cursor:
    #    cursor.execute('SELECT credits FROM users WHERE id=%s', [gcontext['exile_user'].id])
    #    res = cursor.fetchone()
    #    if not res:
    #        raise Exception('can\'t get credits')
    #    gcontext['credits'] = res[0]
    #    t = loader.get_template('exile/header-credits.html')
    #    info = t.render(gcontext, request)
    #    gcontext['contextinfo'] = info

def construct(function):
    global config

    def decorator(request, *args, **kwargs):
        global config
        if settings.MAINTENANCE:
            return HttpResponseRedirect(reverse('exile:maintenance'))
        try:
            user = NexusUsers.objects.get(pk=request.session.get('user_id', 0))
        except (KeyError, NexusUsers.DoesNotExist):
            return HttpResponseRedirect(reverse('exile:logout'))
        gcontext = {
            'test': settings.TEST,
            #'config': config,
            'universe': config.universe,
            'logged': request.session.get('logged', False),
            'user': user,
            'timers_enabled': 'true',
            'CurrentPlanet': request.session.get('CurrentPlanet', 0),
            'CurrentGalaxy': request.session.get('CurrentGalaxy', 0),
            'CurrentSector': request.session.get('CurrentSector', 0),
            'CurrentFleet': request.session.get('CurrentFleet', 0),
            'IsImpersonating':False,
            'skin':'s_transparent',
        }
        request.session['gcontext'] = gcontext
        return function(request, *args, **kwargs)

    return decorator

def admin(function):
    global config

    def decorator(request, *args, **kwargs):
        gcontext = request.session.get('gcontext',{})
        if gcontext['exile_user'].privilege < 100:
            return HttpResponseRedirect(reverse('exile:overview'))
        return function(request, *args, **kwargs)

    return decorator

def logged(function):
    global config

    def decorator(request, *args, **kwargs):
        gcontext = request.session.get('gcontext',{})
        if not request.session.get('sUser', 0) or not request.session.get('logged', False):
            return HttpResponseRedirect(reverse('exile:connect'))
        try:
            user = Users.objects.get(pk=request.session.get('sUser', 0))
        except (KeyError, Users.DoesNotExist):
            return HttpResponseRedirect(reverse('exile:connect'))
        if not user:
            return HttpResponseRedirect(reverse('exile:connect'))
        gcontext['exile_user'] = user
        log_notice(request, 'login_check', 'exile_user='+str(user.id)+' nexus_user='+str(request.session.get('user_id', 0)), 1)
        gcontext['dev'] = user.privilege >= 100
        if user.skin:
            gcontext['skin'] = user.skin
        if not user.timers_enabled:
            gcontext['timers_enabled'] = 'false'
        if not user.lastactivity:
            with connection.cursor() as cursor:
                cursor.execute('UPDATE users SET lastactivity=now() WHERE id=%s', [user.id])
        gcontext['planet_list'] = checkVWPlanetListCache(request, True)
        gcontext['can_join_alliance'] = not gcontext['exile_user'].leave_alliance_datetime and (not gcontext['exile_user'].alliance_left or gcontext['exile_user'].alliance_left < time.time())
        planet = request.GET.get('planet',0)
        forced = False
        if planet and planet.isdigit():
            fplanet = NavPlanet.objects.get(pk=planet)
            if fplanet.ownerid_id == user.id:
                forced = True
                gcontext['CurrentPlanet'] = fplanet.id
                gcontext['CurrentGalaxy'] = fplanet.galaxy_id
                gcontext['CurrentSector'] = fplanet.sector
                request.session['CurrentPlanet'] = fplanet.id
                request.session['CurrentGalaxy'] = fplanet.galaxy_id
                request.session['CurrentSector'] = fplanet.sector
        if gcontext['CurrentPlanet'] == 0:
            fplanet = user.navplanet_set.first()
            if fplanet:
                gcontext['CurrentPlanet'] = fplanet.id
                gcontext['CurrentGalaxy'] = fplanet.galaxy_id
                gcontext['CurrentSector'] = fplanet.sector
                request.session['CurrentPlanet'] = fplanet.id
                request.session['CurrentGalaxy'] = fplanet.galaxy_id
                request.session['CurrentSector'] = fplanet.sector
        elif not forced:
            fplanet = NavPlanet.objects.get(pk=gcontext['CurrentPlanet'])
            if fplanet and fplanet.ownerid_id == user.id:
                gcontext['CurrentPlanet'] = fplanet.id
                gcontext['CurrentGalaxy'] = fplanet.galaxy_id
                gcontext['CurrentSector'] = fplanet.sector
                request.session['CurrentPlanet'] = fplanet.id
                request.session['CurrentGalaxy'] = fplanet.galaxy_id
                request.session['CurrentSector'] = fplanet.sector
            else:
                fplanet = user.navplanet_set.first()
                if fplanet:
                    gcontext['CurrentPlanet'] = fplanet.id
                    gcontext['CurrentGalaxy'] = fplanet.galaxy_id
                    gcontext['CurrentSector'] = fplanet.sector
                    request.session['CurrentPlanet'] = fplanet.id
                    request.session['CurrentGalaxy'] = fplanet.galaxy_id
                    request.session['CurrentSector'] = fplanet.sector
        if fplanet and fplanet.ownerid_id == user.id:
            gcontext['planetid'] = gcontext['CurrentPlanet']
            gcontext['g'] = fplanet.galaxy.id
            gcontext['s'] = fplanet.sector
            gcontext['p'] = fplanet.planet
        fleet = request.GET.get('fleet',0)
        forced = False
        if fleet and fleet.isdigit():
            fleet = Fleets.objects.get(pk=fleet)
            if fleet.ownerid_id == user.id:
                forced = True
                gcontext['CurrentFleet'] = fleet.id
                request.session['CurrentFleet'] = fleet.id
        if gcontext['CurrentFleet'] == 0:
            fleet = user.fleets_set.first()
            if fleet:
                gcontext['CurrentFleet'] = fleet.id
                request.session['CurrentFleet'] = fleet.id
        if IsPlayerAccount(request):
            # Redirect to locked page
            if gcontext['exile_user'].privilege == -1:
                return HttpResponseRedirect(reverse('exile:locked'))
            # Redirect to holidays page
            if gcontext['exile_user'].privilege == -2:
                return HttpResponseRedirect(reverse('exile:holidays'))
            # Redirect to wait page
            if gcontext['exile_user'].privilege == -3:
                return HttpResponseRedirect(reverse('exile:wait'))
            # Redirect to game-over page
            if gcontext['exile_user'].credits_bankruptcy <= 0:
                return HttpResponseRedirect(reverse('exile:gameover'))
        gcontext['hasRight'] = None
        if gcontext['exile_user'].alliance_id:
            with connection.cursor() as cursor:
                cursor.execute('SELECT label, leader, can_invite_player, can_kick_player, can_create_nap, can_break_nap, can_ask_money, can_see_reports, can_accept_money_requests, can_change_tax_rate, can_mail_alliance, ' +
                    ' can_manage_description, can_manage_announce, can_see_members_info, can_use_alliance_radars, can_order_other_fleets ' +
                    ' FROM alliances_ranks ' +
                    ' WHERE allianceid=%s AND rankid=%s',  [gcontext['exile_user'].alliance_id, gcontext['exile_user'].alliance_rank.rankid])
                gcontext['hasRight'] = dictfetchall(cursor)
        # retrieve number of new messages & reports
        with connection.cursor() as cursor:
            cursor.execute("SELECT (SELECT int4(COUNT(*)) FROM messages WHERE ownerid=%s AND read_date is NULL)," +
                "(SELECT int4(COUNT(*)) FROM reports WHERE ownerid=%s AND read_date is NULL AND datetime <= now());", [gcontext['exile_user'].id, gcontext['exile_user'].id])
            res = cursor.fetchone()
            if res[0]:
                gcontext["new_mail"] = res[0]
            if res[1]:
                gcontext["new_report"] = res[1]
            cursor.execute("SELECT sp_log_activity(%s, %s, %s)", [gcontext['exile_user'].id, request.META['REMOTE_ADDR'], 0])
        if gcontext['hasRight'] and gcontext['exile_user'].security_level >= 3:
            gcontext["show_alliance"] = {'is_set':True}
            if hasRight(request,"leader") or hasRight(request,"can_manage_description") or hasRight(request,"can_manage_announce"):
                gcontext["show_alliance"]["show_management"] = True
            if hasRight(request,"leader") or hasRight(request,"can_see_reports"):
                gcontext["show_alliance"]["show_reports"] = True
            if hasRight(request,"leader") or hasRight(request,"can_see_members_info"):
                gcontext["show_alliance"]["show_members"] = True
            if hasRight(request,"leader") or hasRight(request,"can_order_other_fleets"):
                gcontext["show_alliance"]["show_fleets"] = True
        if gcontext['exile_user'].security_level >= 3 and config.allowMercenary:
            gcontext["show_mercenary"] = True
        return function(request, *args, **kwargs)

    return decorator

def index(request):
    return HttpResponseRedirect(reverse('exile:connect'))

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@construct
def connect(request):
    """
    def get_browserid(request):
        try:
            browserid = int(request.COOKIES.get("id", "0"))
        except (KeyError, Exception):
            browserid = 0
        if not browserid:
            with connection.cursor() as cursor:
                cursor.execute("SELECT nextval('stats_requests')")
                re = cursor.fetchone()
                browserid = re[0]
        return browserid
    """
    def sp_account_connect(request,context,browserid):
        address = get_client_ip(request)
        addressForwarded = request.get_host()
        userAgent = request.headers.get('User-Agent','')
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, lastplanetid, privilege, resets FROM sp_account_connect2(%s, %s, %s, %s, %s, %s, %s)', [context['user'].id, context['user'].lcid, address, addressForwarded, userAgent, browserid, context['user'].fingerprint])
            return cursor.fetchone()
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    #browserid = get_browserid(request)
    browserid = 0
    res = sp_account_connect(request,context,browserid)
    request.session['sPlanet'] = res[1]
    request.session['sPrivilege'] = res[2]
    request.session['sUser'] = res[0]
    request.session['sLogonUserID'] = res[0]
    if res[2] < 100 and res[3] == 0:
        response = HttpResponseRedirect(reverse('exile:start'))
    elif res[2] == -3:
        response = HttpResponseRedirect(reverse('exile:wait'))
    elif res[2] == -2:
        response = HttpResponseRedirect(reverse('exile:holidays'))
    else:
        response = HttpResponseRedirect(reverse('exile:overview'))
    #response.set_cookies('id',browserid)
    return response

@construct
@logged
def wait(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    return render(request, 'exile/wait.html', context)

@construct
def start(request):
    def sp_get_galaxy_info(userId):
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, recommended FROM sp_get_galaxy_info(%s)', [userId])
            return cursor.fetchall()
    def is_first_login(userId):
        with connection.cursor() as cursor:
            cursor.execute('SELECT login FROM users WHERE resets=0 AND id=%s', [userId])
            return cursor.fetchone()
    def set_login(userId, newName):
        with connection.cursor() as cursor:
            cursor.execute('UPDATE users SET login=%s, lastactivity=now() WHERE id=%s', [newName, userId])
    def init_player(userId, galaxy, orientation):
        with connection.cursor() as cursor:
            cursor.execute('UPDATE users SET orientation=%s, lastactivity=now() WHERE id=%s', [orientation, userId])
            cursor.execute('SELECT sp_reset_account(%s,%s)', [userId, galaxy])
            res = cursor.fetchone()
            if res[0] != 0:
                raise Exception('can\'t reset account')
            if orientation == 1: # merchant
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,10,1)', [userId])
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,11,1)', [userId])
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,12,1)', [userId])
            elif orientation == 2: # military
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,20,1)', [userId])
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,21,1)', [userId])
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,22,1)', [userId])
            elif orientation == 3: # scientist
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,30,1)', [userId])
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,31,1)', [userId])
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,32,1)', [userId])
            elif orientation == 4: # war lord
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,40,1)', [userId])
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,12,1)', [userId])
                cursor.execute('INSERT INTO researches(userid, researchid, level) VALUES(%s,32,1)', [userId])
            cursor.execute('SELECT sp_update_researches(%s)', [userId])
            cursor.execute('UPDATE users SET privilege=0, email=%s WHERE id=%s', [gcontext['user'].email, userId])
        return HttpResponseRedirect(reverse('exile:overview'))
    global config
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    if not config.registration['enabled'] or ( config.registration['until'] is not None and config.registration['until'] < time.time() ):
        return render(request, 'exile/start-closed.html', context)
    userid = request.session.get('sUser', 0)
    galaxy = request.POST.get('galaxy', 0)
    res = is_first_login(userid)
    if not res:
        return HttpResponseRedirect(reverse('exile:index'))
    userName = res[0]
    result = 0
    if not userName:
        newName = request.POST.get('name', '')
        if newName:
            try:
                if isValidName(newName):
                    set_login(userid, newName)
                    userName = newName
                else:
                    result = 11
            except (KeyError, Exception):
                result = 10
    if result == 0:
        orientation = int(request.POST.get('orientation', 0))
        if orientation in config.allowedOrientations:
            #try:
            return init_player(userid, galaxy, orientation)
            #except (KeyError, Exception):
            #    result = 2
    context['galaxies'] = sp_get_galaxy_info(request.session.get('sUser'))
    context['result'] = result
    context['selected'] = galaxy
    context['login'] = userName
    return render(request, 'exile/start.html', context)

@construct
@logged
def holidays(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    return render(request, 'exile/holidays.html', context)

@construct
@logged
def banned(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    return render(request, 'exile/banned.html', context)

@construct
@logged
def locked(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    return render(request, 'exile/locked.html', context)

@construct
@logged
def gameover(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    return render(request, 'exile/game-over.html', context)

@construct
@logged
def overview(request):
    def check_session_stats():
        stat_rank = request.session.get('stat_rank', 0)
        stat_score = request.session.get('stat_score', 0)
        if not stat_rank or not stat_score or stat_score != gcontext['exile_user'].score:
            with connection.cursor() as cursor:
                cursor.execute('SELECT int4(count(1)), (SELECT int4(count(1)) FROM vw_players WHERE score >= %s) FROM vw_players', [gcontext['exile_user'].score])
                res = cursor.fetchone()
                if not res:
                    raise Exception('can\'t get stats')
                request.session['stat_score'] = gcontext['exile_user'].score
                request.session['stat_players'] = res[0]
                request.session['stat_rank'] = res[1]
                gcontext['stat_rank'] = res[1]
                gcontext['stat_score'] = gcontext['exile_user'].score
                gcontext['stat_players'] = res[0]
        else:
            gcontext['stat_rank'] = request.session.get('stat_rank', 0)
            gcontext['stat_score'] = request.session.get('stat_score', 0)
            gcontext['stat_players'] = request.session.get('stat_players', 0)
    def stat_rank_battle():
        with connection.cursor() as cursor:
            cursor.execute('SELECT (SELECT score_prestige FROM users WHERE id=%s), (SELECT int4(count(1)) FROM vw_players WHERE score_prestige >= (SELECT score_prestige FROM users WHERE id=%s))', [gcontext['exile_user'].id, gcontext['exile_user'].id])
            res = cursor.fetchone()
            if not res:
                raise Exception('can\'t get stats')
            gcontext['stat_score_battle'] = res[0]
            if res[1] > request.session.get('stat_players', 0):
                gcontext['stat_rank_battle'] = request.session.get('stat_players', 0)
            else:
                gcontext['stat_rank_battle'] = res[1]
    def stat_empire():
        with connection.cursor() as cursor:
            cursor.execute('SELECT count(1), sum(ore_production), sum(hydrocarbon_production), int4(sum(workers)), int4(sum(scientists)), int4(sum(soldiers)), now() FROM vw_planets WHERE planet_floor > 0 AND planet_space > 0 AND ownerid=%s', [gcontext['exile_user'].id])
            res = cursor.fetchone()
            if not res:
                raise Exception('can\'t get stats')
            gcontext['date'] = res[6]
            gcontext['stat_colonies'] = res[0]
            gcontext['stat_prod_ore'] = res[1]
            gcontext['stat_prod_hydrocarbon'] = res[2]
            cursor.execute('SELECT COALESCE(int4(sum(cargo_workers)), 0), COALESCE(int4(sum(cargo_scientists)), 0), COALESCE(int4(sum(cargo_soldiers)), 0) FROM fleets WHERE ownerid=%s', [gcontext['exile_user'].id])
            res2 = cursor.fetchone()
            if not res2:
                raise Exception('can\'t get stats')
            gcontext['stat_workers'] = res[3] + res2[0]
            gcontext['stat_scientists'] = res[4] + res2[1]
            gcontext['stat_soldiers'] = res[5] + res2[2]
    def cur_buildings_constructions():
        with connection.cursor() as cursor:
            cursor.execute('SELECT p.id, p.name, p.galaxy, p.sector, p.planet, b.buildingid, b.remaining_time, destroying' +
                ' FROM nav_planet AS p' +
                ' LEFT JOIN vw_buildings_under_construction2 AS b ON (p.id=b.planetid)' +
                ' WHERE p.ownerid=%s' +
                ' ORDER BY p.id, destroying, remaining_time DESC', [gcontext['exile_user'].id])
            res = cursor.fetchall()
            if not res:
                raise Exception('can\'t get stats')
            constructionyards = {}
            for re in res:
                if re[0] not in constructionyards.keys():
                    constructionyards[re[0]] = {
                        'planetid': re[0],
                        'planetname': re[1],
                        'galaxy': re[2],
                        'sector': re[3],
                        'planet': re[4],
                        'buildings': {},
                    }
                if re[5]:
                    constructionyards[re[0]]['buildings'][re[5]] = {
                        'buildingid': re[5],
                        'building': getBuildingLabel(re[5]),
                        'time': re[6],
                        'destroy': re[7],
                    }
            return constructionyards
    def cur_ships_constructions():
        with connection.cursor() as cursor:
            cursor.execute('SELECT p.id, p.name, p.galaxy, p.sector, p.planet, s.shipid, s.remaining_time, s.recycle, p.shipyard_next_continue IS NOT NULL, p.shipyard_suspended,' +
                ' (SELECT shipid FROM planet_ships_pending WHERE planetid=p.id ORDER BY start_time LIMIT 1)' +
                ' FROM nav_planet AS p' +
                ' LEFT JOIN vw_ships_under_construction AS s ON (p.id=s.planetid AND p.ownerid=s.ownerid AND s.end_time IS NOT NULL)' +
                ' WHERE (s.recycle OR EXISTS(SELECT 1 FROM planet_buildings WHERE (buildingid = 105 OR buildingid = 205) AND planetid=p.id)) AND p.ownerid=%s' +
                ' ORDER BY p.id, s.remaining_time DESC', [gcontext['exile_user'].id])
            res = cursor.fetchall()
            if not res:
                raise Exception('can\'t get ships constructions')
            shipyards = {}
            for re in res:
                if re[0] not in shipyards.keys():
                    shipyards[re[0]] = {
                        'planetid': re[0],
                        'planetname': re[1],
                        'galaxy': re[2],
                        'sector': re[3],
                        'planet': re[4],
                        'shipid': re[5],
                        'ship': getShipLabel(re[5]),
                        'time': re[6],
                        'recycle': re[7],
                        'waiting_resources': re[8],
                        'suspended': re[9],
                        'waiting_ship': getShipLabel(re[10]),
                    }
            return shipyards
    def cur_researches():
        with connection.cursor() as cursor:
            cursor.execute('SELECT researchid, int4(date_part(\'epoch\', end_time-now())) FROM researches_pending WHERE userid=%s', [gcontext['exile_user'].id])
            res = cursor.fetchall()
            if not res:
                raise Exception('can\'t get researches')
            researches = {}
            for re in res:
                if re[0] not in researches.keys():
                    researches[re[0]] = {
                        'researchid': re[0],
                        'research': getResearchLabel(re[0]),
                        'time': re[1],
                    }
            return researches
    def get_fleets():
        with connection.cursor() as cursor:
            cursor.execute('SELECT f.id, f.name, f.signature, f.ownerid, ' +
            'COALESCE((( SELECT vw_relations.relation FROM vw_relations WHERE vw_relations.user1 = users.id AND vw_relations.user2 = f.ownerid)), -3) AS owner_relation, f.owner_name,' +
            'f.planetid, f.planet_name, COALESCE((( SELECT vw_relations.relation FROM vw_relations WHERE vw_relations.user1 = users.id AND vw_relations.user2 = f.planet_ownerid)), -3) AS planet_owner_relation, f.planet_galaxy, f.planet_sector, f.planet_planet, ' +
            'f.destplanetid, f.destplanet_name, COALESCE((( SELECT vw_relations.relation FROM vw_relations WHERE vw_relations.user1 = users.id AND vw_relations.user2 = f.destplanet_ownerid)), -3) AS destplanet_owner_relation, f.destplanet_galaxy, f.destplanet_sector, f.destplanet_planet, ' +
            'f.planet_owner_name, f.destplanet_owner_name, f.speed,' +
            'COALESCE(f.remaining_time, 0), COALESCE(f.total_time-f.remaining_time, 0), ' +
            '( SELECT int4(COALESCE(max(nav_planet.radar_strength), 0)) FROM nav_planet WHERE nav_planet.galaxy = f.planet_galaxy AND nav_planet.sector = f.planet_sector AND nav_planet.ownerid IS NOT NULL AND EXISTS ( SELECT 1 FROM vw_friends_radars WHERE vw_friends_radars.friend = nav_planet.ownerid AND vw_friends_radars.userid = users.id)) AS from_radarstrength, ' +
            '( SELECT int4(COALESCE(max(nav_planet.radar_strength), 0)) FROM nav_planet WHERE nav_planet.galaxy = f.destplanet_galaxy AND nav_planet.sector = f.destplanet_sector AND nav_planet.ownerid IS NOT NULL AND EXISTS ( SELECT 1 FROM vw_friends_radars WHERE vw_friends_radars.friend = nav_planet.ownerid AND vw_friends_radars.userid = users.id)) AS to_radarstrength, ' +
            'attackonsight' +
            ' FROM users, vw_fleets f ' +
            ' WHERE users.id=%s AND (action = 1 OR action = -1) AND (ownerid=%s OR (destplanetid IS NOT NULL AND destplanetid IN (SELECT id FROM nav_planet WHERE ownerid=%s)))' +
            ' ORDER BY ownerid, COALESCE(remaining_time, 0)', [gcontext['exile_user'].id, gcontext['exile_user'].id, gcontext['exile_user'].id])
            res = cursor.fetchall()
            if not res:
                raise Exception('can\'t get fleets')
            fleets = {}
            for re in res:
                parseFleet = True
                fleet = {
                    'signature': re[2],
                    'f_planetname': getPlanetName(request,re[8], re[23], re[18], re[7]),
                    'f_planetid': re[6],
                    'f_g': re[9],
                    'f_s': re[10],
                    'f_p': re[11],
                    'f_relation': re[8],
                    't_planetname': getPlanetName(request,re[14], re[24], re[19], re[13]),
                    't_planetid': re[12],
                    't_g': re[15],
                    't_s': re[16],
                    't_p': re[17],
                    't_relation': re[14],
                    'time': re[21],
                }
                # retrieve the radar strength where the fleet comes from
                if re[23]:
                    extRadarStrength = re[23]
                else:
                    extRadarStrength = 0
                # retrieve the radar strength where the fleet goes to
                if re[24]:
                    incRadarStrength = re[24]
                else:
                    incRadarStrength = 0
                if re[6]:
                    if re[4] < config.rAlliance and re[21] > math.sqrt(incRadarStrength)*6*1000/re[20]*3600 and (extRadarStrength == 0 or incRadarStrength == 0):
                        parseFleet = False
                    else:
                        if extRadarStrength > 0 or re[4] >= config.rAlliance or re[8] >= config.rFriend:
                            fleet['movingfrom'] = True
                        else:
                            fleet['movingfrom'] = False
                if parseFleet:
                    if re[4] == config.rSelf:
                        fleet['id'] = re[0]
                        fleet['name'] = re[1]
                        if re[25]:
                            fleet['owned'] = 'attack'
                        else:
                            fleet['owned'] = 'defend'
                    elif re[4] == config.rAlliance:
                        fleet['id'] = re[3]
                        fleet['name'] = re[5]
                        if re[25]:
                            fleet['ally'] = 'attack'
                        else:
                            fleet['ally'] = 'defend'
                    elif re[4] == config.rFriend:
                        fleet['id'] = re[3]
                        fleet['name'] = re[5]
                        if re[25]:
                            fleet['friend'] = 'attack'
                        else:
                            fleet['friend'] = 'defend'
                    else:
                        fleet['id'] = re[3]
                        fleet['name'] = re[5]
                        fleet['hostile'] = True
                fleets[re[0]] = fleet.copy()
            return fleets

    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'overview'
    gcontext['menu'] = menu(request)
    context = gcontext
    t = loader.get_template('exile/overview.html')
    context['stat_score'] = context['exile_user'].score
    context['stat_score_delta'] = context['exile_user'].score - context['exile_user'].previous_score
    context['stat_credits'] = context['exile_user'].credits
    try:
        check_session_stats()
    except (KeyError, Exception):
        pass
    context['stat_victory_marks'] = context['exile_user'].prestige_points
    context['stat_maxcolonies'] = int(context['exile_user'].mod_planets)
    #try:
    stat_rank_battle()
    #except (KeyError, Exception):
    #    pass
    #try:
    stat_empire()
    #except (KeyError, Exception):
    #    pass
    try:
        context['constructionyards'] = cur_buildings_constructions()
    except (KeyError, Exception):
        context['constructionyards'] = {}
    try:
        context['shipyards'] = cur_ships_constructions()
    except (KeyError, Exception):
        context['shipyards'] = {}
    try:
        context['research'] = cur_researches()
    except (KeyError, Exception):
        context['research'] = {}
    try:
        context['fleets'] = get_fleets()
    except (KeyError, Exception):
        context['fleets'] = {}

    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def upkeep(request):
    def getCosts():
        hours = 24 - datetime.datetime.now().hour
        with connection.cursor() as cursor:
            cursor.execute('SELECT scientists,soldiers,planets,ships_signature,ships_in_position_signature,ships_parked_signature,' +
            ' cost_planets2,cost_scientists,cost_soldiers,cost_ships,cost_ships_in_position,cost_ships_parked,' +
            ' int4(upkeep_scientists + scientists*cost_scientists/24*%(hours)s),' +
            ' int4(upkeep_soldiers + soldiers*cost_soldiers/24*%(hours)s),' +
            ' int4(upkeep_planets + cost_planets2/24*%(hours)s),' +
            ' int4(upkeep_ships + ships_signature*cost_ships/24*%(hours)s),' +
            ' int4(upkeep_ships_in_position + ships_in_position_signature*cost_ships_in_position/24*%(hours)s),' +
            ' int4(upkeep_ships_parked + ships_parked_signature*cost_ships_parked/24*%(hours)s),' +
            ' commanders, commanders_salary, cost_commanders, upkeep_commanders + int4(commanders_salary*cost_commanders/24*%(hours)s)' +
            ' FROM vw_players_upkeep' +
            ' WHERE userid=%(UserId)s', {'hours': hours, 'UserId': gcontext['exile_user'].id})
            res = cursor.fetchone()
            if not res:
                raise Exception('can\'t get upkeep')
            gcontext['upkeep'] = {
                "commanders_quantity": res[18],
                "commanders_salary": res[19],
                "commanders_cost": res[20],
                "commanders_estimated_cost": res[21],
                "scientists_quantity": res[0],
                "soldiers_quantity": res[1],
                "planets_quantity": res[2],
                "ships_signature": res[3],
                "ships_in_position_signature": res[4],
                "ships_parked_signature": res[5],
                "planets_cost": res[6],
                "scientists_cost": res[7],
                "soldiers_cost": res[8],
                "ships_cost": res[9],
                "ships_in_position_cost": res[10],
                "ships_parked_cost": res[11],
                "scientists_estimated_cost": res[12],
                "soldiers_estimated_cost": res[13],
                "planets_estimated_cost": res[14],
                "ships_estimated_cost": res[15],
                "ships_in_position_estimated_cost": res[16],
                "ships_parked_estimated_cost": res[17],
                "total_estimation": res[12] + res[13] + res[14] + res[15] + res[16] + res[17] + res[21],
            }
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'upkeep'
    gcontext['menu'] = menu(request)
    context = gcontext
    FillHeaderCredits(request)
    getCosts()
    t = loader.get_template('exile/upkeep.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def commanders(request):
    max_ore = 2.0
    max_hydrocarbon = 2.0
    max_energy = 2.0
    max_workers = 2.0
    max_speed = 1.3
    max_shield = 1.4
    max_handling = 1.75
    max_targeting = 1.75
    max_damages = 1.3
    max_signature = 1.2
    max_recycling = 1.1
    max_build = 3
    max_ship = 3
    def ListCommanders():
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_commanders_check_new_commanders(%s)', [gcontext['exile_user'].id])
            cursor.execute('SELECT int4(count(1)) FROM commanders WHERE recruited <= now() AND ownerid=%s', [gcontext['exile_user'].id])
            res = cursor.fetchone()
            if not res:
                can_engage_commander = 0 < gcontext['exile_user'].mod_commanders
            else:
                can_engage_commander = res[0] < gcontext['exile_user'].mod_commanders
            cursor.execute('SELECT c.id, c.name, c.recruited, points, added, salary, can_be_fired, ' +
                ' p.id, p.galaxy, p.sector, p.planet, p.name, ' +
                ' f.id, f.name, ' +
                ' c.mod_production_ore, c.mod_production_hydrocarbon, c.mod_production_energy, ' +
                ' c.mod_production_workers, c.mod_fleet_speed, c.mod_fleet_shield, ' +
                ' c.mod_fleet_handling, c.mod_fleet_tracking_speed, c.mod_fleet_damage, c.mod_fleet_signature, ' +
                ' c.mod_construction_speed_buildings, c.mod_construction_speed_ships, last_training < now()-interval \'1 day\', sp_commanders_prestige_to_train(c.ownerid, c.id), salary_increases < 20 ' +
                ' FROM commanders AS c ' +
                '   LEFT JOIN fleets AS f ON (c.id=f.commanderid) ' +
                '   LEFT JOIN nav_planet AS p ON (c.id=p.commanderid) ' +
                ' WHERE c.ownerid=%s ' +
                ' ORDER BY upper(c.name)', [gcontext['exile_user'].id])
            available_commanders_count = 0
            commanders_count = 0
            available_commanders = {}
            commanders = {}
            res = cursor.fetchall()
            if not res:
                return
            else:
                available_commanders = {}
                commanders = {}
                for re in res:
                    commander = {
                        "id": re[0],
                        "name": re[1],
                        "recruited": re[2],
                        "added": re[4],
                        "salary": re[5],
                        "bonus": {"description": {}}
                    }
                    if not re[7]: # commander is not assigned to a planet
                        if not re[12]: # nor to a fleet
                            commander['not_assigned'] = True
                        else:
                            commander['fleet_command'] = {
                                "fleetid": re[12],
                                "commandment": re[13],
                            }
                    else:
                        commander['planet_command'] = {
                            "planetid": re[7],
                            "g": re[8],
                            "s": re[9],
                            "p": re[10],
                            "commandment": re[11],
                        }
                    for i in range(15,26):
                        if re[i] != 1:
                            commander['bonus']['description'][i] = round((re[i]-1)*100)
                    if re[26] and re[28]:
                        commander['train'] = True
                        commander['prestige'] = re[27]
                    elif re[28]:
                        commander['cant_train'] = True
                    else:
                        commander['cant_train_anymore'] = True
                    if re[3] > 0:
                        commander['levelup'] = re[3]
                    if not re[2]:
                        available_commanders_count += 1
                        commander['can_engage'] = can_engage_commander
                        available_commanders[re[0]] = commander.copy()
                    else:
                        commanders_count += 1
                        commander['can_fire'] = re[6]
                        commanders[re[0]] = commander.copy()
            gcontext['available_commanders_count'] = available_commanders_count
            gcontext['available_commanders'] = available_commanders
            gcontext['commanders_count'] = commanders_count
            gcontext['commanders'] = commanders
    def DisplayCommanderEdition(CommanderId):
        gcontext['commanderid'] = CommanderId
        gcontext['editcommander'] = {}
        if CommanderId != 0:
            with connection.cursor() as cursor:
                cursor.execute('SELECT mod_production_ore, mod_production_hydrocarbon, mod_production_energy,' +
                    ' mod_production_workers, mod_fleet_speed, mod_fleet_shield, mod_fleet_handling,' +
                    ' mod_fleet_tracking_speed, mod_fleet_damage, mod_fleet_signature,' +
                    ' mod_construction_speed_buildings, mod_construction_speed_ships,' +
                    ' points, name' +
                    ' FROM commanders WHERE id=%s AND ownerid=%s', [CommanderId, gcontext['exile_user'].id])
                res = cursor.fetchone()
                if not res:
                    return HttpResponseRedirect(reverse('exile:commanders'))
                gcontext['editcommander']["name"] = res[13]
                gcontext['editcommander']["maxpoints"] = res[12]
                gcontext['editcommander']["ore"] = res[0]
                gcontext['editcommander']["hydrocarbon"] = res[1]
                gcontext['editcommander']["energy"] = res[2]
                gcontext['editcommander']["workers"] = res[3]
                gcontext['editcommander']["speed"] = res[4]
                gcontext['editcommander']["shield"] = res[5]
                gcontext['editcommander']["handling"] = res[6]
                gcontext['editcommander']["targeting"] = res[7]
                gcontext['editcommander']["damages"] = res[8]
                gcontext['editcommander']["signature"] = res[9]
                gcontext['editcommander']["build"] = res[10]
                gcontext['editcommander']["ship"] = res[11]
                gcontext['editcommander']["max_ore"] = max_ore
                gcontext['editcommander']["max_hydrocarbon"] = max_hydrocarbon
                gcontext['editcommander']["max_energy"] = max_energy
                gcontext['editcommander']["max_workers"] = max_workers
                gcontext['editcommander']["max_speed"] = max_speed
                gcontext['editcommander']["max_shield"] = max_shield
                gcontext['editcommander']["max_handling"] = max_handling
                gcontext['editcommander']["max_targeting"] = max_targeting
                gcontext['editcommander']["max_damages"] = max_damages
                gcontext['editcommander']["max_signature"] = max_signature
                gcontext['editcommander']["max_build"] = max_build
                gcontext['editcommander']["max_ship"] = max_ship
                gcontext['editcommander']["max_recycling"] = max_recycling
    def EditCommander(CommanderId):
        ore = max(0, int(request.POST.get("ore", 0)))
        hydrocarbon = max(0, int(request.POST.get("hydrocarbon", 0)))
        energy = max(0, int(request.POST.get("energy", 0)))
        workers = max(0, int(request.POST.get("workers", 0)))
        fleetspeed = max(0, int(request.POST.get("fleet_speed", 0)))
        fleetshield = max(0, int(request.POST.get("fleet_shield", 0)))
        fleethandling = max(0, int(request.POST.get("fleet_handling", 0)))
        fleettargeting = max(0, int(request.POST.get("fleet_targeting", 0)))
        fleetdamages = max(0, int(request.POST.get("fleet_damages", 0)))
        fleetsignature = max(0, int(request.POST.get("fleet_signature", 0)))
        build = max(0, int(request.POST.get("buildindspeed", 0)))
        ship = max(0, int(request.POST.get("shipconstructionspeed", 0)))
        total = ore + hydrocarbon + energy + workers + fleetspeed + fleetshield + fleethandling + fleettargeting + fleetdamages + fleetsignature + build + ship
        with connection.cursor() as cursor:
            cursor.execute('UPDATE commanders SET' +
                ' mod_production_ore=mod_production_ore + 0.01*%s' +
                ' ,mod_production_hydrocarbon=mod_production_hydrocarbon + 0.01*%s' +
                ' ,mod_production_energy=mod_production_energy + 0.1*%s' +
                ' ,mod_production_workers=mod_production_workers + 0.1*%s' +
                ' ,mod_fleet_speed=mod_fleet_speed + 0.02*%s' +
                ' ,mod_fleet_shield=mod_fleet_shield + 0.02*%s' +
                ' ,mod_fleet_handling=mod_fleet_handling + 0.05*%s' +
                ' ,mod_fleet_tracking_speed=mod_fleet_tracking_speed + 0.05*%s' +
                ' ,mod_fleet_damage=mod_fleet_damage + 0.02*%s' +
                ' ,mod_fleet_signature=mod_fleet_signature + 0.02*%s' +
                ' ,mod_construction_speed_buildings=mod_construction_speed_buildings + 0.05*%s' +
                ' ,mod_construction_speed_ships=mod_construction_speed_ships + 0.05*%s' +
                ' ,points=points-%s' +
                ' WHERE ownerid=%s AND id=%s AND points >= %s', [ore, hydrocarbon, energy, workers, fleetspeed, fleetshield, fleethandling, fleettargeting, fleetdamages, fleetsignature, build, ship, total, gcontext['exile_user'].id, CommanderId, total])
            cursor.execute('SELECT mod_production_ore, mod_production_hydrocarbon, mod_production_energy,' +
                ' mod_production_workers, mod_fleet_speed, mod_fleet_shield, mod_fleet_handling,' +
                ' mod_fleet_tracking_speed, mod_fleet_damage, mod_fleet_signature,' +
                ' mod_construction_speed_buildings, mod_construction_speed_ships' +
                ' FROM commanders' +
                ' WHERE id=%s AND ownerid=%s', [CommanderId, gcontext['exile_user'].id])
            res = cursor.fetchone()
            if not res:
                return HttpResponseRedirect(reverse('exile:commanders'))
            if res[0] <= max_ore+0.0001 and res[1] <= max_hydrocarbon+0.0001 and res[2] <= max_energy+0.0001 and res[3] <= max_workers+0.0001 and \
                res[4] <= max_speed+0.0001 and res[5] <= max_shield+0.0001 and res[6] <= max_handling+0.0001 and res[7] <= max_targeting+0.0001 and \
                res[8] <= max_damages+0.0001 and res[9] <= max_signature+0.0001 and res[10] <= max_build+0.0001 and res[11] <= max_ship+0.0001:
                cursor.execute('SELECT sp_update_fleet_bonus(id) FROM fleets WHERE commanderid=%s', [CommanderId])
                cursor.execute('SELECT sp_update_planet(id) FROM nav_planet WHERE commanderid=%s', [CommanderId])
        return HttpResponseRedirect(reverse('exile:commanders'))
    def RenameCommander(CommanderId, NewName):
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_commanders_rename(%s, %s, %s)', [gcontext['exile_user'].id, CommanderId, NewName])
            return HttpResponseRedirect(reverse('exile:commanders'))
    def EngageCommander(CommanderId):
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_commanders_engage(%s, %s)', [gcontext['exile_user'].id, CommanderId])
            return HttpResponseRedirect(reverse('exile:commanders'))
    def FireCommander(CommanderId):
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_commanders_fire(%s, %s)', [gcontext['exile_user'].id, CommanderId])
            return HttpResponseRedirect(reverse('exile:commanders'))
    def TrainCommander(CommanderId):
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_commanders_train(%s, %s)', [gcontext['exile_user'].id, CommanderId])
            return HttpResponseRedirect(reverse('exile:commanders'))
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'commanders'
    gcontext['menu'] = menu(request)
    context = gcontext
    CommanderId = request.POST.get('id',request.GET.get('id', 0))
    NewName = request.POST.get('name', request.GET.get('name', 0))
    a = request.POST.get('a', request.GET.get('a', ''))
    if a == 'rename':
        return RenameCommander(CommanderId, NewName)
    elif a == 'edit':
        return EditCommander(CommanderId)
    elif a == "fire":
        return FireCommander(CommanderId)
    elif a == "engage":
        return EngageCommander(CommanderId)
    elif a == "skills":
        DisplayCommanderEdition(CommanderId)
    elif a == "train":
        return TrainCommander(CommanderId)
    else:
        ListCommanders()
    gcontext['max_commanders'] = int(gcontext['exile_user'].mod_commanders)
    t = loader.get_template('exile/commanders.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)


@construct
@logged
def fleettrade(request):
    def RetrieveFleetOwnerId(fleetid):
        # retrieve fleet owner
        with connection.cursor() as cursor:
            cursor.execute("SELECT ownerid FROM vw_fleets as f" +
                " WHERE (ownerid=%s OR (shared AND owner_alliance_id=%s)) AND id=%s", [gcontext['exile_user'].id, gcontext['can_command_alliance_fleets'], fleetid])
            res = cursor.fetchone()
            gcontext['fleet_owner_id'] = res[0]
    # display fleet info
    def DisplayExchangeForm(fleetid):
        # retrieve fleet name, size, position, destination
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, attackonsight, engaged, size, signature, speed, remaining_time, commanderid, commandername," +
                " planetid, planet_name, planet_galaxy, planet_sector, planet_planet, planet_ownerid, planet_owner_name, planet_owner_relation," +
                " cargo_capacity, cargo_ore, cargo_hydrocarbon, cargo_scientists, cargo_soldiers, cargo_workers" +
                " FROM vw_fleets" +
                " WHERE ownerid=%s AND id=%s", [gcontext['fleet_owner_id'], fleetid])
            res = cursor.fetchone()
            # if fleet doesn't exist, redirect to the list of fleets
            if not res:
                if request.GET.get("a") == "open":
                    return False
                else:
                    return HttpResponseRedirect(reverse('exile:fleets'))
            relation = res[17]
            # if fleet is moving or engaged, go back to the fleets
            if res[7] or res[3]:
                if request.GET.get("a") == "open":
                    relation = config.rWar
                else:
                    return HttpResponseRedirect(reverse('exile:fleet') + "?id=" + str(fleetid))
            gcontext["fleetid"] = fleetid
            gcontext["fleetname"] = res[1]
            gcontext["size"] = res[4]
            gcontext["speed"] = res[6]
            gcontext["fleet_capacity"] = res[18]
            gcontext["fleet_ore"] = res[19]
            gcontext["fleet_hydrocarbon"] = res[20]
            gcontext["fleet_scientists"] = res[21]
            gcontext["fleet_soldiers"] = res[22]
            gcontext["fleet_workers"] = res[23]
            gcontext["fleet_load"] = res[19] + res[20] + res[21] + res[22] + res[23]
            if relation == config.rSelf:
                # retrieve planet ore, hydrocarbon, workers, relation
                cursor.execute("SELECT ore, hydrocarbon, scientists, soldiers," +
                        " GREATEST(0, workers-GREATEST(workers_busy,workers_for_maintenance-workers_for_maintenance/2+1,500))," +
                        " workers > workers_for_maintenance/2" +
                        " FROM vw_planets WHERE id=%s", [res[10]])
                res = cursor.fetchone()
                gcontext["planet_ore"] = res[0]
                gcontext["planet_hydrocarbon"] = res[1]
                gcontext["planet_scientists"] = res[2]
                gcontext["planet_soldiers"] = res[3]
                gcontext["planet_workers"] = res[4]
                gcontext["load"] = {'not_enough_workers_to_load': False}
                if not res[5]:
                    gcontext["planet_ore"] = 0
                    gcontext["planet_hydrocarbon"] = 0
                    gcontext["load"]['not_enough_workers_to_load'] = True
            elif relation == config.rFriend or relation == config.rAlliance or relation == config.rHostile:
                gcontext["unload"] = True
            else:
                gcontext["cargo"] = True
    def TransferResources(fleetid):
        try:
            ore = int(request.GET.get("load_ore", 0)) - int(request.GET.get("unload_ore", 0))
            hydrocarbon = int(request.GET.get("load_hydrocarbon", 0)) - int(request.GET.get("unload_hydrocarbon", 0))
            scientists = int(request.GET.get("load_scientists", 0)) - int(request.GET.get("unload_scientists", 0))
            soldiers = int(request.GET.get("load_soldiers", 0)) - int(request.GET.get("unload_soldiers", 0))
            workers = int(request.GET.get("load_workers", 0)) - int(request.GET.get("unload_workers", 0))
            if ore != 0 or hydrocarbon != 0 or scientists != 0 or soldiers != 0 or workers != 0:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT sp_transfer_resources_with_planet(%s, %s, %s, %s, %s, %s, %s)", [gcontext['fleet_owner_id'], fleetid, ore, hydrocarbon, scientists, soldiers, workers])
        except (KeyError, Exception):
            pass
    def TransferResourcesViaPost(fleetid):
        try:
            ore = int(request.POST.get("load_ore", 0)) - int(request.POST.get("unload_ore", 0))
            hydrocarbon = int(request.POST.get("load_hydrocarbon", 0)) - int(request.POST.get("unload_hydrocarbon", 0))
            scientists = int(request.POST.get("load_scientists", 0)) - int(request.POST.get("unload_scientists", 0))
            soldiers = int(request.POST.get("load_soldiers", 0)) - int(request.POST.get("unload_soldiers", 0))
            workers = int(request.POST.get("load_workers", 0)) - int(request.POST.get("unload_workers", 0))
            if ore != 0 or hydrocarbon != 0 or scientists != 0 or soldiers != 0 or workers != 0:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT sp_transfer_resources_with_planet(%s, %s, %s, %s, %s, %s, %s)", [gcontext['fleet_owner_id'], fleetid, ore, hydrocarbon, scientists, soldiers, workers])
                    res = cursor.fetchone()
                    return HttpResponseRedirect(reverse('exile:fleet') + "?id=" + str(fleetid) + "&trade=" + str(res[0]))
        except (KeyError, Exception):
            pass
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'fleets'
    gcontext['menu'] = menu(request)
    gcontext['can_command_alliance_fleets'] = -1
    if gcontext['exile_user'].alliance_id and hasRight(request,"can_order_other_fleets"):
        gcontext['can_command_alliance_fleets'] = gcontext['exile_user'].alliance_id
    gcontext['fleet_owner_id'] = gcontext['exile_user'].id
    try:
        fleetid = int(request.GET.get("id", 0))
    except (KeyError, Exception):
        fleetid = 0
    if fleetid == 0:
        return HttpResponseRedirect(reverse('exile:fleets'))
    RetrieveFleetOwnerId(fleetid)
    r = TransferResourcesViaPost(fleetid)
    if r:
        return r
    if request.GET.get("a", "") != "open":
        return HttpResponseRedirect(reverse('exile:fleet') + "?id=" + str(fleetid))
    TransferResources(fleetid)
    r = DisplayExchangeForm(fleetid)
    if r:
        return r
    context = gcontext
    return render(request, 'exile/fleet-trade.html', context)

@construct
@logged
def fleetsplit(request):
    # display fleet info
    def DisplayExchangeForm(fleetid):
        # retrieve fleet name, size, position, destination
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, attackonsight, engaged, size, signature, speed, remaining_time, commanderid, commandername," +
                " planetid, planet_name, planet_galaxy, planet_sector, planet_planet, planet_ownerid, planet_owner_name, planet_owner_relation," +
                " cargo_capacity, cargo_ore, cargo_hydrocarbon, cargo_scientists, cargo_soldiers, cargo_workers," +
                " action " +
                " FROM vw_fleets" +
                " WHERE ownerid=%s AND id=%s", [gcontext['exile_user'].id, fleetid])
            re = cursor.fetchone()
            # if fleet doesn't exist, redirect to the list of fleets
            if not re:
                return HttpResponseRedirect(reverse('exile:fleets'))
            # if fleet is moving or engaged, go back to the fleets
            if re[24]:
                return HttpResponseRedirect(reverse('exile:fleet')+"?id=" + str(fleetid))
            gcontext["fleetid"] = fleetid
            gcontext["fleetname"] = re[1]
            gcontext["size"] = re[4]
            gcontext["speed"] = re[6]
            gcontext["fleet_capacity"] = re[18]
            gcontext["available_ore"] = re[19]
            gcontext["available_hydrocarbon"] = re[20]
            gcontext["available_scientists"] = re[21]
            gcontext["available_soldiers"] = re[22]
            gcontext["available_workers"] = re[23]
            gcontext["fleet_load"] = re[19] + re[20] + re[21] + re[22] + re[23]
            # retrieve the list of ships in the fleet
            cursor.execute("SELECT db_ships.id, db_ships.label, db_ships.capacity, db_ships.signature," +
                "COALESCE((SELECT quantity FROM fleets_ships WHERE fleetid=%s AND shipid = db_ships.id), 0)" +
                " FROM fleets_ships" +
                "   INNER JOIN db_ships ON (db_ships.id=fleets_ships.shipid)" +
                " WHERE fleetid=%s" +
                " ORDER BY db_ships.category, db_ships.label", [fleetid, fleetid])
            res = cursor.fetchall()
            shipCount = 0
            gcontext['ship'] = {}
            for re in res:
                shipCount += 1
                ship = {
                    "id": re[0],
                    "name": re[1],
                    "cargo_capacity": re[2],
                    "signature": re[3],
                    "quantity": re[4],
                }
                if fleet_split_error != e_no_error:
                    ship["transfer"], request.POST.get("transfership"+str(re[0]),"")
                gcontext['ship'][shipCount] = ship.copy()
            if fleet_split_error != e_no_error:
                gcontext["error"+str(fleet_split_error)] = True
                gcontext["t_ore"] = request.POST.get("load_ore","")
                gcontext["t_hydrocarbon"] = request.POST.get("load_hydrocarbon","")
                gcontext["t_scientists"] = request.POST.get("load_scientists","")
                gcontext["t_workers"] = request.POST.get("load_workers","")
                gcontext["t_soldiers"] = request.POST.get("load_soldiers","")
            return False
    # split current fleet into 2 fleets
    def SplitFleet(fleetid):
        newfleetname = request.POST.get("newname","")
        if not isValidName(newfleetname):
            fleet_split_error = e_bad_name
            return
        # retrieve the planet where the current fleet is patrolling
        with connection.cursor() as cursor:
            cursor.execute("SELECT planetid FROM vw_fleets WHERE ownerid=%s AND id=%s", [gcontext['exile_user'].id, fleetid])
            re = cursor.fetchone()
            if not re:
                return
            fleetplanetid = re[0]
            # retrieve 'source' fleet cargo and action
            cursor.execute(" SELECT id, action, cargo_ore, cargo_hydrocarbon, " +
                    " cargo_scientists, cargo_soldiers, cargo_workers" +
                    " FROM vw_fleets" +
                    " WHERE ownerid=%s AND id=%s", [gcontext['exile_user'].id, fleetid])
            re = cursor.fetchone()
            if not re:
                fleet_split_error = e_occupied
                return
            try:
                ore = min(int(request.POST.get("load_ore", "0")), re[2])
            except (KeyError, Exception):
                ore = 0
            try:
                hydrocarbon = min(int(request.POST.get("load_hydrocarbon", "0")), re[3])
            except (KeyError, Exception):
                hydrocarbon = 0
            try:
                scientists = min(int(request.POST.get("load_scientists", "0")), re[4])
            except (KeyError, Exception):
                scientists = 0
            try:
                soldiers = min(int(request.POST.get("load_soldiers", "0")), re[5])
            except (KeyError, Exception):
                soldiers = 0
            try:
                workers = min(int(request.POST.get("load_workers", "0")), re[6])
            except (KeyError, Exception):
                workers = 0
            # 1/ create a new fleet at the current fleet planet with the given name
            cursor.execute("SELECT sp_create_fleet(%s, %s, %s)", [gcontext['exile_user'].id, fleetplanetid, newfleetname])
            re = cursor.fetchone()
            if not re:
                return
            newfleetid = re[0]
            if newfleetid < 0:
                if newfleetid == -1:
                    fleet_split_error = e_already_exists
                elif newfleetid == -2:
                    fleet_split_error = e_already_exists
                elif newfleetid == -3:
                    fleet_split_error = e_limit_reached
                return
            # 2/ add the ships to the new fleet
            # retrieve ships belonging to current fleet
            cursor.execute("SELECT db_ships.id, " +
                "COALESCE((SELECT quantity FROM fleets_ships WHERE fleetid=%s AND shipid = db_ships.id), 0)" +
                " FROM db_ships" +
                " ORDER BY db_ships.category, db_ships.label", [fleetid])
            res = cursor.fetchall()
            if not res:
                availableCount = -1
                availableArray = []
            else:
                availableArray = res.copy()
                availableCount = len(availableArray)
            # for each available ship id, check if the player wants to add ships of this kind
            for i in availableArray:
                shipid = i[0]
                try:
                    quantity = min(int(request.POST.get("transfership"+str(shipid), "0")), i[1])
                except (KeyError, Exception):
                    quantity = 0
                if quantity > 0:
                    # add the ships to the new fleet
                    cursor.execute(" INSERT INTO fleets_ships (fleetid, shipid, quantity) VALUES (%s, %s, %s)", [newfleetid, shipid, quantity])
            # reset fleets idleness, partly to prevent cheating and being able to do multiple invasions with only a fleet
            cursor.execute("UPDATE fleets SET idle_since=now() WHERE ownerid =%s AND (id=%s OR id=%s)", [gcontext['exile_user'].id, newfleetid, fleetid])
            # 3/ Move the resources to the new fleet
            #   a/ Add resources to the new fleet
            #   b/ Remove resource from the 'source' fleet
            # retrieve new fleet's cargo capacity
            cursor.execute("SELECT cargo_capacity FROM vw_fleets WHERE ownerid=%s AND id=%s", [gcontext['exile_user'].id, newfleetid])
            re = cursor.fetchone()
            newload = re[0]
            ore = min( ore, newload)
            newload -= ore
            hydrocarbon = min( hydrocarbon, newload)
            newload -= hydrocarbon
            scientists = min( scientists, newload)
            newload-= scientists
            soldiers = min( soldiers, newload)
            newload -= soldiers
            workers = min( workers, newload)
            newload -= workers
            if ore or hydrocarbon or scientists or soldiers or workers:
                # a/ put the resources to the new fleet
                cursor.execute("UPDATE fleets SET cargo_ore=%s, cargo_hydrocarbon=%s, cargo_scientists=%s, cargo_soldiers=%s, cargo_workers=%s WHERE id=%s AND ownerid=%s",
                    [ore, hydrocarbon, scientists, soldiers, workers, newfleetid, gcontext['exile_user'].id])
                # b/ remove the resources from the 'source' fleet
                cursor.execute("UPDATE fleets SET" +
                            " cargo_ore=cargo_ore-%s, cargo_hydrocarbon=cargo_hydrocarbon-%s, " +
                            " cargo_scientists=cargo_scientists-%s, cargo_soldiers=cargo_soldiers-%s, cargo_workers=cargo_workers-%s" +
                            " WHERE id=%s AND ownerid=%s", [ore, hydrocarbon, scientists, soldiers, workers, fleetid, gcontext['exile_user'].id])
            # 4/ Remove the ships from the 'source' fleet
            for i in availableArray:
                shipid = i[0]
                try:
                    quantity = min(int(request.POST.get("transfership"+str(shipid), "0")), i[1])
                except (KeyError, Exception):
                    quantity = 0
                if quantity > 0:
                    # remove the ships from the 'source' fleet
                    cursor.execute(" UPDATE fleets_ships SET quantity=quantity-%s WHERE fleetid=%s AND shipid=%s", [quantity, fleetid, shipid])
            cursor.execute("DELETE FROM fleets WHERE ownerid=%s AND size=0", [gcontext['exile_user'].id])
            return HttpResponseRedirect(reverse('exile:fleet')+"?id="+str(newfleetid))
    def ExecuteOrder(fleetid):
        if request.POST.get("split","") == "1":
            return SplitFleet(fleetid)
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'fleets'
    e_no_error = 0
    e_bad_name = 1
    e_already_exists = 2
    e_occupied = 3
    e_limit_reached = 4
    fleet_split_error = e_no_error
    try:
        fleetid = int(request.GET.get("id", "0"))
    except (KeyError, Exception):
        fleetid = 0
    if not fleetid:
        return HttpResponseRedirect(reverse('exile:fleets'))
    r = ExecuteOrder(fleetid)
    if r:
        return r
    r = DisplayExchangeForm(fleetid)
    if r:
        return r
    gcontext['menu'] = menu(request)
    context = gcontext
    if gcontext['exile_user'].privilege > 100:
        t = loader.get_template('exile/fleet-split_old.html')
        # à regarder !!!
        #t = loader.get_template('exile/fleet-split.html')
    else:
        t = loader.get_template('exile/fleet-split_old.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def fleetships(request):
    # display fleet info
    def DisplayFleet(fleetid):
        # retrieve fleet name, size, position, destination
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, attackonsight, engaged, size, signature, speed, remaining_time, commanderid, commandername," +
                " planetid, planet_name, planet_galaxy, planet_sector, planet_planet, planet_ownerid, planet_owner_name, planet_owner_relation," +
                " cargo_capacity, cargo_ore, cargo_hydrocarbon, cargo_scientists, cargo_soldiers, cargo_workers" +
                " FROM vw_fleets WHERE ownerid=%s AND id=%s", [gcontext['exile_user'].id,fleetid])
            re = cursor.fetchone()
            # if fleet doesn't exist, redirect to the list of fleets
            if not re:
                return HttpResponseRedirect(reverse('exile:fleets'))
            # if fleet is moving or engaged, go back to the fleets
            if re[7] or re[3]:
                return HttpResponseRedirect(reverse('exile:fleet')+'?id='+str(fleetid))
            gcontext["fleetid"] = fleetid
            gcontext["fleetname"] = re[1]
            gcontext["size"] = re[4]
            gcontext["speed"] = re[6]
            gcontext["fleet_capacity"] = re[18]
            gcontext["fleet_load"] = re[19] + re[20] + re[21] + re[22] + re[23]
            shipCount = 0
            gcontext["shiplist"] = {}
            if re[17] == config.rSelf:
                # retrieve the list of ships in the fleet
                cursor.execute("SELECT db_ships.id, db_ships.capacity," +
                    "COALESCE((SELECT quantity FROM fleets_ships WHERE fleetid=%s AND shipid = db_ships.id), 0)," +
                    "COALESCE((SELECT quantity FROM planet_ships WHERE planetid=(SELECT planetid FROM fleets WHERE id=%s) AND shipid = db_ships.id), 0)" +
                    " FROM db_ships" +
                    " ORDER BY db_ships.category, db_ships.label", [fleetid, fleetid])
                res = cursor.fetchall()
                gcontext['ship'] = {}
                for re in res:
                    if re[2] > 0 or re[3] > 0:
                        shipCount += 1
                        ship = {
                            "id": re[0],
                            "name": getShipLabel(re[0]),
                            "cargo_capacity": re[1],
                            "quantity": re[2],
                            "available": re[3],
                        }
                        gcontext['ship'][re[0]] = ship.copy()
                gcontext["shiplist"]["can_manage"] = True
            return False
    # Transfer ships between the planet and the fleet
    def TransferShips(fleetid):
        ShipsRemoved = 0
        with connection.cursor() as cursor:
        # if units are removed, the fleet may be destroyed so retrieve the planetid where the fleet is
            cursor.execute("SELECT planetid FROM fleets WHERE id=%s", [fleetid])
            re = cursor.fetchone()
            if not re:
                fleet_planet = -1
            else:
                fleet_planet = re[0]
            # retrieve the list of all existing ships
            shipsArray = retrieveShipsCache()
            # for each ship id, check if the player wants to add ships of this kind
            for i in shipsArray:
                shipid = i[0]
                try:
                    quantity = int(request.POST.get("addship" + str(shipid), '0'))
                except (KeyError, Exception):
                    quantity = 0
                if quantity > 0:
                    #print("SELECT sp_transfer_ships_to_fleet("+str(gcontext['exile_user'].id)+", "+str(fleetid)+", "+str(shipid)+", "+str(quantity)+")")
                    cursor.execute("SELECT sp_transfer_ships_to_fleet(%s, %s, %s, %s)", [gcontext['exile_user'].id, fleetid, shipid, quantity])
            # for each ship id, check if the player wants to remove ships of this kind
            for i in shipsArray:
                shipid = i[0]
                try:
                    quantity = int(request.POST.get("removeship" + str(shipid), '0'))
                except (KeyError, Exception):
                    quantity = 0
                if quantity > 0:
                    ShipsRemoved += quantity
                    #print("SELECT sp_transfer_ships_to_planet("+str(gcontext['exile_user'].id)+", "+str(fleetid)+", "+str(shipid)+", "+str(quantity)+")")
                    cursor.execute("SELECT sp_transfer_ships_to_planet(%s, %s, %s, %s)", [gcontext['exile_user'].id, fleetid, shipid, quantity])
            if ShipsRemoved > 0:
                cursor.execute("SELECT id FROM fleets WHERE id=%s", [fleetid])
                re = cursor.fetchone()
                if not re:
                    if fleet_planet > 0:
                        return HttpResponseRedirect(reverse('exile:orbit')+'?planet='+str(fleet_planet))
                    else:
                        return HttpResponseRedirect(reverse('exile:fleets'))
            return False
    def ExecuteOrder(fleetid):
        if request.POST.get("transfer_ships","0") == "1":
            return TransferShips(fleetid)
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'fleets_fleets'
    gcontext['menu'] = menu(request)
    e_no_error = 0
    e_bad_destination = 1
    fleet_error = e_no_error
    fleetid = request.GET.get("id")
    if not fleetid or not fleetid.isdigit():
        return HttpResponseRedirect(reverse('exile:fleets'))
    fleetid = int(fleetid)
    r = ExecuteOrder(fleetid)
    if r:
        return r
    r = DisplayFleet(fleetid)
    if r:
        return r
    context = gcontext
    t = loader.get_template('exile/fleet-ships.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def fleet(request):
    def RetrieveFleetOwnerId(fleetid):
        # retrieve fleet owner
        with connection.cursor() as cursor:
            cursor.execute("SELECT ownerid" +
                " FROM vw_fleets as f" +
                " WHERE (ownerid=%s OR (shared AND owner_alliance_id=%s))" +
                " AND id=%s AND (SELECT privilege FROM users WHERE users.id = f.ownerid) = 0", [gcontext['exile_user'].id, gcontext['can_command_alliance_fleets'], fleetid])
            res = cursor.fetchone()
            if res:
                gcontext['fleet_owner_id'] = res[0]
    # display fleet info
    def DisplayFleet(fleetid):
        # retrieve fleet name, size, position, destination
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, attackonsight, engaged, size, signature, speed, remaining_time, commanderid, commandername," + # 0 1 2 3 4 5 6 7 8 9
                " planetid, planet_name, planet_galaxy, planet_sector, planet_planet, planet_ownerid, planet_owner_name, planet_owner_relation," + # 10 11 12 13 14 15 16 17
                " destplanetid, destplanet_name, destplanet_galaxy, destplanet_sector, destplanet_planet, destplanet_ownerid, destplanet_owner_name, destplanet_owner_relation," + # 18 19 20 21 22 23 24 25
                " cargo_capacity, cargo_ore, cargo_hydrocarbon, cargo_scientists, cargo_soldiers, cargo_workers," + # 26 27 28 29 30 31
                " recycler_output, orbit_ore > 0 OR orbit_hydrocarbon > 0, action, total_time, idle_time, date_part('epoch', const_interval_before_invasion())," + # 32 33 34 35 36 37
                " long_distance_capacity, droppods, warp_to,"+ # 38 39 40
                    "( SELECT int4(COALESCE(max(nav_planet.radar_strength), 0))" +
                    " FROM nav_planet" +
                    " WHERE nav_planet.galaxy = f.planet_galaxy AND nav_planet.sector = f.planet_sector AND nav_planet.ownerid IS NOT NULL" +
                    " AND EXISTS ( SELECT 1 FROM vw_friends_radars WHERE vw_friends_radars.friend = nav_planet.ownerid AND vw_friends_radars.userid = %s)) AS from_radarstrength, " + # 41
                    "( SELECT int4(COALESCE(max(nav_planet.radar_strength), 0))" +
                    " FROM nav_planet" +
                    " WHERE nav_planet.galaxy = f.destplanet_galaxy AND nav_planet.sector = f.destplanet_sector AND nav_planet.ownerid IS NOT NULL" +
                    " AND EXISTS ( SELECT 1 FROM vw_friends_radars WHERE vw_friends_radars.friend = nav_planet.ownerid AND vw_friends_radars.userid = %s)) AS to_radarstrength," + # 42
                " firepower > 0, next_waypointid, (SELECT routeid FROM routes_waypoints WHERE id=f.next_waypointid), now(), spawn_ore + spawn_hydrocarbon," + # 43 44 45 46 47
                " radar_jamming, planet_floor, real_signature, required_vortex_strength, upkeep," + # 48 49 50 51 52
                " CASE WHEN planet_owner_relation IN (-1,-2) THEN const_upkeep_ships_in_position() ELSE const_upkeep_ships() END AS upkeep_multiplicator," + # 53
                " ((sp_commander_fleet_bonus_efficiency(size::bigint - leadership, 2.0)-1.0)*100)::integer AS commander_efficiency, leadership, ownerid, shared," + # 54 55 56 57
                " (SELECT prestige_points >= sp_get_prestige_cost_for_new_planet(planets) FROM users WHERE id=ownerid) AS can_take_planet," + # 58
                " (SELECT sp_get_prestige_cost_for_new_planet(planets) FROM users WHERE id=ownerid) AS prestige_cost" + # 59
                " FROM vw_fleets as f" +
                " WHERE ownerid=%s AND id=%s", [gcontext['exile_user'].id, gcontext['exile_user'].id, gcontext['fleet_owner_id'], fleetid])
            res = cursor.fetchone()
            # if fleet doesnt exist, redirect to the last known planet orbit or display the fleets list
            if not res:
                return HttpResponseRedirect(reverse('exile:fleets'))
            if gcontext['fleet_owner_id'] == gcontext['exile_user'].id:
                gcontext['CurrentFleet'] = fleetid
                request.session['CurrentFleet'] = fleetid
            gcontext['overview'] = {
                'actions':{'action':{}},
                'shiplist':{},
                "fleet_leadership": res[55],
                "fleet_commander_efficiency": res[54],
                "fleet_signature": res[5],
                "fleet_real_signature": res[50],
                "fleet_upkeep": res[52],
            	"fleet_upkeep_multiplicator": res[53],
            	"fleet_long_distance_capacity": res[38],
            	"fleet_required_vortex_strength": res[51],
            	"fleet_droppods": res[39],
            	"fleet_ore": res[27],
            	"fleet_hydrocarbon": res[28],
            	"fleet_scientists": res[29],
            	"fleet_soldiers": res[30],
            	"fleet_workers": res[31],
            	"fleet_load": res[27] + res[28] + res[29] + res[30] + res[31],
            	"fleet_capacity": res[26],
            	"fleetid": fleetid,
            	"fleetname": res[1],
            	"fleet_size": res[4],
            	"fleet_speed": res[6],
            	"recycler_output": res[32],
            }
            if res[39] <= 0:
                gcontext['overview']["hide_droppods"] = True
            if res[38] < res[50]:
                gcontext['overview']["insufficient_long_distance_capacity"] = True
            if res[26] <= 0:
                gcontext['overview']["hide_cargo"] = True
                gcontext['hide_cargo'] = True
            if gcontext['exile_user'].alliance_id:
                if res[57]:
                    gcontext['overview']['shared'] = True
                else:
                    gcontext['overview']['not_shared'] = True
                gcontext['overview']['actions']['action']["shareable"] = True
            if res[32] <= 0:
                gcontext['overview']["hide_recycling"] = True
            # Assign remaining time
            if res[7]:
                gcontext['overview']["time"] = res[7]
            else:
                gcontext['overview']["time"] = 0
            # display the fleet stance
            if res[2]:
                gcontext['overview']["attack"] = True
            else:
                gcontext['overview']["defend"] = True
            # if the fleet can be set to attack (firepower > 0)
            if res[43]:
                gcontext['overview']["setstance"] = {}
                if res[2]:
                    gcontext['overview']["setstance"]["defend"] = True
                else:
                    gcontext['overview']["setstance"]["attack"] = True
            else:
                gcontext['overview']["cant_setstance"] = True
            if res[45]:
                cursor.execute("SELECT routes_waypoints.id, action, p.id, p.galaxy, p.sector, p.planet, p.name, sp_get_user(p.ownerid), sp_relation(p.ownerid,%s)," +
                        " routes_waypoints.ore, routes_waypoints.hydrocarbon" +
                        " FROM routes_waypoints" +
                        "   LEFT JOIN nav_planet AS p ON (routes_waypoints.planetid=p.id)" +
                        " WHERE routeid=%s AND routes_waypoints.id >= %s" +
                        " ORDER BY routes_waypoints.id", [gcontext['exile_user'].id, res[45], res[44]])
                res2 = cursor.fetchall()
                waypointscount = 0
                for re in res2:
                    wp = {'fake':True}
                    if re[2]:
                        wp = {
                            "planetid": re[2],
                            "g": re[3],
                            "s": re[4],
                            "p": re[5],
                            "relation": re[8],
                        }
                        if re[8] >= config.rAlliance:
                            wp["planetname"] = re[6]
                        elif re[8] >= config.rUninhabited:
                            wp["planetname"] = re[7]
                        else:
                            wp["planetname"] = ""
                    if re[1] == 0:
                        if re[9] > 0:
                            if not "loadall" in gcontext['overview']['actions']['action']:
                                gcontext['overview']['actions']['action']["loadall"] = {}
                            gcontext['overview']['actions']['action']["loadall"][waypointscount] = wp.copy()
                        else:
                            if not "unloadall" in gcontext['overview']['actions']['action']:
                                gcontext['overview']['actions']['action']["unloadall"] = {}
                            gcontext['overview']['actions']['action']["unloadall"][waypointscount] = wp.copy()
                    elif re[1] == 1:
                            if not "move" in gcontext['overview']['actions']['action']:
                                gcontext['overview']['actions']['action']["move"] = {}
                            gcontext['overview']['actions']['action']["move"][waypointscount] = wp.copy()
                    elif re[1] ==  2:
                            if not "recycle" in gcontext['overview']['actions']['action']:
                                gcontext['overview']['actions']['action']["recycle"] = {}
                            gcontext['overview']['actions']['action']["recycle"][waypointscount] = wp.copy()
                    elif re[1] == 4:
                            if not "wait" in gcontext['overview']['actions']['action']:
                                gcontext['overview']['actions']['action']["wait"] = {}
                            gcontext['overview']['actions']['action']["wait"][waypointscount] = wp.copy()
                    elif re[1] == 5:
                            if not "invade" in gcontext['overview']['actions']['action']:
                                gcontext['overview']['actions']['action']["invade"] = {}
                            gcontext['overview']['actions']['action']["invade"][waypointscount] = wp.copy()
                    waypointscount += 1
            # list commmanders
            cursor.execute(" SELECT c.id, c.name, c.fleetname, c.planetname, fleets.id AS available" +
                    " FROM vw_commanders AS c" +
                    "   LEFT JOIN fleets ON (c.fleetid=fleets.id AND c.ownerid=fleets.ownerid AND NOT engaged AND action=0)" +
                    " WHERE c.ownerid=%s" +
                    " ORDER BY c.fleetid IS NOT NULL, c.planetid IS NOT NULL, c.fleetid, c.planetid ", [gcontext['fleet_owner_id']])
            res2 = cursor.fetchall()
            gcontext['overview']['optgroup'] = {'none':{},'planet':{},'fleet':{}}
            for re in res2:
                if not re[2]:
                    if not re[3]:
                        item = "none"
                    else:
                        item = "planet"
                else:
                    item = "fleet"
                # check if the commander is the commander of the fleet we display
                cmd = {
                    "cmd_id": re[0],
                    "cmd_name": re[1],
                    "option": {}
                }
                if res[8] == re[0]:
                    cmd['option']["selected"] = True
                if item == "planet":
                    cmd["name"] = re[3]
                    cmd['option']["assigned"] = True
                elif item == "fleet":
                    cmd["name"] = re[2]
                    if re[4]:
                        cmd['option']["assigned"] = True
                    else:
                        cmd['option']["unavailable"] = True
                gcontext['overview']['optgroup'][item][re[0]] = cmd.copy()
            if not res[8]:
                # display "no commander" or "fire commander" in the combobox of commanders
                gcontext['overview']["none"] = True
                gcontext['overview']["nocommander"] = True
            else:
                gcontext['overview']["unassign"] = True
                gcontext['overview']["commander"] = res[9]
            # display fleets that are near the same planet as this fleet
            # it allows to switch between the fleets and merge them quickly
            fleetCount = 0
            gcontext['fleets'] = {'playerfleet':{},'fleet':{'enemy':{},'ally':{}}}
            if res[34] != -1:
                cursor.execute("SELECT vw_fleets.id, vw_fleets.name, size, signature, speed, cargo_capacity-cargo_free, cargo_capacity, action, ownerid, owner_name, alliances.tag, sp_relation(%s,ownerid)" +
                        " FROM vw_fleets" +
                        "   LEFT JOIN alliances ON alliances.id=owner_alliance_id" +
                        " WHERE planetid=%s AND vw_fleets.id != %s AND NOT engaged AND action != 1 AND action != -1" +
                        " ORDER BY upper(vw_fleets.name)", [gcontext['exile_user'].id, res[10], res[0]])
                res2 = cursor.fetchall()
                for re in res2:
                    fleet = {
                        "id": re[0],
                        "name": re[1],
                        "size": re[2],
                        "speed": re[4],
                        "cargo_load": re[5],
                        "cargo_capacity": re[6],
                    }
                    # res[48] radar_jamming of planet
                    if res[17] > config.rFriend or re[11] > config.rFriend or res[48] == 0 or res[41] > res[48]:
                        fleet["signature"] = re[3]
                    else:
                        fleet["signature"] = 0
                    if re[8] == gcontext['exile_user'].id:
                        if res[34] == 0 and re[7] == 0:
                            fleet["merge"] = True
                        gcontext['fleets']["playerfleet"][re[0]] = fleet.copy()
                    else:
                        fleet["owner"] = re[9]
                        if re[10]:
                            fleet["tag"] = re[10]
                        if re[11] == 1:
                            gcontext['fleets']['fleet']["ally"][re[0]] = fleet.copy()
                        elif re[11] == 0:
                            gcontext['fleets']['fleet']["friend"][re[0]] = fleet.copy()
                        elif re[11] == -1:
                            if res[34] != 1:
                                gcontext['fleets']['fleet']["enemy"][re[0]] = fleet.copy()
                    fleetCount += 1
            if fleetCount == 0:
                gcontext['fleets']["nofleets"] =True
            # assign fleet current planet
            gcontext['overview']["planetid"] = res[10]
            gcontext['overview']["g"] = res[12]
            gcontext['overview']["s"] = res[13]
            gcontext['overview']["p"] = res[14]
            gcontext['overview']["relation"] = res[17]
            gcontext['overview']["planetname"] = getPlanetName(request,res[17], res[41], res[16], res[11])
        #   if res[17] < rAlliance and not IsNull(res[16]):
        #       if res[41] > 0 or res[17] = rFriend:
        #           content.AssignValue "planetname", res[16]
        #       else
        #           content.AssignValue "planetname", ""
        #       end if
        #   else
        #       content.AssignValue "planetname", res[11]
        #   end if
            if res[34] == -1 or res[34] == 1: # fleet is moving when dest_planetid is not null
                # Assign destination planet
                gcontext['overview']["t_planetid"] = res[18]
                gcontext['overview']["t_g"] = res[20]
                gcontext['overview']["t_s"] = res[21]
                gcontext['overview']["t_p"] = res[22]
                gcontext['overview']["t_relation"] = res[25]
                gcontext['overview']["t_planetname"] = getPlanetName(request,res[25], res[42], res[24], res[19])
        #       if res[25] < rAlliance and not IsNull(res[24]):
        #           if res[42] > 0 or res[25] = rFriend:
        #               content.AssignValue "t_planetname", res[24]
        #           else
        #               content.AssignValue "t_planetname", ""
        #           end if
        #       else
        #           content.AssignValue "t_planetname", res[19]
        #       end if
                
                # display Cancel Move orders if fleet has covered less than 100 units of distance, or during 2 minutes
                # and if from_planet is not null
                timelimit = int(100/res[6]*3600)
                if timelimit < 120:
                    timelimit = 120
                if not res[3] and res[35]-res[7] < timelimit and res[10]:
                    gcontext['overview']["timelimit"] = timelimit-(res[35]-res[7])
                    gcontext['overview']["cancel_moving"] = True
                if res[10]:
                    gcontext['overview']['moving'] = {"from": True}
                can_install_building = False
            else:
                if res[3]: #if is engaged
                    gcontext['overview']["fighting"] = True
                elif res[34] == 2:
                    gcontext['overview']["recycling"] = True
                elif res[34] == 4:
                    gcontext['overview']["waiting"] = True
                else:
                    if res[40]:
                        gcontext['overview']["warp"] = True
                    if res[32] == 0 or (not res[33] and res[47] == 0): # if no recycler or nothing to recycle
                        gcontext['overview']["cant_recycle"] = True
                    else:
                        gcontext['overview']["recycle"] = True
                    can_install_building = (not res[15] or (res[17] >= config.rHostile)) and not res[40]
                    # assign buildings that can be installed
                    # only possible if not moving, not engaged, planet is owned by self or by nobody and is not a vortex
                    if res[17] >= config.rFriend:
                        gcontext['overview']["unloadcargo"] = True
                    if res[17] == config.rSelf and res[49] > 0:
                        gcontext['overview']["loadcargo"] = True
                        gcontext['overview']["shiplist"]["manage"] = True
        #           if UserId = 1009:
        #               if res[17] = rSelf and false:
        #                   # retrieve planet ore, hydrocarbon, workers, relation
        #                   dim oPlanetRs
        #                   query = "SELECT ore, hydrocarbon, scientists, soldiers," +
        #                           " GREATEST(0, workers-GREATEST(workers_busy,workers_for_maintenance-workers_for_maintenance/2+1,500))," +
        #                           " workers > workers_for_maintenance/2" +
        #                           " FROM vw_planets WHERE id="&res[10]
        #                   set oPlanetRs = oConn.Execute(query)
        #                   content.AssignValue "planet_ore", res[0]
        #                   content.AssignValue "planet_hydrocarbon", res[1]
        #                   content.AssignValue "planet_scientists", res[2]
        #                   content.AssignValue "planet_soldiers", res[3]
        #                   content.AssignValue "planet_workers", res[4]
        #               end if
        #           end if
                    if res[34] == 0 and res[4] > 1 and res[56] == gcontext['exile_user'].id:
                        gcontext['overview']["split"] = True
                        gcontext['overview']["shiplist"]["split"] = True
                    if res[15] and res[17] < config.rFriend and res[30] > 0:
                        # fleet has to wait some time (defined in DB) before being able to invade
                        # res[37] is the value returned by const_seconds_before_invasion() from DB
                        if res[36] < res[37]:
                            t = res[37] - res[36]
                        else:
                            t = 0
                        gcontext['overview']["invade_time"] = t
                        if res[39] == 0:
                            gcontext['overview']["cant_invade"] = True
                        else:
                            if res["can_take_planet"]:
                                gcontext['overview']["prestige"] = res[59]
                                gcontext['overview']["invade"] = {"can_take":True}
                    else:
                        gcontext['overview']["cant_invade"] = True
                    if res[34] == 0:
                        gcontext['overview']["patrolling"] = True # standing by/patrolling
                        gcontext['overview']["idle"] = True
                # Fleet idling
                if res[34] == 0:
                    if gcontext['move_fleet_result'] != "":
                        gcontext['move_fleet'] = {'result':{gcontext['move_fleet_result']:True}}
                    else:
                        gcontext['move_fleet'] = {}
                    # populate destination list, there are 2 groups : planets and fleets
                    # retrieve planet list
                    hasAPlanetSelected = False
                    gcontext['move_fleet']['planetgroup'] = {'location':{}}
                    cpt = 0
                    for i in checkPlanetListCache(request,True): #request.session.get('sPlanetList'):
                        pla = {
                            "index": cpt,
                            "name": i[1],
                            "to_g": i[2],
                            "to_s": i[3],
                            "to_p": i[4],
                        }
                        if i[0] == res[10]:
                            pla['selected'] = True
                            hasAPlanetSelected = True
                        gcontext['move_fleet']['planetgroup']['location'][cpt] = pla.copy()
                        cpt += 1
                    # list planets where we have fleets not on our planets
                    cursor.execute("SELECT DISTINCT ON (f.planetid) f.name, f.planetid, f.planet_galaxy, f.planet_sector, f.planet_planet" +
                            " FROM vw_fleets AS f" +
                            "    LEFT JOIN nav_planet AS p ON (f.planetid=p.id)" +
                            " WHERE f.ownerid=%s AND p.ownerid IS DISTINCT FROM %s AND f.action <> 1" + # cacher les flottes en mouvement
                            " ORDER BY f.planetid" +
                            " LIMIT 200", [gcontext['exile_user'].id, gcontext['exile_user'].id])
                    res2 = cursor.fetchall()
                    gcontext['move_fleet']['fleetgroup'] = {'location':{}}
                    for re in res2:
                        pla = {
                            "index": cpt,
                            "fleet_name": re[0],
                            "to_g": re[2],
                            "to_s": re[3],
                            "to_p": re[4],
                        }
                        if re[1] == res[10] and not hasAPlanetSelected:
                            pla['selected'] = True
                        gcontext['move_fleet']['fleetgroup']['location'][cpt] = pla.copy()
                        cpt += 1
                    # list merchant planets in the galaxy of the fleet
                    query = " SELECT id, galaxy, sector, planet FROM nav_planet WHERE ownerid=3"
                    if res[12]:
                        query += " AND galaxy=" + str(res[12])
                    query += " ORDER BY id"
                    cursor.execute(query)
                    res2 = cursor.fetchall()
                    gcontext['move_fleet']['merchantplanetsgroup'] = {'location':{}}
                    for re in res2:
                        pla = {
                            "index": cpt,
                            "to_g": re[1],
                            "to_s": re[2],
                            "to_p": re[3],
                        }
                        if re[0] == res[10] and not hasAPlanetSelected:
                            pla['selected'] = True
                        gcontext['move_fleet']['merchantplanetsgroup']['location'][cpt] = pla.copy()
                        cpt += 1
                    if gcontext['exile_user'].privilege > 100:
                        # list routes
                        cursor.execute("SELECT id, name, repeat FROM routes WHERE ownerid=%s", [gcontext['exile_user'].id])
                        res2 = cursor.fetchall()
                        gcontext['overview']['route'] = {'itemm':{}}
                        if not res2:
                            gcontext['overview']['route']["none"] = True
                        for re in res2:
                            route = {
                                "route_id": re[0],
                                "route_name": re[1],
                            }
                            if re[0] == res[45]:
                                route["selected"] = True
                            gcontext['overview']['route']["itemm"][re[0]] = route.copy()
                        gcontext['overview']['route']["idle"] = True
            # display action error
            if gcontext['action_result'] != "":
                gcontext['overview'][action_result] = True
            if res[15]:
                planet_ownerid = res[15]
            else:
                planet_ownerid = gcontext['exile_user'].id
            # display header
            if res[34] == 0 and res[15] == gcontext['exile_user'].id:
                gcontext['CurrentPlanet'] = res[10]
                gcontext['contextinfo'] = header(request)
            else:
                FillHeaderCredits(request)
            # display the list of ships in the fleet
            cursor.execute("SELECT db_ships.id, fleets_ships.quantity," +
                    " signature, capacity, handling, speed, weapon_turrets, weapon_dmg_em+weapon_dmg_explosive+weapon_dmg_kinetic+weapon_dmg_thermal AS weapon_power, weapon_tracking_speed, hull, shield, recycler_output, long_distance_capacity, droppods," +
                    " buildingid, sp_can_build_on(%s, db_ships.buildingid,%s)=0 AS can_build" +
                    " FROM fleets_ships" +
                    "   LEFT JOIN db_ships ON (fleets_ships.shipid = db_ships.id)" +
                    " WHERE fleetid=%s" +
                    " ORDER BY db_ships.category, db_ships.label", [res[10], planet_ownerid, fleetid])
            res = cursor.fetchall()
            shipCount = 0
            gcontext['shiplist'] = {}
            for re in res:
                shipCount += 1
                ship = {
                    "id": re[0],
                    "quantity": re[1],
                    "name": getShipLabel(re[0]),
                    "description": getShipDescription(re[0]),
                    "ship_signature": re[2],
                    "ship_cargo": re[3],
                    "ship_handling": re[4],
                    "ship_speed": re[5],
                    "ship_turrets": re[6],
                    "ship_power": re[7],
                    "ship_tracking_speed": re[8],
                    "ship_hull": re[9],
                    "ship_shield": re[10],
                    "ship_recycler_output": re[11],
                    "ship_long_distance_capacity": re[12],
                    "ship_droppods": re[13],
                }
                if re[14]:
                    if can_install_building and re[15]:
                        ship["install"] = True
                    else:
                        ship["cant_install"] = True
                gcontext['shiplist'][re[0]] = ship.copy()
    def InstallBuilding(fleetid, shipid):
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_start_ship_building_installation(%s, %s, %s)", [gcontext['fleet_owner_id'], fleetid, shipid])
            res = cursor.fetchone()
            if not res:
                return
            if res[0] >= 0:
                # set as the new planet in case it has been colonized, the player expects to see its new planet after colonization
                #SetCurrentPlanet(res[0])
                # invalidate planet list to reload it in case a planet has been colonized
                #InvalidatePlanetList()
                checkPlanetListCache(request, True)
                return HttpResponseRedirect(reverse('exile:planet') + '?planet='+ str(res[0]))
            elif res[0] == -7:
                gcontext['action_result'] = "error_max_planets_reached"
            elif res[0] == -8:
                gcontext['action_result'] = "error_deploy_enemy_ships"
            elif res[0] == -11:
                gcontext['action_result'] = "error_deploy_too_many_safe_planets"
    def MoveFleet(fleetid,pid=0):
        if not pid:
            try:
                g = int(request.POST.get("g",-1))
            except (KeyError, Exception):
                g = -1
            try:
                s = int(request.POST.get("s",-1))
            except (KeyError, Exception):
                s = -1
            try:
                p = int(request.POST.get("p",-1))
            except (KeyError, Exception):
                p = -1
        else:
            planet = NavPlanet.objects.get(pk=pid)
            if planet:
                g = planet.galaxy_id
                s = planet.sector
                p = planet.planet
            else:
                return HttpResponse('KO')
        if g==-1 or s==-1 or p==-1:
            gcontext['move_fleet_result'] = "bad_destination"
            return
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_move_fleet(%s, %s, %s, %s, %s)", [gcontext['fleet_owner_id'], fleetid, g, s, p])
            res = cursor.fetchone()
            if pid:
                return HttpResponse('OK')
            if res:
                if res[0] == 0:
                    if request.POST.get("movetype", "0") == "1":
                        cursor.execute("UPDATE fleets SET next_waypointid = sp_create_route_unload_move(planetid) WHERE ownerid=%s AND id=%s", [gcontext['fleet_owner_id'], fleetid])
                    elif request.POST.get("movetype", "0") ==  "2":
                        cursor.execute("UPDATE fleets SET next_waypointid = sp_create_route_recycle_move(planetid) WHERE ownerid=%s AND id=%s", [gcontext['fleet_owner_id'], fleetid])
            else:
                res[0] = 0
            if res[0] == 0:
                gcontext['move_fleet_result'] = "ok"
            elif res[0] == -1: # fleet not found or busy
                log_notice(request, "fleet", "Move: cant move fleet", 0)
            elif res[0] == -4: # new player or holidays protection
                gcontext['move_fleet_result'] = "new_player_protection"
            elif res[0] == -5: # long travel not possible
                gcontext['move_fleet_result'] = "long_travel_impossible"
            elif res[0] == -6: # not enough money
                gcontext['move_fleet_result'] = "not_enough_credits"
            elif res[0] == -7:
                gcontext['move_fleet_result'] = "error_jump_from_require_empty_location"
            elif res[0] == -8:
                gcontext['move_fleet_result'] = "error_jump_protected_galaxy"
            elif res[0] == -9:
                gcontext['move_fleet_result'] = "error_jump_to_require_empty_location"
            elif res[0] == -10:
                gcontext['move_fleet_result'] = "error_jump_to_same_point_limit_reached"
    def Invade(fleetid, droppods, take):
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_invade_planet(%s, %s, %s)", [gcontext['fleet_owner_id'], fleetid, droppods])
            res = cursor.fetchone()
            if res[0] == -1:
                gcontext['action_result'] = "error_soldiers"
            elif res[0] == -2:
                gcontext['action_result'] = "error_fleet"
            elif res[0] == -3:
                gcontext['action_result'] = "error_planet"
            elif res[0] == -5:
                gcontext['action_result'] = "error_invade_enemy_ships"
            if res[0] > 0:
                #InvalidatePlanetList()
                checkPlanetListCache(request, True)
                return HttpResponseRedirect(reverse('exile:invasion') + '?id=' + str(res[0]) + '&fleetid=' + str(fleetid))
            return False
    def ExecuteOrder(fleetid):
        action = request.POST.get('action',request.GET.get('action', ''))
        if action == "invade":
            try:
                droppods = int(request.POST.get("droppods", 0))
            except (KeyError, Exception):
                droppods = 0
            return Invade(fleetid, droppods, request.POST.get("take", "") != "")
        elif action == "rename":
            fleetname = request.POST.get("newname", "").strip()
            if isValidName(fleetname):
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE fleets SET name=%s WHERE action=0 AND not engaged AND ownerid=%s AND id=%s", [fleetname, gcontext['exile_user'].id, fleetid])
        elif action == "assigncommander":
            try:
                commanderid = int(request.POST.get('commander', 0))
            except (KeyError, Exception):
                commanderid = 0
            if commanderid != 0:
                # assign new commander
                with connection.cursor() as cursor:
                    cursor.execute("SELECT sp_commanders_assign(%s, %s, null, %s)", [gcontext['fleet_owner_id'], commanderid, fleetid])
            else:
                # unassign current fleet commander
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE fleets SET commanderid=NULL WHERE ownerid=%s AND id=%s", [gcontext['fleet_owner_id'], fleetid])
                    cursor.execute("SELECT sp_update_fleet_bonus(%s)", [fleetid])
        elif action == "move":
            loop = request.POST.get('loop', '0')
            if loop != "0":
                log_notice(request, "fleet", "Move: parameter missing", 1)
                with connection['exile_nexus'].cursor() as cursor:
                    cursor.execute("UPDATE nusers SET cheat_detected=now() WHERE id=%s", [gcontext['user'].id])
            MoveFleet(fleetid)
        elif action == "move2":
            return MoveFleet(fleetid,request.GET.get('pid', '0'))
        elif action == "share":
            with connection.cursor() as cursor:
                cursor.execute("UPDATE fleets SET shared=not shared WHERE ownerid=%s AND id=%s", [gcontext['fleet_owner_id'], fleetid])
        elif action == "abandon":
            #response.write "SELECT sp_abandon_fleet(" & UserId & "," & fleetid & ")"
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_abandon_fleet(%s, %s)", [gcontext['exile_user'].id, fleetid])
        elif action == "attack":
            with connection.cursor() as cursor:
                cursor.execute("UPDATE fleets SET attackonsight=firepower > 0 WHERE ownerid=%s AND id=%s", [gcontext['fleet_owner_id'], fleetid])
        elif action == "defend":
            with connection.cursor() as cursor:
                cursor.execute("UPDATE fleets SET attackonsight=false WHERE ownerid=%s AND id=%s", [gcontext['fleet_owner_id'], fleetid])
        elif action == "recycle":
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_start_recycling(%s, %s)", [gcontext['fleet_owner_id'], fleetid])
                res = cursor.fetchone()
                if res[0] == -2:
                    gcontext['action_result'] = "error_recycling"
        elif action == "stoprecycling":
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_cancel_recycling(%s, %s)", [gcontext['fleet_owner_id'], fleetid])
        elif action == "stopwaiting":
            with connection.cursor() as cursor:
                cursor.execute( "SELECT sp_cancel_waiting(%s ,%s)", [gcontext['fleet_owner_id'], fleetid])
        elif action == "merge":
            try:
                destfleetid = int(request.GET.get("with", 0))
            except (KeyError, Exception):
                destfleetid = 0
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_merge_fleets(%s, %s, %s)", [gcontext['exile_user'].id, fleetid, destfleetid])
        elif action == "return":
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_cancel_move(%s, %s)", [gcontext['fleet_owner_id'], fleetid])
        elif action == "install":
            try:
                shipid = int(request.GET.get("s", 0))
            except (KeyError, Exception):
                shipid = 0
            r = InstallBuilding(fleetid, shipid)
            if r:
                return r
        elif action == "warp":
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_warp_fleet(%s, %s)", [gcontext['fleet_owner_id'], fleetid])
        return False
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['action_result'] = ""
    gcontext['move_fleet_result'] = ""
    gcontext['can_command_alliance_fleets'] = -1
    if gcontext['exile_user'].alliance_id and hasRight(request,"can_order_other_fleets"):
        gcontext['can_command_alliance_fleets'] = gcontext['exile_user'].alliance_id
    gcontext['fleet_owner_id'] = gcontext['exile_user'].id
    gcontext['selectedmenu'] = 'fleets_fleets'
    gcontext['menu'] = menu(request)
    try:
        fleetid = int(request.GET.get("fleet", 0))
    except (KeyError, Exception):
        fleetid = 0
    if not fleetid:
        try:
            fleetid = int(request.GET.get("id", 0))
        except (KeyError, Exception):
            fleetid = 0
    try:
        trade = int(request.GET.get("trade", 0))
    except (KeyError, Exception):
        trade = 0
    if trade == 9:
        gcontext['action_result'] = "error_trade"
    if fleetid == 0:
        return HttpResponseRedirect(reverse('exile:orbit'))
    RetrieveFleetOwnerId(fleetid)
    r = ExecuteOrder(fleetid)
    if r:
        return r
    DisplayFleet(fleetid)
    fh = fleetheader(request)
    if fh:
        gcontext['contextinfo'] = fleetheader(request)
    context = gcontext
    t = loader.get_template('exile/fleet.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def invasion(request):
    def DisplayReport(invasionid, readerid):
        with connection.cursor() as cursor:
            cursor.execute("SELECT i.id, i.time, i.planet_id, i.planet_name, i.attacker_name, i.defender_name, " +
                "i.attacker_succeeded, i.soldiers_total, i.soldiers_lost, i.def_soldiers_total, " +
                "i.def_soldiers_lost, i.def_scientists_total, i.def_scientists_lost, i.def_workers_total, " +
                "i.def_workers_lost, galaxy, sector, planet, sp_get_user(%s) " +
                "FROM invasions AS i INNER JOIN nav_planet ON nav_planet.id = i.planet_id WHERE i.id = %s", [readerid, invasionid])
            re = cursor.fetchone()
            if not re:
                return HttpResponseRedirect(reverse('exile:reports'))
            viewername = re[18]
            # compare the attacker name and defender name with the name of who is reading this report
            if re[4] != viewername and re[5] != viewername and gcontext['exile_user'].alliance_id:
                # if we are not the attacker or defender, check if we can view this invasion as a member of our alliance of we are ambassador
                if hasRight(request,"can_see_reports"):
                    # find the name of the member that did this invasion, either the attacker or the defender
                    cursor.execute("SELECT login FROM users" +
                            " WHERE (login=%s OR login=%s) AND alliance_id=%s AND alliance_joined <= (SELECT time FROM invasions WHERE id=%s)",
                            [re[4], re[5], gcontext['exile_user'].alliance_id, invasionid])
                    re2 = cursor.fetchone()
                    if not re2:
                        return HttpResponseRedirect(reverse('exile:overview'))
                    viewername = re2[0]
                else:
                    return HttpResponseRedirect(reverse('exile:overview'))
            gcontext["reportplanetid"] = re[2]
            gcontext["planetname"] = re[3]
            gcontext["reportg"] = re[15]
            gcontext["reports"] = re[16]
            gcontext["reportp"] = re[17]
            gcontext["planet_owner"] = re[5]
            gcontext["fleet_owner"] = re[4]
            gcontext["date"] = re[1]
            gcontext["soldiers_total"] = re[7]
            gcontext["soldiers_lost"] = re[8]
            gcontext["soldiers_alive"] = re[7] - re[8]
            gcontext["def_soldiers_total"] = re[9]
            gcontext["def_soldiers_lost"] = re[10]
            gcontext["def_soldiers_alive"] = re[9] - re[10]
            def_total = re[9]
            def_losts = re[10]
            gcontext["invasion_report"] = {"report":{}}
            if re[4] == viewername: # we are the attacker
                gcontext["relation"] = config.rWar
                # display only troops encountered by the attacker's soldiers
                if re[9]-re[10] == 0:
                    # if no workers remain, display the scientists
                    if re[13]-re[14] == 0:
                        def_total = def_total + re[11]
                        def_losts = def_losts + re[12]
                        gcontext["def_scientists_total"] = re[11]
                        gcontext["def_scientists_lost"] = re[12]
                        gcontext["def_scientists_alive"] = re[11] - re[12]
                        gcontext["invasion_report"]["report"]["scientists"] = True
                    # if no soldiers remain, display the workers
                    def_total = def_total + re[13]
                    def_losts = def_losts + re[14]
                    gcontext["def_workers_total"] = re[13]
                    gcontext["def_workers_lost"] = re[14]
                    gcontext["def_workers_alive"] = re[13] - re[14]
                    gcontext["invasion_report"]["report"]["workers"] =True
                gcontext["planetname"] = re[5]
                gcontext["def_alive"] = def_total - def_losts
                gcontext["def_total"] = def_total
                gcontext["def_losts"] = def_losts
                gcontext["invasion_report"]["report"]["attacker"] = {"ally":True}
                gcontext["invasion_report"]["report"]["defender"] = {"enemy":True}
            else: # ...we are the defender
                gcontext["relation"] = config.rFriend
                def_total = def_total + re[11]
                def_losts = def_losts + re[12]
                gcontext["def_scientists_total"] = re[11]
                gcontext["def_scientists_lost"] = re[12]
                gcontext["def_scientists_alive"] = re[11] - re[12]
                gcontext["invasion_report"]["report"]["scientists"] =True
                def_total = def_total + re[13]
                def_losts = def_losts + re[14]
                gcontext["def_workers_total"] = re[13]
                gcontext["def_workers_lost"] = re[14]
                gcontext["def_workers_alive"] = re[13] - re[14]
                gcontext["invasion_report"]["report"]["workers"] =True
                gcontext["def_alive"] = def_total - def_losts
                gcontext["def_total"] = def_total
                gcontext["def_losts"] = def_losts
                gcontext["invasion_report"]["report"]["attacker"] = {"enemy":True}
                gcontext["invasion_report"]["report"]["defender"] = {"ally":True}
            if fleetid:
                # if a fleetid is specified, parse a link to redirect the user to the fleet
                gcontext["fleetid"] = fleetid
                gcontext["invasion_report"]["justdone"] = True
            if re[6]:
                gcontext["invasion_report"]["succeeded"] = True
            else:
                gcontext["invasion_report"]["not_succeeded"] = True
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'invasion'
    try:
        invasionid = int(request.GET.get("id", "0"))
    except (KeyError, Exception):
        invasionid = 0
    if not invasionid:
        return HttpResponseRedirect(reverse('exile:overview'))
    try:
        fleetid = int(request.GET.get("fleetid", "0"))
    except (KeyError, Exception):
        fleetid = 0
    #if not fleetid:
    #    return HttpResponseRedirect(reverse('exile:overview'))
    DisplayReport(invasionid, gcontext['exile_user'].id)
    gcontext['menu'] = menu(request)
    context = gcontext
    t = loader.get_template('exile/invasion.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def fleets(request):
    def DisplayFleetsPage():
        gcontext['master'] = {'category': {}}
        with connection.cursor() as cursor:
            cursor.execute('SELECT category, label' +
                ' FROM users_fleets_categories' +
                ' WHERE userid=%s' +
                ' ORDER BY upper(label)', [gcontext['exile_user'].id])
            res = cursor.fetchall()
            for re in res:
                gcontext['master']['category'][re[0]] = {
                    'id': re[0],
                    'label': re[1],
                }
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'fleets'
    gcontext['menu'] = menu(request)
    context = gcontext
    DisplayFleetsPage()
    t = loader.get_template('exile/fleets.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def fleetshandler(request):
    def GetFleetList():
        with connection.cursor() as cursor:
            cursor.execute('SELECT fleetid, fleets_ships.shipid, quantity' +
                ' FROM fleets' +
                ' INNER JOIN fleets_ships ON (fleets.id=fleets_ships.fleetid)' +
                ' WHERE ownerid=%s' +
                ' ORDER BY fleetid, fleets_ships.shipid', [gcontext['exile_user'].id])
            res = cursor.fetchall()
            if not res:
                ShipListCount = -1
            else:
                ShipListArray = res
                ShipListCount = len(res)
            cursor.execute('SELECT id, name, attackonsight, engaged, size, signature, speed, remaining_time, commanderid, commandername,' + # 0 1 2 3 4 5 6 7 8 9
                ' planetid, planet_name, planet_galaxy, planet_sector, planet_planet, planet_ownerid, planet_owner_name, planet_owner_relation,' + # 10 11 12 13 14 15 16 17
                ' destplanetid, destplanet_name, destplanet_galaxy, destplanet_sector, destplanet_planet, destplanet_ownerid, destplanet_owner_name, destplanet_owner_relation,' + # 18 19 20 21 22 23 24 25
                ' cargo_capacity, cargo_ore, cargo_hydrocarbon, cargo_scientists, cargo_soldiers, cargo_workers,' + # 26 27 28 29 30 31
                ' recycler_output, orbit_ore > 0 OR orbit_hydrocarbon > 0, action,' + # 32 33 34
                '( SELECT int4(COALESCE(max(nav_planet.radar_strength), 0)) FROM nav_planet WHERE nav_planet.galaxy = f.planet_galaxy AND nav_planet.sector = f.planet_sector AND nav_planet.ownerid IS NOT NULL AND EXISTS ( SELECT 1 FROM vw_friends_radars WHERE vw_friends_radars.friend = nav_planet.ownerid AND vw_friends_radars.userid = %(UserId)s)) AS from_radarstrength, ' + # 35
                '( SELECT int4(COALESCE(max(nav_planet.radar_strength), 0)) FROM nav_planet WHERE nav_planet.galaxy = f.destplanet_galaxy AND nav_planet.sector = f.destplanet_sector AND nav_planet.ownerid IS NOT NULL AND EXISTS ( SELECT 1 FROM vw_friends_radars WHERE vw_friends_radars.friend = nav_planet.ownerid AND vw_friends_radars.userid = %(UserId)s)) AS to_radarstrength,' + # 36
                ' categoryid' + # 37
                ' FROM vw_fleets as f WHERE ownerid = %(UserId)s', {'UserId': gcontext['exile_user'].id})
            res = cursor.fetchall()
            gcontext['list'] = {'fleet': {}}
            if not res:
                pass
            else:
                for re in res:
                    fleet = {}
                    fleet['ship'] = {}
                    fleet['resource'] = {1:{},2:{},3:{},4:{},5:{}}
                    fleet['id'] = re[0]
                    fleet['name'] = re[1]
                    fleet['category'] = re[37]
                    fleet['size'] = re[4]
                    fleet['signature'] = re[5]
                    fleet['cargo_load'] = re[27]+re[28]+re[29]+re[30]+re[31]
                    fleet['cargo_capacity'] = re[26]
                    fleet['cargo_ore'] = re[27]
                    fleet['cargo_hydrocarbon'] = re[28]
                    fleet['cargo_scientists'] = re[29]
                    fleet['cargo_soldiers'] = re[30]
                    fleet['cargo_workers'] = re[31]
                    fleet['commandername'] = re[9]
                    if not re[9]:
                        fleet['commandername'] = ''
                    fleet['action'] = abs(re[34])
                    if re[3]:
                        fleet['action'] = "x"
                    if re[2]:
                        fleet['stance'] = 1
                    else:
                        fleet['stance'] = 0
                    if re[7]:
                        fleet['time'] = re[7]
                    else:
                        fleet['time'] = 0
                    # Assign fleet current planet
                    fleet['planetid'] = 0
                    fleet['g'] = 0
                    fleet['s'] = 0
                    fleet['p'] = 0
                    fleet['relation'] = 0
                    fleet['planetname'] = ""
                    if re[10]:
                        fleet['planetid'] = re[10]
                        fleet['g'] = re[12]
                        fleet['s'] = re[13]
                        fleet['p'] = re[14]
                        fleet['relation'] = re[17]
                        fleet['planetname'] = getPlanetName(request,re[17], re[35], re[16], re[11])
                        if not fleet['planetname']:
                            fleet['planetname'] = re[16]
                    # Assign fleet destination planet
                    fleet['t_planetid'] = 0
                    fleet['t_g'] = 0
                    fleet['t_s'] = 0
                    fleet['t_p'] = 0
                    fleet['t_relation'] = 0
                    fleet['t_planetname'] = ""
                    if re[18]:
                        fleet['t_planetid'] = re[18]
                        fleet['t_g'] = re[20]
                        fleet['t_s'] = re[21]
                        fleet['t_p'] = re[22]
                        fleet['t_relation'] = re[25]
                        fleet['t_planetname'] = getPlanetName(request,re[25], re[36], re[24], re[19])
                    for i in range(0, ShipListCount):
                        if ShipListArray[i][0] == re[0]:
                            fleet['ship'][i] = {
                                'ship_label':getShipLabel(ShipListArray[i][1]),
                                'ship_quantity': ShipListArray[i][2],
                            }
                    fleet['resource'][1]['res_id'] = 1
                    fleet['resource'][1]['res_quantity'] = re[27]
                    fleet['resource'][2]['res_id'] = 2
                    fleet['resource'][2]['res_quantity'] = re[28]
                    fleet['resource'][3]['res_id'] = 3
                    fleet['resource'][3]['res_quantity'] = re[29]
                    fleet['resource'][4]['res_id'] = 4
                    fleet['resource'][4]['res_quantity'] = re[30]
                    fleet['resource'][5]['res_id'] = 5
                    fleet['resource'][5]['res_quantity'] = re[31]
                    gcontext['list']['fleet'][re[0]] = fleet.copy()
    global config
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    a = request.POST.get('a', request.GET.get('a', ''))
    if a == 'setcat':
        fleetid = request.POST.get('id', request.GET.get('id', ''))
        oldCat = request.POST.get('old', request.GET.get('old', ''))
        newCat = request.POST.get('new', request.GET.get('new', ''))
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_fleets_set_category(%s, %s, %s, %s)', [gcontext['exile_user'].id, fleetid, oldCat, newCat])
            res = cursor.fetchone()
            if res and res[0]:
                gcontext['id'] = fleetid
                gcontext['old'] = oldCat
                gcontext['new'] = newCat
                gcontext['fleet_category_changed'] = True
    elif a == 'newcat':
        name = request.POST.get('name', request.GET.get('name', ''))
        if isValidName(name):
            with connection.cursor() as cursor:
                cursor.execute('SELECT sp_fleets_categories_add(%s, %s)', [gcontext['exile_user'].id, name])
                res = cursor.fetchone()
                if res:
                    gcontext['id'] = res[0]
                    gcontext['label'] = name
                    gcontext['category'] = True
        else:
            gcontext['category_name_invalid'] = True
    elif a == "rencat":
        name = request.POST.get('name', request.GET.get('name', ''))
        catid = request.POST.get('id', request.GET.get('id', ''))
        if name == '':
            with connection.cursor() as cursor:
                cursor.execute('SELECT sp_fleets_categories_delete(%s, %s)', [gcontext['exile_user'].id, catid])
                res = cursor.fetchone()
                if res:
                    gcontext['id'] = catid
                    gcontext['label'] = name
                    gcontext['category'] = True
        elif isValidName(name):
            with connection.cursor() as cursor:
                cursor.execute('SELECT sp_fleets_categories_rename(%s, %s, %s)")', [gcontext['exile_user'].id, catid, name])
                res = cursor.fetchone()
                if res:
                    gcontext['id'] = catid
                    gcontext['label'] = name
                    gcontext['category'] = True
        else:
            gcontext['category_name_invalid'] = True
    elif a == "list":
        GetFleetList()
    return render(request, 'exile/fleets.html', context)

@construct
@logged
def fleetsorbiting(request):
    # list fleets not belonging to the player that are near his planets
    def listFleetsOrbiting():
        with connection.cursor() as cursor:
            cursor.execute("SELECT nav_planet.id, nav_planet.name, nav_planet.galaxy, nav_planet.sector, nav_planet.planet," +
                " fleets.id, fleets.name, users.login, alliances.tag, sp_relation(fleets.ownerid, nav_planet.ownerid), fleets.signature" +
                " FROM nav_planet" +
                "   INNER JOIN fleets ON fleets.planetid=nav_planet.id" +
                "   INNER JOIN users ON fleets.ownerid=users.id" +
                "   LEFT JOIN alliances ON users.alliance_id=alliances.id" +
                " WHERE nav_planet.ownerid=%s AND fleets.ownerid <> nav_planet.ownerid AND action <> 1 AND action <> -1" +
                " ORDER BY nav_planet.id, upper(alliances.tag), upper(fleets.name)", [gcontext['exile_user'].id])
            res = cursor.fetchall()
            if not res:
                gcontext["nofleets"] = True
            else:
                gcontext['planet'] = {}
                for re in res:
                    if re[0] not in gcontext['planet'].keys():
                        planet = {
                            "planetid": re[0],
                            "planetname": re[1],
                            "g": re[2],
                            "s": re[3],
                            "p": re[4],
                            'fleet': {}
                        }
                        gcontext['planet'][re[0]] = planet.copy()
                    fleet = {
                        "fleetname": re[6],
                        "fleetowner": re[7],
                        "fleetsignature": re[10],
                    }
                    if re[8]:
                        fleet["tag"] = re[8]
                        fleet["alliance"] = True
                    if re[9] == -1:
                        fleet["enemy"] = True
                    elif re[9] == 0:
                        fleet["friend"] = True
                    elif re[9] == 1:
                        fleet["ally"] = True
                    gcontext['planet'][re[0]]['fleet'][re[5]] = fleet.copy()
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'fleets_orbiting'
    gcontext['menu'] = menu(request)
    listFleetsOrbiting()
    context = gcontext
    t = loader.get_template('exile/fleets-orbiting.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def fleetsstandby(request):
    # List the fleets owned by the player
    def ListStandby():
        # list the ships
    #   query = "SELECT nav_planet.id, nav_planet.name, nav_planet.galaxy, nav_planet.sector, nav_planet.planet, db_ships.category, SUM(quantity)" & _
    #           " FROM planet_ships" &_
    #           "   INNER JOIN nav_planet ON (planet_ships.planetid = nav_planet.id)" &_
    #           "   LEFT JOIN db_ships ON (planet_ships.shipid = db_ships.id)" &_
    #           " WHERE nav_planet.ownerid =" & UserId & _
    #           " GROUP BY nav_planet.id, nav_planet.name, db_ships.category, nav_planet.galaxy, nav_planet.sector, nav_planet.planet" &_
    #           " ORDER BY nav_planet.id, db_ships.category"
        with connection.cursor() as cursor:
            cursor.execute("SELECT nav_planet.id, nav_planet.name, nav_planet.galaxy, nav_planet.sector, nav_planet.planet, shipid, quantity" +
                " FROM planet_ships" +
                "   INNER JOIN nav_planet ON (planet_ships.planetid = nav_planet.id)" +
                " WHERE nav_planet.ownerid=%s" +
                " ORDER BY nav_planet.id, shipid", [gcontext['exile_user'].id])
            res = cursor.fetchall()
            if not res:
                gcontext["noships"] = True
            else:
                gcontext['planet'] = {}
                for re in res:
                    if re[0] not in gcontext['planet'].keys():
                        pla = {
                            "planetid": re[0],
                            "planetname": re[1],
                            "g": re[2],
                            "s": re[3],
                            "p": re[4],
                            'ship': {},
                        }
                        gcontext['planet'][re[0]] = pla.copy()
                    ship = {
                        "ship": getShipLabel(re[5]),
                        "quantity": re[6],
        #               "planet.ship.category" & re[5]
        #               "planet.ship.category"
                    }
                    gcontext['planet'][re[0]]['ship'][re[5]] = ship.copy()
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'fleets_standby'
    gcontext['menu'] = menu(request)
    ListStandby()
    context = gcontext
    t = loader.get_template('exile/fleets-standby.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def fleetsshipsstats(request):
    # List all the available ships for construction
    def ListShips():
        # list ships that can be built on the planet
        with connection.cursor() as cursor:
            cursor.execute("SELECT category, shipid, killed, lost" +
                " FROM users_ships_kills" +
                "   INNER JOIN db_ships ON (db_ships.id = users_ships_kills.shipid)" +
                " WHERE userid=%s" +
                " ORDER BY shipid", [gcontext['exile_user'].id])
            res = cursor.fetchall()
            # number of items in category
            gcontext['category'] = {}
            gcontext['total'] = {'killed':0,'losses':0}
            for re in res:
                if re[0] not in gcontext['category'].keys():
                    gcontext['category'][re[0]] = {
                        'killed': 0,
                        'losses': 0,
                        'ship': {}
                    }
                ship = {
                    "id": re[1],
                    "name": getShipLabel(re[1]),
                    "killed": re[2],
                    "losses": re[3],
                }
                gcontext['category'][re[0]]['ship'][re[1]] = ship.copy()
                gcontext['category'][re[0]]['killed'] += re[2]
                gcontext['total']['killed'] += re[2]
                gcontext['category'][re[0]]['losses'] += re[3]
                gcontext['total']['losses'] += re[3]
            if not gcontext['category']:
                gcontext["no_ship"] = True
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'fleets_ships_stats'
    gcontext['menu'] = menu(request)
    ListShips()
    context = gcontext
    t = loader.get_template('exile/fleets-ships-stats.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def planets(request):
    def ListPlanets():
        gcontext['planets'] = {}
        col = int(request.POST.get('col', request.GET.get('col', 0)))
        if col == 0:
            orderby = 'id'
        elif col == 1:
            orderby = 'upper(name)'
        elif col == 2:
            orderby = 'ore_production'
        elif col == 3:
            orderby = 'hydrocarbon_production'
        elif col == 4:
            orderby = 'energy_consumption/(1.0+energy_production)'
        elif col == 5:
            orderby = 'mood'
        if request.POST.get('r', request.GET.get('r', '')) != '':
            reversed = True
        else:
            gcontext['r' + str(col)] = True
            reversed = False
        if reversed:
            orderby += ' DESC'
        orderby += ', upper(name)'
        with connection.cursor() as cursor:
            cursor.execute('SELECT t.id, name, galaxy, sector, planet,' +
                ' ore, ore_production, ore_capacity,' +
                ' hydrocarbon, hydrocarbon_production, hydrocarbon_capacity,' +
                ' workers-workers_busy, workers_capacity,' +
                ' energy_production - energy_consumption, energy_capacity,' +
                ' floor, floor_occupied,' +
                ' space, space_occupied,' +
                ' commanderid, (SELECT name FROM commanders WHERE id = t.commanderid) AS commandername,' +
                ' mod_production_ore, mod_production_hydrocarbon, workers, t.soldiers, soldiers_capacity,' +
                ' t.scientists, scientists_capacity, workers_for_maintenance, planet_floor, mood,' +
                ' energy, mod_production_energy, upkeep, energy_consumption,' +
                ' (SELECT int4(COALESCE(sum(scientists), 0)) FROM planet_training_pending WHERE planetid=t.id) AS scientists_training,' +
                ' (SELECT int4(COALESCE(sum(soldiers), 0)) FROM planet_training_pending WHERE planetid=t.id) AS soldiers_training,' +
                ' credits_production, credits_random_production, production_prestige' +
                ' FROM vw_planets AS t' +
                ' WHERE planet_floor > 0 AND planet_space > 0 AND ownerid=%s' +
                ' ORDER BY ' + orderby, [gcontext['exile_user'].id])
            res = cursor.fetchall()
            for re in res:
                mood_delta = 0
                planet = {
                    "planet_img": planetimg(re[0], re[29]),
                    "planet_id": re[0],
                    "planet_name": re[1],
                    "g": re[2],
                    "s": re[3],
                    "p": re[4],
                    "ore": re[5],
                    "ore_production": re[6],
                    "ore_capacity": re[7],
                    "hydrocarbon": re[8],
                    "hydrocarbon_production": re[9],
                    "hydrocarbon_capacity": re[10],
                    "energy": re[31],
                    "energy_production": re[13],
                    "energy_capacity": re[14],
                    "prestige": re[39],
                    "workers": re[23],
                    "workers_idle": re[11],
                    "workers_capacity": re[12],
                    "soldiers": re[24],
                    "soldiers_capacity": re[25],
                    "soldiers_training": re[36],
                    "scientists": re[26],
                    "scientists_capacity": re[27],
                    "scientists_training": re[35],
                    "floor_capacity": re[15],
                    "floor_occupied": re[16],
                    "space_capacity": re[17],
                    "space_occupied": re[18],
                    "upkeep_credits": re[33],
                    "upkeep_workers": re[28],
                    "upkeep_soldiers": int((re[23]+re[26]) / 250),
                }
                ore_level = getpercent(re[5], re[7], 10)
                if ore_level >= 90:
                    planet['high_ore'] = True
                elif ore_level >= 70:
                    planet['medium_ore'] = True
                else:
                    planet['normal_ore'] = True
                hydrocarbon_level = getpercent(re[8], re[10], 10)
                if hydrocarbon_level >= 90:
                    planet['high_hydrocarbon'] = True
                elif hydrocarbon_level >= 70:
                    planet['medium_hydrocarbon'] = True
                else:
                    planet['normal_hydrocarbon'] = True
                energy_level = getpercent(re[31], re[14], 10)
                planet['normal_energy'] = True
                planet['credits'] = int(re[37] + (re[38] / 2)) # - (re["upkeep"] / 24)
                if planet['credits'] < 0:
                    planet['credits_minus'] = True
                else:
                    planet['credits_plus'] = True
                if re[13] < 0:
                    planet['negative_energy_production'] = True
                elif re[32] >= 0 and re[23] >= re[28]:
                    planet['normal_energy_production'] = True
                else:
                    planet['medium_energy_production'] = True
                if re[36] > 0:
                    planet['soldiers_training'] = re[36]
                if re[35] > 0:
                    planet['scientists_training'] = re[35]
                if re[23] < re[28]:
                    planet['workers_low'] = True
                if re[24]*250 < re[23]+re[26]:
                    planet['soldiers_low'] = True
                if re[30] > 100:
                    planet['mood'] = 100
                else:
                    planet['mood'] = re[30]
                moodlevel = round(re[30] / 10) * 10
                if moodlevel > 100:
                    moodlevel = 100
                planet['mood_level'] = moodlevel
                if re[19]:
                    mood_delta += 1
                if re[24]*250 >= re[23]+re[26]:
                    mood_delta += 2
                else:
                    mood_delta -= 1
                planet['mood_delta'] = mood_delta
                if mood_delta > 0:
                    planet['mood_plus'] = True
                elif mood_delta < 0:
                    planet['mood_minus'] = True
                if re[19]:
                    planet['commander'] = {
                        'commander_id': re[19],
                        'commander_name': re[20],
                    }
                if re[21] >= 0 and re[23] >= re[28]:
                    planet['normal_ore_production'] = True
                else:
                    planet['medium_ore_production'] = True
                if re[22] >= 0 and re[23] >= re[28]:
                    planet['normal_hydrocarbon_production'] = True
                else:
                    planet['medium_hydrocarbon_production'] = True
                if re[0] == gcontext['CurrentPlanet']:
                    planet['highlight'] = True
                gcontext['planets'][re[0]] = planet.copy()
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'planets'
    gcontext['menu'] = menu(request)
    context = gcontext
    ListPlanets()
    t = loader.get_template('exile/planets.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def planet(request):
    def planetimg(id,floor):
        planetimg = 1 + (floor + id) % 21
        if planetimg < 10:
            planetimg = "0" + str(planetimg)
        return str(planetimg)
    def DisplayPlanet():
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, name, galaxy, sector, planet, ' +
                ' floor_occupied, floor, space_occupied, space, workers, workers_capacity, mod_production_workers, ' +
                ' scientists, scientists_capacity, soldiers, soldiers_capacity, commanderid, recruit_workers, ' +
                ' planet_floor, COALESCE(buy_ore, 0), COALESCE(buy_hydrocarbon, 0) ' +
                ' FROM vw_planets WHERE id=%s', [gcontext['CurrentPlanet']])
            re = cursor.fetchone()
            if not re:
                return
            planet = {
                "planet_id": re[0],
                "planet_name": re[1],
                "planet_img": planetimg(re[0], re[18]),
                "g": re[2],
                "s": re[3],
                "p":re[4],
                "floor_occupied": re[5],
                "floor": re[6],
                "space_occupied": re[7],
                "space": re[8],
                "workers": re[9],
                "workers_capacity": re[10],
                "scientists": re[12],
                "scientists_capacity": re[13],
                "soldiers": re[14],
                "soldiers_capacity": re[15],
                "growth": re[11]/10,
                "buy_ore": re[19],
                "buy_hydrocarbon": re[20],
                "optgroups": {'none':{},'planet':{},'fleet':{}}
            }
            if re[17]:
                planet["suspend"] = True
            else:
                planet["resume"] = True
            if re[16]:
                cursor.execute('SELECT name FROM commanders WHERE ownerid=%s AND id=%s', [gcontext['exile_user'].id, re[16]])
                oCmdRs = cursor.fetchone()
                if oCmdRs:
                    planet["commander"] = oCmdRs[0]
                CmdId = re[16]
            else:
                CmdId = 0
            if CmdId:
                planet["unassign"] = True
            cursor.execute('SELECT id, name, fleetname, planetname, fleetid ' +
                ' FROM vw_commanders WHERE ownerid=%s ' +
                ' ORDER BY fleetid IS NOT NULL, planetid IS NOT NULL, fleetid, planetid ', [gcontext['exile_user'].id])
            res = cursor.fetchall()
            lastItem = ""
            item = ""
            i = 0
            for re in res:
                optgroup = {
                    "cmd_id": re[0],
                    "cmd_name": re[1],
                    "cmd_option": {},
                }
                if not re[2] and not re[3]:
                    item = "none"
                elif not re[2]:
                    item = "planet"
                else:
                    item = "fleet"
                if CmdId == re[0]:
                    optgroup["cmd_option"]["selected"] = True
                if item == "planet":
                    optgroup["name"] = re[3]
                    optgroup["cmd_option"]["assigned"] = True
                if item == "fleet":
                    optgroup["name"] = re[2]
                    cursor.execute('SELECT dest_planetid, engaged, action FROM fleets WHERE ownerid=%s AND id=%s', [gcontext['exile_user'].id, re[4]])
                    activityRs = cursor.fetchone()
                    if activityRs:
                        if not activityRs[0] and not activityRs[1] and activityRs[2] == 0:
                            optgroup["cmd_option"]["assigned"] = True
                        else:
                            optgroup["cmd_option"]["unavailable"] = True
                planet["optgroups"][item][re[0]] = optgroup.copy()
                lastItem = item
                i += 1
            cursor.execute('SELECT buildingid, remaining_time, destroying ' +
                ' FROM vw_buildings_under_construction2 WHERE planetid=%s ' +
                ' ORDER BY remaining_time DESC', [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            planet['buildings'] = {}
            for re in res:
                building = {
                    "buildingid": re[0],
                    "building": getBuildingLabel(re[0]),
                    "time": re[1],
                }
                if re[2]:
                    building['destroy'] = True
                planet['buildings'][re[0]] = building.copy()
            cursor.execute('SELECT shipid, remaining_time, recycle ' +
                ' FROM vw_ships_under_construction ' +
                ' WHERE ownerid=%s AND planetid=%s AND end_time IS NOT NULL ' +
                ' ORDER BY remaining_time DESC', [gcontext['exile_user'].id, gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            planet['ships'] = {}
            for re in res:
                ship = {
                    "shipid": re[0],
                    "ship": getShipLabel(re[0]),
                    "time": re[1],
                }
                if re[2]:
                    ship['recycle'] = True
                planet['ships'][re[0]] = ship.copy()
            cursor.execute('SELECT id, name, attackonsight, engaged, size, signature, commanderid, (SELECT name FROM commanders WHERE id=commanderid) as commandername, ' +
                ' action, sp_relation(ownerid, %s) AS relation, sp_get_user(ownerid) AS ownername ' +
                ' FROM fleets ' +
                ' WHERE action != -1 AND action != 1 AND planetid=%s ' +
                ' ORDER BY upper(name)', [gcontext['exile_user'].id, gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            planet['fleets'] = {}
            for re in res:
                fleet = {
                    "id": re[0],
                    "size": re[4],
                    "signature": re[5],
                }
                if re[9] > config.rFriend:
                    fleet['name'] = re[1]
                else:
                    fleet['name'] = re[10]
                if re[6]:
                    fleet['commander'] = {
                        "commanderid": re[6],
                        "commandername": re[7],
                    }
                if re[3]:
                    fleet['fighting'] = True
                elif re[8] == 2:
                    fleet['recycling'] = True
                else:
                    fleet['patrolling'] = True
                if re[9] == config.rHostile or re[9] == config.rWar:
                    fleet['enemy'] = True
                elif re[9] == config.rFriend:
                    fleet['friend'] = True
                elif re[9] == config.rAlliance:
                    fleet['ally'] = True
                elif re[9] == config.rSelf:
                    fleet['owner'] = True
                planet['fleets'][re[0]] = fleet.copy()
            gcontext['planet'] = planet
    global config
    gcontext = request.session.get('gcontext',{})
    e_no_error = 0
    e_rename_bad_name = 1
    planet_error = e_no_error
    gcontext['showHeader'] = True
    gcontext['selectedmenu'] = 'planet'
    pid = request.POST.get('id', request.GET.get('id' , gcontext['CurrentPlanet']))
    try:
        fplanet = NavPlanet.objects.get(pk=pid)
    except (KeyError, NavPlanet.DoesNotExist):
        return HttpResponseRedirect(reverse('exile:planet')+'?id='+str(gcontext['CurrentPlanet']))
    if fplanet.ownerid_id != gcontext['exile_user'].id:
        return HttpResponseRedirect(reverse('exile:planet')+'?id='+str(gcontext['CurrentPlanet']))
    gcontext['CurrentPlanet'] = fplanet.id
    request.session['CurrentPlanet'] = fplanet.id
    request.session['CurrentGalaxy'] = fplanet.galaxy.id
    request.session['CurrentSector'] = fplanet.sector
    gcontext['planetid'] = gcontext['CurrentPlanet']
    gcontext['g'] = fplanet.galaxy.id
    gcontext['s'] = fplanet.sector
    gcontext['p'] = fplanet.planet
    gcontext['menu'] = menu(request)
    context = gcontext
    action = request.POST.get('action', request.GET.get('action', ''))
    if action == "assigncommander":
        commander = request.POST.get('commander', request.GET.get('commander', 0))
        if commander != 0:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM sp_commanders_assign(%s, %s, %s, null)', [gcontext['exile_user'].id, commander, gcontext['CurrentPlanet']])
        else:
            with connection.cursor() as cursor:
                cursor.execute('UPDATE nav_planet SET commanderid=NULL WHERE ownerid=%s AND id=%s', [gcontext['exile_user'].id, gcontext['CurrentPlanet']])
    elif action == "rename":
        name = request.POST.get('name', request.GET.get('name', ''))
        if not isValidName(name):
            gcontext['rename_bad_name'] = True
        else:
            with connection.cursor() as cursor:
                cursor.execute('UPDATE nav_planet SET name=%s WHERE ownerid=%s AND id=%s', [name, gcontext['exile_user'].id, gcontext['CurrentPlanet']])
    elif action == "firescientists":
        amount = request.POST.get('amount', request.GET.get('amount', 0))
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_dismiss_staff(%s, %s, %s, 0, 0)', [gcontext['exile_user'].id, gcontext['CurrentPlanet'], amount])
    elif action == "firesoldiers":
        amount = request.POST.get('amount', request.GET.get('amount', 0))
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_dismiss_staff(%s, %s, 0, %s, 0)', [gcontext['exile_user'].id, gcontext['CurrentPlanet'], amount])
    elif action == "fireworkers":
        amount = request.POST.get('amount', request.GET.get('amount', 0))
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_dismiss_staff(%s, %s, 0, 0, %s)', [gcontext['exile_user'].id, gcontext['CurrentPlanet'], amount])
    elif action == "abandon":
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_abandon_planet(%s, %s)', [gcontext['exile_user'].id, gcontext['CurrentPlanet']])
        return HttpResponseRedirect(reverse('exile:overview'))
    elif action == "resources_price":
        buy_ore = request.POST.get('buy_ore', request.GET.get('buy_ore', ''))
        if not buy_ore:
            buy_ore = 0
        buy_hydrocarbon = request.POST.get('buy_hydrocarbon', request.GET.get('buy_hydrocarbon', ''))
        if not buy_hydrocarbon:
            buy_hydrocarbon = 0
        with connection.cursor() as cursor:
            cursor.execute('UPDATE nav_planet SET buy_ore = GREATEST(0, LEAST(1000, %s)), buy_hydrocarbon = GREATEST(0, LEAST(1000, %s))' +
            ' WHERE ownerid=%s AND id=%s', [buy_ore, buy_hydrocarbon, gcontext['exile_user'].id, gcontext['CurrentPlanet']])
    a = request.POST.get('a', request.GET.get('a', ''))
    if a == "suspend":
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_update_planet_production(%s)', [gcontext['CurrentPlanet']])
            cursor.execute('UPDATE nav_planet SET mod_production_workers=0, recruit_workers=false WHERE ownerid=%s AND id=%s', [gcontext['exile_user'].id, gcontext['CurrentPlanet']])
    elif a == "resume":
        with connection.cursor() as cursor:
            cursor.execute('UPDATE nav_planet SET recruit_workers=true WHERE ownerid=%s AND id=%s', [gcontext['exile_user'].id, gcontext['CurrentPlanet']])
            cursor.execute('SELECT sp_update_planet(%s)', [gcontext['CurrentPlanet']])
    DisplayPlanet()
    gcontext['contextinfo'] = header(request)
    t = loader.get_template('exile/planet.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def marketsell(request):
    # display market for current player's planets
    def DisplayMarket():
        #Session("details") = "Display market : retrieve prices"
        try:
            planet = int(request.GET.get("planet","0"))
        except (KeyError, Exception):
            planet = ""
        if planet:
            planet = " AND v.id=" +str(planet)
        else:
            planet = ""
        #Session("details") = "list planets"
        # retrieve ore, hydrocarbon, sales quantities on the planet
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, galaxy, sector, planet, ore, hydrocarbon, ore_capacity, hydrocarbon_capacity, planet_floor," +
                " ore_production, hydrocarbon_production," +
                " (sp_market_price((sp_get_resource_price(0, galaxy)).sell_ore, planet_stock_ore))," +
                " (sp_market_price((sp_get_resource_price(0, galaxy)).sell_hydrocarbon, planet_stock_hydrocarbon))" +
                " FROM vw_planets AS v" +
                " WHERE floor > 0 AND v.ownerid=%s" + str(planet) +
                " ORDER BY v.id", [gcontext['exile_user'].id])
            res = cursor.fetchall()
            total = count = 0
            i = 1
            gcontext['planet'] = {}
            for re in res:
                p_img = 1+(re[9] + re[0]) % 21
                if p_img < 10:
                    p_img = "0" + str(p_img)
                pla = {
                    "index": i,
                    "planet_img": p_img,
                    "planet_id": re[0],
                    "planet_name": re[1],
                     "g": re[2],
                    "s": re[3],
                    "p": re[4],
                    "planet_ore": re[5],
                    "planet_hydrocarbon": re[6],
                    "planet_ore_capacity": re[7],
                    "planet_hydrocarbon_capacity": re[8],
                    "planet_ore_production": re[10],
                    "planet_hydrocarbon_production": re[11],
                    "ore_price": re[12],
                    "hydrocarbon_price": re[13],
                    "ore_price2": re[12],
                    "hydrocarbon_price2": re[13],
                }
                # if ore/hydrocarbon quantity reach their capacity in less than 4 hours
                if re[5] > re[7]-4*re[10]:
                    pla["high_ore_capacity"] = True
                if re[6] > re[8]-4*re[11]:
                    pla["high_hydrocarbon_capacity"] = True
                pla["ore_max"] = min(10000, int(re[5]/1000))
                pla["hydrocarbon_max"] = min(10000, int(re[6]/1000))
                #content.AssignValue "ore", request.POST.get("o" & re[0])
                #content.AssignValue "hydrocarbon", request.POST.get("h" & re[0])
                pla["selling_price"] = 0
                count = count + 1
                if re[0] == gcontext['CurrentPlanet']:
                    pla["highlight"] = True
                gcontext["planet"][i] = pla.copy()
                i = i + 1
            if planet:
                gcontext['showHeader'] = True
                gcontext['contextinfo'] = header(request)
                gcontext["planetid"] = gcontext["planet"][1]['planet_id']
                gcontext['selectedmenu'] = 'market_sell'
            else:
                FillHeaderCredits(request)
                gcontext["total"] = total
                gcontext["totalprice"] = True
                gcontext['selectedmenu'] = 'merchant_sell'
            if count > 0:
                gcontext["sell"] = True
    # execute sell orders
    def ExecuteOrder():
        if request.GET.get("a","") != "sell":
            return
        #Session("details") = "Execute orders"
        # retrieve the prices given when we last asked for the market prices
        #RetrievePrices()
        # for each planet owned, check what the player sells
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM nav_planet WHERE ownerid=%s", [gcontext['exile_user'].id])
            res =cursor.fetchall()
            # set the timeout : 2 seconds per planet
            #Server.ScriptTimeout = Server.ScriptTimeout + planetsCount*2
            for re in res:
                planetid = re[0]
                # retrieve ore & hydrocarbon quantities
                try:
                    ore = int(request.POST.get("o" + str(planetid), '0'))
                except (KeyError, Exception):
                    ore = 0
                try:
                    hydrocarbon = int(request.POST.get("h" + str(planetid), '0'))
                except (KeyError, Exception):
                    hydrocarbon = 0
                if ore > 0 or hydrocarbon > 0:
                    #Session("details") = query
                    cursor.execute("SELECT sp_market_sell(%s, %s, %s, %s)", [gcontext['exile_user'].id, planetid, ore*1000, hydrocarbon*1000])
                    #Session("details") = "done:"&query
            if request.POST.get("rel") != 1:
                log_notice(request, "market-sell", "hidden value is missing from form data", 1)
    gcontext = request.session.get('gcontext',{})
    ExecuteOrder()
    DisplayMarket()
    gcontext['menu'] = menu(request)
    context = gcontext
    t = loader.get_template('exile/market-sell.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def marketbuy(request):
    # display market for current player's planets
    def DisplayMarket():
        # get market template
        try:
            planet = int(request.GET.get("planet","0"))
        except (KeyError, Exception):
            planet = 0
        if planet:
            planet = " AND v.id=" + str(planet)
        else:
            planet = ''
        #Session("details") = "list planets"
        # retrieve ore, hydrocarbon, sales quantities on the planet
        with connection.cursor() as cursor:
            cursor.execute("SELECT v.id, v.name, v.galaxy, v.sector, v.planet, v.ore, v.hydrocarbon, v.ore_capacity, v.hydrocarbon_capacity, v.planet_floor," +
                " v.ore_production, v.hydrocarbon_production," +
                " m.ore, m.hydrocarbon, m.ore_price, m.hydrocarbon_price," +
                " int4(date_part('epoch', m.delivery_time-now()))," +
                " sp_get_planet_blocus_strength(v.id) >= v.space," +
                " workers, workers_for_maintenance," +
                " (SELECT has_merchants FROM nav_galaxies WHERE id=v.galaxy) as has_merchants," +
                " (sp_get_resource_price(%(UserId)s, v.galaxy)).buy_ore::real AS p_ore," +
                " (sp_get_resource_price(%(UserId)s, v.galaxy)).buy_hydrocarbon AS p_hydrocarbon" +
                " FROM vw_planets AS v" +
                "   LEFT JOIN market_purchases AS m ON (m.planetid=v.id)" +
                " WHERE floor > 0 AND v.ownerid=%(UserId)s" + planet +
                " ORDER BY v.id", {'UserId':gcontext['exile_user'].id})
            res = cursor.fetchall()
            total = count = 0
            i = 1
            gcontext['planet'] = {}
            for re in res:
                p_img = 1+(re[9] + re[0]) % 21
                if p_img < 10:
                    p_img = "0" + str(p_img)
                pla = {
                    "index": i,
                    "planet_img": p_img,
                    "planet_id": re[0],
                    "planet_name": re[1],
                    "g": re[2],
                    "s": re[3],
                    "p": re[4],
                    "planet_ore": re[5],
                    "planet_hydrocarbon": re[6],
                    "planet_ore_capacity": re[7],
                    "planet_hydrocarbon_capacity": re[8],
                    "planet_ore_production": re[10],
                    "planet_hydrocarbon_production": re[11],
                    "can_buy": {},
                }
                # if ore/hydrocarbon quantity reach their capacity in less than 4 hours
                if re[5] > re[7]-4*re[10]:
                    pla["high_ore_capacity"] = True
                if re[6] > re[8]-4*re[11]:
                    pla["high_hydrocarbon_capacity"] = True
                pla["ore_max"] = int((re[7]-re[5])/1000)
                pla["hydrocarbon_max"] = int((re[8]-re[6])/1000)
                pla["price_ore"] = re[21]
                pla["price_hydrocarbon"] = re[22]
                if re[12]:
                    pla["buying_ore"] = re[12]
                    pla["buying_hydrocarbon"] = re[13]
                    subtotal = re[12]/1000*re[14] + re[13]/1000*re[15]
                    total = total + subtotal
                    pla["buying_price"] = subtotal
                    pla["can_buy"]["buying"] = True
                else:
                    pla["ore"] = request.POST.get("o" + str(re[0]),"")
                    pla["hydrocarbon"] = request.POST.get("h" + str(re[0]),"")
                    pla["buying_price"] = 0
                    if not re[20]:
                        pla["cant_buy_merchants"] = True
                    elif re[18] < re[19] / 2:
                        pla["cant_buy_workers"] = True
                    elif re[17]:
                        pla["cant_buy_enemy"] = True
                    else:
                        pla["can_buy"]["buy"] = True
                    count += 1
                if re[0] == gcontext['CurrentPlanet']:
                    pla["highlight"] = True
                gcontext['planet'][i] = pla.copy()
                i = i + 1
            if planet:
                gcontext['showHeader'] = True
                gcontext['contextinfo'] = header(request)
                gcontext["planetid"] = gcontext["planet"][1]['planet_id']
                gcontext['selectedmenu'] = 'market_buy'
            else:
                FillHeaderCredits(request)
                gcontext["total"] = total
                gcontext["totalprice"] = True
                gcontext['selectedmenu'] = 'merchant_buy'
            if count > 0:
                gcontext["buy"] = True
    # execute buy orders
    def ExecuteOrder():
        if request.GET.get("a","") != "buy":
            return
        #Session("details") = "Execute orders"
        # for each planet owned, check what the player buys
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM nav_planet WHERE ownerid=%s", [gcontext['exile_user'].id])
            res =cursor.fetchall()
            # set the timeout : 2 seconds per planet
            #Server.ScriptTimeout = Server.ScriptTimeout + planetsCount*2
            for re in res:
                planetid = re[0]
                # retrieve ore & hydrocarbon quantities
                try:
                    ore = int(request.POST.get("o" + str(planetid), "0"))
                except (KeyError, Exception):
                    ore = 0
                try:
                    hydrocarbon = int(request.POST.get("h" + str(planetid), "0"))
                except (KeyError, Exception):
                    hydrocarbon = 0
                if ore > 0 or hydrocarbon > 0:
                    #Session("details") = query
                    cursor.execute("SELECT * FROM sp_buy_resources(%s, %s, %s, %s)", [gcontext['exile_user'].id, planetid, ore*1000, hydrocarbon*1000])
                    #Session("details") = "done:"&query
    gcontext = request.session.get('gcontext',{})
    ExecuteOrder()
    DisplayMarket()
    gcontext['menu'] = menu(request)
    gcontext['contextinfo'] = header(request)
    context = gcontext
    t = loader.get_template('exile/market-buy.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def research(request):
    def HasEnoughFunds(credits):
        return credits <= 0 or gcontext['exile_user'].credits >= credits
    # List all the available researches
    def ListResearches():
        # count number of researches pending
        with connection.cursor() as cursor:
            cursor.execute('SELECT int4(count(1)) FROM researches_pending WHERE userid=%s LIMIT 1', [gcontext['exile_user'].id])
            res = cursor.fetchone()
            if res:
                underResearchCount = res[0]
            # list things that can be researched
            cursor.execute('SELECT researchid, category, total_cost, total_time, level, levels, researchable, buildings_requirements_met, status, ' +
                ' (SELECT looping FROM researches_pending WHERE researchid = t.researchid AND userid=%s) AS looping, ' +
                ' expiration_time IS NOT NULL, planet_elements_requirements_met ' +
                ' FROM sp_list_researches(%s) AS t ' +
                ' WHERE level > 0 OR (researchable AND planet_elements_requirements_met)', [gcontext['exile_user'].id, gcontext['exile_user'].id])
            res = cursor.fetchall()
            # number of items in category
            gcontext['category'] = {}
            for re in res:
                category = re[1]
                research = {
                    "id": re[0],
                    "name": getResearchLabel(re[0]),
                    "credits": re[2],
                    "nextlevel": re[4]+1,
                    "level": re[4],
                    "levels": re[5],
                    "description": getResearchDescription(re[0]),
                }
                status = re[8]
                # if status is not null: this research is under way
                if status:
                    if status < 0:
                        status = 0
                    research['leveling'] = True
                    research['remainingtime'] = status
                    if re[9]:
                        research['auto'] = True
                    else:
                        research['manual'] = True
                    research['cost'] = True
                    research['countdown'] = True
                    research['researching'] = True
                else:
                    #research['level'] = True
                    if re[4] < re[5] or re[10]:
                        research['time'] = re[3]
                        research['researchtime'] = True
                        if not re[6] or not re[7] or not re[11]:
                            research['notresearchable'] = True
                        elif underResearchCount > 0:
                            research['busy'] = True
                        elif not HasEnoughFunds(re[2]):
                            research['notenoughmoney'] = True
                        else:
                            research['research'] = True
                        research['cost'] = True
                    else:
                        research['nocost'] = True
                        research['noresearchtime'] = True
                        research['complete'] = True
                ck = 'category' + str(category)
                if not ck in gcontext['category']:
                    gcontext['category'][ck] = {}
                gcontext['category'][ck][re[0]] = research.copy()
    def StartResearch(ResearchId):
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM sp_start_research(%s, %s, false)', [gcontext['exile_user'].id, ResearchId])
    def CancelResearch(ResearchId):
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM sp_cancel_research(%s, %s)', [gcontext['exile_user'].id, ResearchId])
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'research'
    gcontext['menu'] = menu(request)
    context = gcontext
    with connection.cursor() as cursor:
        cursor.execute('SELECT sp_update_researches(%s)', [gcontext['exile_user'].id])
    Action = request.GET.get('a', '').lower()
    ResearchId = int(request.GET.get('r', 0))
    if ResearchId != 0:
        if Action == "research":
            StartResearch(ResearchId)
        elif Action == "cancel":
            CancelResearch(ResearchId)
        elif Action == "continue":
            with connection.cursor() as cursor:
                cursor.execute('UPDATE researches_pending SET looping=true WHERE userid=%s AND researchid=%s', [gcontext['exile_user'].id, ResearchId])
        elif Action == "stop":
            with connection.cursor() as cursor:
                cursor.execute('UPDATE researches_pending SET looping=false WHERE userid=%s AND researchid=%s', [gcontext['exile_user'].id, ResearchId])
    ListResearches()
    FillHeaderCredits(request)
    t = loader.get_template('exile/research.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def researchoverview(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/research-overview.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def alliance(request):
    def DisplayAlliance(alliance_tag):
        gcontext['addAllowedImageDomain'] = "*"
        gcontext['selectedmenu'] = 'alliance_overview'
        with connection.cursor() as cursor:
            if not alliance_tag:
                cursor.execute("SELECT id, name, tag, description, created, (SELECT count(*) FROM users WHERE alliance_id=alliances.id)," +
                " logo_url, website_url, max_members" +
                " FROM alliances WHERE id=%s LIMIT 1", [gcontext['exile_user'].alliance_id])
            else:
                cursor.execute("SELECT id, name, tag, description, created, (SELECT count(*) FROM users WHERE alliance_id=alliances.id)," +
                " logo_url, website_url, max_members" +
                " FROM alliances  WHERE tag=upper(%s) LIMIT 1", [alliance_tag])
                gcontext['selectedmenu'] = 'alliance_ranking'
            res = cursor.fetchall()
            for re in res:
                alliance = {
                    'id': re[0],
                    "name": re[1],
                    "tag": re[2],
                    "description": re[3],
                    "created": re[4],
                    "members": re[5],
                    "max_members": re[8],
                    "naps" : {},
                    "wars": {},
                }
                alliance_id = re[0]
                if re[6] and re[6] != "":
                    alliance["logo_url"] = re[6]
                    alliance["logo"] = True
                # Display Non Aggression Pacts (NAP)
                NAPcount = 0
                cursor.execute('SELECT allianceid1, tag, name ' +
                        ' FROM alliances_naps INNER JOIN alliances ON (alliances_naps.allianceid1=alliances.id) ' +
                        ' WHERE allianceid2=%s', [alliance_id])
                res1 = cursor.fetchall()
                for re1 in res1:
                    nap = {
                        'naptag': re1[1],
                        'napname': re1[2],
                    }
                    alliance['naps'][NAPcount] = nap.copy()
                    NAPcount += 1
                if NAPcount == 0:
                    alliance['nonaps'] = True
                # Display WARs
                WARcount = 0
                cursor.execute('SELECT w.created, alliances.id, alliances.tag, alliances.name ' +
                    ' FROM alliances_wars w ' +
                    '   INNER JOIN alliances ON (allianceid2 = alliances.id) ' +
                    ' WHERE allianceid1=%s ' +
                    ' UNION SELECT w.created, alliances.id, alliances.tag, alliances.name ' +
                    ' FROM alliances_wars w ' +
                    '   INNER JOIN alliances ON (allianceid1 = alliances.id) ' +
                    ' WHERE allianceid2=%s', [alliance_id, alliance_id])
                res1 = cursor.fetchall()
                for re1 in res1:
                    war = {
                        'wartag': re1[2],
                        'warname': re1[3],
                    }
                    alliance['wars'][WARcount] = war.copy()
                    WARcount += 1
                if WARcount == 0:
                    alliance['nowars'] = True
                # List members that should be displayed
                cursor.execute("SELECT id, rankid, label, members_displayed" +
                        " FROM alliances_ranks" +
                        " WHERE allianceid=%s" +
                        " ORDER BY rankid", [alliance_id])
                res1 = cursor.fetchall()
                if res1:
                    alliance['members'] = {'rank_label':{},'total':0}
                    member= 0
                    for re1 in res1:
                        if re1[2] not in alliance['members']['rank_label'].keys():
                            alliance['members']['rank_label'][re1[2]] = {}
                        cursor.execute("SELECT login" +
                                " FROM users" +
                                " WHERE alliance_id=%s AND alliance_rank = %s " +
                                " ORDER BY upper(login)", [alliance_id, re1[0]])
                        res2 = cursor.fetchall()
                        for re2 in res2:
                            if re1[3]:
                                alliance['members']["rank_label"][re1[2]][member] = {'member':re2[0]}
                            member += 1
                    alliance['members']['total'] = member
                gcontext['alliance'] = alliance.copy()
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'noalliance'
    tag = request.GET.get("tag",'')
    if tag:
        DisplayAlliance(tag)
    else:
        if not gcontext['exile_user'].alliance_id:
            return HttpResponseRedirect(reverse("exile:allianceinvitations"))
        else:
            DisplayAlliance('')
    gcontext['menu'] = menu(request)
    context = gcontext
    t = loader.get_template('exile/alliance.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def alliancemanage(request):
    # Display alliance description page
    def displayGeneral():
        # Display alliance tag, name, description, creation date, number of members
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, tag, name, description, created, (SELECT count(*) FROM users WHERE alliance_id=alliances.id), logo_url," +
                " max_members FROM alliances WHERE id=%s", [gcontext['exile_user'].alliance_id])
            res = cursor.fetchone()
            gcontext["general"] = {}
            if res:
                gcontext["general"]["tag"] = res[1]
                gcontext["general"]["name"] = res[2]
                gcontext["general"]["description"] = res[3]
                gcontext["general"]["created"] = res[4]
                gcontext["general"]["members"] = res[5]
                gcontext["general"]["max_members"] = res[7]
                if res[6] != "":
                    gcontext["general"]["logo_url"] = res[6]
                    gcontext["general"]["logo"] = True
    # Display alliance MotD (message of the day)
    def displayMotD():
        # Display alliance MotD (message of the day)
        with connection.cursor() as cursor:
            cursor.execute("SELECT announce, defcon FROM alliances WHERE id=%s", [gcontext['exile_user'].alliance_id])
            res = cursor.fetchone()
            gcontext["motd"] = {}
            if res:
                gcontext["motd"]["motd"] = res[0]
                gcontext["motd"]["defcon_" + str(res[1])] = True
    def displayRanks():
        # list ranks
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, rankid, label, leader, can_invite_player, can_kick_player, can_create_nap, can_break_nap, can_ask_money, can_see_reports, " + # 0 1 2 3 4 5 6 7 8 9
                " can_accept_money_requests, can_change_tax_rate, can_mail_alliance, is_default, members_displayed, can_manage_description, can_manage_announce, " + # 10 11 12 13 14 15 16
                " enabled, can_see_members_info, can_order_other_fleets, can_use_alliance_radars" + # 17 18 19 20
                " FROM alliances_ranks" +
                " WHERE allianceid=%s" +
                " ORDER BY rankid", [gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            gcontext['ranks'] = {}
            for re in res:
                rank = {
                    'id': re[0],
                    "rank_id": re[1],
                    "rank_label": re[2],
                }
                if re[3]:
                    rank["disabled"] = True
                if re[3] or re[17]:
                    rank["checked_enabled"] = True
                if re[13] and not re[3]:
                    rank["checked_0"] = True
                if re[3] or re[4]:
                    rank["checked_1"] = True
                if re[3] or re[5]:
                    rank["checked_2"] = True
                if re[3] or re[6]:
                    rank["checked_3"] = True
                if re[3] or re[7]:
                    rank["checked_4"] = True
                if re[3] or re[8]:
                    rank["checked_5"] = True
                if re[3] or re[9]:
                    rank["checked_6"] = True
                if re[3] or re[10]:
                    rank["checked_7"] = True
                if re[3] or re[11]:
                    rank["checked_8"] = True
                if re[3] or re[12]:
                    rank["checked_9"] = True
                if re[3] or re[15]:
                    rank["checked_10"] = True
                if re[3] or re[16]:
                    rank["checked_11"] = True
                if re[3] or re[18]:
                    rank["checked_12"] = True
                if re[3] or re[14]:
                    rank["checked_13"] = True
                if re[3] or re[19]:
                    rank["checked_14"] = True
                if re[3] or re[20]:
                    rank["checked_15"] = True
                gcontext['ranks'][re[0]] = rank.copy()
    # Load template and display the right page
    def DisplayOptions(cat):
        if gcontext['cat'] == 1:
            displayGeneral()
        elif gcontext['cat'] == 2:
            displayMotD()
        elif gcontext['cat'] == 3:
            displayRanks()
        if gcontext['changes_status'] != "":
            gcontext['error'][gcontext['changes_status']] = True
        gcontext['nav'] = {}
        gcontext['nav']['cat'+str(gcontext['cat'])] = {'selected': True}
        if hasRight(request,"leader") or hasRight(request,"can_manage_description"):
            gcontext['nav']['cat1'] = True
        if hasRight(request,"leader") or hasRight(request,"can_manage_announce"):
            gcontext['nav']['cat2'] = True
        if hasRight(request,"leader"):
            gcontext['nav']['cat3'] = True
    def SaveGeneral():
        logo = request.POST.get("logo", "").strip()
        description = strip_tags(request.POST.get("description", "").strip())
        try:
            if not logo:
                #logo is invalid
                gcontext['changes_status'] = "check_logo"
            else:
                validate = URLValidator(schemes=('http', 'https', 'ftp', 'ftps', 'rtsp', 'rtmp'))
                validate(logo)
                # save updated information
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE alliances SET logo_url=%s, description=%s WHERE id=%s", [logo, description, gcontext['exile_user'].alliance_id])
                    gcontext['changes_status'] = "done"
        except ValidationError:
            #logo is invalid
            gcontext['changes_status'] = "check_logo"
    def SaveMotD():
        MotD = strip_tags(request.POST.get("motd", "").strip())
        try:
            defcon = int(request.POST.get("defcon", "5"))
        except (KeyError, Exception):
            defcon = 5
        # save updated information
        with connection.cursor() as cursor:
            cursor.execute("UPDATE alliances SET defcon=%s, announce=%s WHERE id=%s", [defcon, MotD, gcontext['exile_user'].alliance_id])
            gcontext['changes_status'] = "done"
    def SaveRanks():
        # list ranks
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, rankid, leader FROM alliances_ranks WHERE allianceid=%s ORDER BY rankid", [gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            for re in res:
                name = request.POST.get("n"+str(re[1]), "").strip()
                if len(name) > 2:
                    c0 = True and bool(request.POST.get("c"+str(re[1])+"_0", ""))
                    c1 = True and bool(request.POST.get("c"+str(re[1])+"_1", ""))
                    c2 = True and bool(request.POST.get("c"+str(re[1])+"_2", ""))
                    c3 = True and bool(request.POST.get("c"+str(re[1])+"_3", ""))
                    c4 = True and bool(request.POST.get("c"+str(re[1])+"_4", ""))
                    c5 = True and bool(request.POST.get("c"+str(re[1])+"_5", ""))
                    c6 = True and bool(request.POST.get("c"+str(re[1])+"_6", ""))
                    c7 = True and bool(request.POST.get("c"+str(re[1])+"_7", ""))
                    c8 = True and bool(request.POST.get("c"+str(re[1])+"_8", ""))
                    c9 = True and bool(request.POST.get("c"+str(re[1])+"_9", ""))
                    c10 = True and bool(request.POST.get("c"+str(re[1])+"_10", ""))
                    c11 = True and bool(request.POST.get("c"+str(re[1])+"_11", ""))
                    c12 = True and bool(request.POST.get("c"+str(re[1])+"_12", ""))
                    c13 = True and bool(request.POST.get("c"+str(re[1])+"_13", ""))
                    c14 = True and bool(request.POST.get("c"+str(re[1])+"_14", ""))
                    c15 = True and bool(request.POST.get("c"+str(re[1])+"_15", ""))
                    cenabled = True and bool(request.POST.get("c"+str(re[1])+"_enabled", ""))
                    if c0:
                        cursor.execute("UPDATE alliances_ranks SET is_default=false WHERE allianceid=%s", [gcontext['exile_user'].alliance_id])
                    cursor.execute("UPDATE alliances_ranks SET" +
                        " label=%s" +
                        ", is_default=NOT leader AND %s" +
                        ", can_invite_player=leader OR %s" +
                        ", can_kick_player=leader OR %s" +
                        ", can_create_nap=leader OR %s" +
                        ", can_break_nap=leader OR %s" +
                        ", can_ask_money=leader OR %s" +
                        ", can_see_reports=leader OR %s" +
                        ", can_accept_money_requests=leader OR %s" +
                        ", can_change_tax_rate=leader OR %s" +
                        ", can_mail_alliance=leader OR %s" +
                        ", can_manage_description=leader OR %s" +
                        ", can_manage_announce=leader OR %s" +
                        ", can_see_members_info=leader OR %s" +
                        ", members_displayed=leader OR %s" +
                        ", can_order_other_fleets=leader OR %s" +
                        ", can_use_alliance_radars=leader OR %s" +
                        ", enabled=leader OR EXISTS(SELECT 1 FROM users WHERE alliance_id=%s AND alliance_rank=%s LIMIT 1) OR %s OR %s" +
                        " WHERE allianceid=%s AND rankid=%s",
                        [name, c0, c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14, c15,
                        gcontext['exile_user'].alliance_id, re[0], cenabled, c0, gcontext['exile_user'].alliance_id, re[1]])
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'alliance_manage'
    gcontext['changes_status'] = ''
    gcontext['error'] = {}
    if not gcontext['exile_user'].alliance_id:
        return HttpResponseRedirect(reverse('exile:alliance'))
    if not (hasRight(request,"leader") or hasRight(request,"can_manage_description") or hasRight(request,"can_manage_announce")):
        return HttpResponseRedirect(reverse('exile:alliance'))
    try:
        cat = int(request.GET.get("cat", '1'))
    except (KeyError, Exception):
        cat = 1
    if cat < 1 or cat > 3:
        cat = 1
    if cat == 3 and not hasRight(request,"leader"):
        cat=1
    if cat == 1 and not (hasRight(request,"leader") or hasRight(request,"can_manage_description")):
        cat=2
    if cat == 2 and not (hasRight(request,"leader") or hasRight(request,"can_manage_announce")):
        cat=1
    if request.POST.get("submit", "") != "":
        if cat == 1:
            SaveGeneral()
        elif cat == 2:
            SaveMotD()
        elif cat == 3:
            SaveRanks()
    gcontext['cat'] = cat
    DisplayOptions(cat)
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/alliance-manage.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def alliancefleets(request):
    def getAllyFleets():
        with connection.cursor() as cursor:
            cursor.execute('SELECT fleetid, fleets_ships.shipid, quantity' +
                ' FROM fleets' +
                ' INNER JOIN fleets_ships ON (fleets.id=fleets_ships.fleetid)' +
                ' INNER JOIN users ON (users.id=fleets.ownerid)' +
                ' WHERE shared AND users.alliance_id=%s' +
                ' ORDER BY fleetid, fleets_ships.shipid', [gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            if not res:
                ShipListCount = -1
            else:
                ShipListArray = res
                ShipListCount = len(res)
            cursor.execute('SELECT id, name, attackonsight, engaged, size, signature, speed, remaining_time, commanderid, commandername,' + # 0 1 2 3 4 5 6 7 8 9
                ' planetid, planet_name, planet_galaxy, planet_sector, planet_planet, planet_ownerid, planet_owner_name, planet_owner_relation,' + # 10 11 12 13 14 15 16 17
                ' destplanetid, destplanet_name, destplanet_galaxy, destplanet_sector, destplanet_planet, destplanet_ownerid, destplanet_owner_name, destplanet_owner_relation,' + # 18 19 20 21 22 23 24 25
                ' cargo_capacity, cargo_ore, cargo_hydrocarbon, cargo_scientists, cargo_soldiers, cargo_workers,' + # 26 27 28 29 30 31
                ' recycler_output, orbit_ore > 0 OR orbit_hydrocarbon > 0, action,' + # 32 33 34
                '( SELECT int4(COALESCE(max(nav_planet.radar_strength), 0)) FROM nav_planet WHERE nav_planet.galaxy = f.planet_galaxy AND nav_planet.sector = f.planet_sector AND nav_planet.ownerid IS NOT NULL AND EXISTS ( SELECT 1 FROM vw_friends_radars WHERE vw_friends_radars.friend = nav_planet.ownerid AND vw_friends_radars.userid = %s)) AS from_radarstrength, ' + # 35
                '( SELECT int4(COALESCE(max(nav_planet.radar_strength), 0)) FROM nav_planet WHERE nav_planet.galaxy = f.destplanet_galaxy AND nav_planet.sector = f.destplanet_sector AND nav_planet.ownerid IS NOT NULL AND EXISTS ( SELECT 1 FROM vw_friends_radars WHERE vw_friends_radars.friend = nav_planet.ownerid AND vw_friends_radars.userid = %s)) AS to_radarstrength' +
                " FROM vw_fleets as f" +
                " WHERE shared AND owner_alliance_id=%s", [gcontext['exile_user'].id, gcontext['exile_user'].id, gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            gcontext['list'] = {'fleet': {}}
            if not res:
                pass
            else:
                for re in res:
                    fleet = {}
                    fleet['ship'] = {}
                    fleet['resource'] = {1:{},2:{},3:{},4:{},5:{}}
                    fleet['id'] = re[0]
                    fleet['name'] = re[1]
                    fleet['size'] = re[4]
                    fleet['signature'] = re[5]
                    fleet['cargo_load'] = re[27]+re[28]+re[29]+re[30]+re[31]
                    fleet['cargo_capacity'] = re[26]
                    fleet['cargo_ore'] = re[27]
                    fleet['cargo_hydrocarbon'] = re[28]
                    fleet['cargo_scientists'] = re[29]
                    fleet['cargo_soldiers'] = re[30]
                    fleet['cargo_workers'] = re[31]
                    fleet['commandername'] = re[9]
                    if not re[9]:
                        fleet['commandername'] = ''
                    fleet['action'] = abs(re[34])
                    if re[3]:
                        fleet['action'] = "x"
                    if re[2]:
                        fleet['stance'] = 1
                    else:
                        fleet['stance'] = 0
                    if re[7]:
                        fleet['time'] = re[7]
                    else:
                        fleet['time'] = 0
                    # Assign fleet current planet
                    fleet['planetid'] = 0
                    fleet['g'] = 0
                    fleet['s'] = 0
                    fleet['p'] = 0
                    fleet['relation'] = 0
                    fleet['planetname'] = ""
                    if re[10]:
                        fleet['planetid'] = re[10]
                        fleet['g'] = re[12]
                        fleet['s'] = re[13]
                        fleet['p'] = re[14]
                        fleet['relation'] = re[17]
                        fleet['planetname'] = getPlanetName(request,re[17], re[35], re[16], re[11])
                        if not fleet['planetname']:
                            fleet['planetname'] = re[16]
                    # Assign fleet destination planet
                    fleet['t_planetid'] = 0
                    fleet['t_g'] = 0
                    fleet['t_s'] = 0
                    fleet['t_p'] = 0
                    fleet['t_relation'] = 0
                    fleet['t_planetname'] = ""
                    if re[18]:
                        fleet['t_planetid'] = re[18]
                        fleet['t_g'] = re[20]
                        fleet['t_s'] = re[21]
                        fleet['t_p'] = re[22]
                        fleet['t_relation'] = re[25]
                        fleet['t_planetname'] = getPlanetName(request,re[25], re[36], re[24], re[19])
                    for i in range(0, ShipListCount):
                        if ShipListArray[i][0] == re[0]:
                            fleet['ship'][i] = {
                                'ship_label':getShipLabel(ShipListArray[i][1]),
                                'ship_quantity': ShipListArray[i][2],
                            }
                    fleet['resource'][1]['res_id'] = 1
                    fleet['resource'][1]['res_quantity'] = re[27]
                    fleet['resource'][2]['res_id'] = 2
                    fleet['resource'][2]['res_quantity'] = re[28]
                    fleet['resource'][3]['res_id'] = 3
                    fleet['resource'][3]['res_quantity'] = re[29]
                    fleet['resource'][4]['res_id'] = 4
                    fleet['resource'][4]['res_quantity'] = re[30]
                    fleet['resource'][5]['res_id'] = 5
                    fleet['resource'][5]['res_quantity'] = re[31]
                    gcontext['list']['fleet'][re[0]] = fleet.copy()
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'alliance_fleets'
    if not gcontext['exile_user'].alliance_id:
        return HttpResponseRedirect(reverse('exile:alliance'))
    if not hasRight(request,"leader") and not hasRight(request,"can_order_other_fleets"):
        return HttpResponseRedirect(reverse('exile:alliance'))
    getAllyFleets()
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/alliance-fleets.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def alliancemembers(request):
    def displayMembers():
        try:
            col = int(request.GET.get("col", '1'))
        except (KeyError, Exception):
            col = 1
        if col < 1 or col > 7:
            col = 1
        reversed = False
        if col == 1:
                orderby = "upper(login)"
        elif col == 2:
                orderby = "score"
                reversed = True
        elif col == 3:
                orderby = "colonies"
                reversed = True
        elif col == 4:
                orderby = "credits"
                reversed = True
        elif col == 5:
                orderby = "lastactivity"
                reversed = True
        elif col == 6:
                orderby = "alliance_joined"
                reversed = True
        elif col == 7:
                orderby = "alliance_rank"
                reversed = False
        ParseR = False
        if request.GET.get("r", ""):
            reversed = not reversed
        else:
            ParseR = True
        if reversed:
            orderby += " DESC"
        orderby += ", upper(login)"
        # list ranks
        with connection.cursor() as cursor:
            gcontext['members'] = {'rank': {}}
            cursor.execute("SELECT id, rankid, label FROM alliances_ranks WHERE enabled AND allianceid=%s ORDER BY rankid", [gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            i = 0
            for re in res:
                gcontext['members']['rank'][re[0]] = {
                    "rank_id": re[1],
                    "rank_label": re[2],
                }
                i += 1
            # list members
            cursor.execute("SELECT login, CASE WHEN id=%s OR score_visibility >=1 THEN score ELSE 0 END AS score, int4((SELECT count(1) FROM nav_planet WHERE ownerid=users.id)) AS colonies," +
                " date_part('epoch', now()-lastactivity) / 3600, alliance_joined, alliance_rank, privilege, score-previous_score AS score_delta, id," +
                " sp_alliance_get_leave_cost(id), credits, score_visibility, orientation, COALESCE(date_part('epoch', leave_alliance_datetime-now()), 0), avatar_url" +
                " FROM users" +
                " WHERE alliance_id=%s" +
                " ORDER BY " + orderby, [gcontext['exile_user'].id, gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            if hasRight(request,"can_kick_player"):
                gcontext['members']['recruit'] = True
            else:
                gcontext['members']['viewonly'] = True
            if ParseR:
                gcontext['members']['r' + str(col)] = True
            totalColonies = 0 
            totalCredits = 0
            totalScore = 0
            totalScoreDelta = 0
            i = 0
            for re in res:
                totalColonies += re[2]
                totalCredits += re[10]
                member = {
                    "place": i+1,
                    "name": re[0],
                    "score": re[1],
                    "score_delta": re[7],
                    "stat_colonies": re[2],
                    "joined": re[4],
                    "rank": gcontext['members']['rank'][re[5]]["rank_id"],
                    "id": re[8],
                    "player": {},
                    "avatar": re[14],
                }
                if re[3]:
                    member["hours"] = int(re[3]) % 24
                    member["days"] = int(re[3] / 24)
                else:
                    member["hours"] = 0
                    member["days"] = 0
                member['player']["orientation" + str(re[12])] = True
                if re[5] > gcontext['exile_user'].alliance_rank.rankid and hasRight(request,"can_kick_player"):
                    member["kick_price"] = re[9]
                else:
                    member["kick_price"] = 0
                member["credits"] = re[10]
                if re[10] < 0:
                    member['player']['lowcredits'] = True
                if re[11] >= 1 or re[8] == gcontext['exile_user'].id:
                    totalScore += re[1]
                    totalScoreDelta += re[7]
                    if re[7] > 0:
                        member['player']['score'] = {"plus": True}
                    if re[7] < 0:
                        member['player']['score'] = {"minus": True}
                else:
                    member['player']['score_na'] = True
                if re[6] == -1:
                    member['player']['banned'] = True
                elif re[6] == -2:
                    member['player']['onholidays'] = True
                #less than 15mins ? = 1/4 h
                elif re[3]:
                    if re[3] < 0.25:
                        member['player']['online'] = True
                    elif re[3] < 1:
                        member['player']['less1h'] = True
                    elif re[3] < 1*24:
                        member['player']['hours'] = True
                    elif re[3] < 7*24:
                        member['player']['days'] = True
                    elif re[3] <= 14*24:
                        member['player']['1weekplus'] = True
                    elif re[3] > 14*24:
                        member['player']['2weeksplus'] = True
                if hasRight(request,"leader"):
                    if re[5] > gcontext['exile_user'].alliance_rank.rankid or re[8] == gcontext['exile_user'].id:
                        member['player']['manage'] = True
                    else:
                        member['player']['cant_manage'] = True
                if re[13] > 0:
                    member['player']["leaving"] = True
                    member['player']["leaving_time"] = re[13]
                elif re[13] == 0:
                    if hasRight(request,"can_kick_player"):
                        if re[5] > gcontext['exile_user'].alliance_rank.rankid:
                            member['player']["kick"] = True
                        else:
                            member['player']["cant_kick"] = True
                gcontext['members'][i] = member.copy()
                i += 1
            gcontext["total_colonies"] = totalColonies
            gcontext["total_credits"] = totalCredits
            gcontext["total_score"] = totalScore
            gcontext["total_score_delta"] = totalScoreDelta
            if totalScore != 0:
                if totalScoreDelta > 0:
                    gcontext["members"]["score"] = {"plus": True}
                if totalScoreDelta < 0:
                    gcontext["members"]["score"] = {"minus": True}
            else:
                gcontext["members"]["score_na"] = True
    def displayInvitations():
        if hasRight(request,"can_invite_player"):
            with connection.cursor() as cursor:
                gcontext['invitations'] = {'inv':{}}
                cursor.execute("SELECT recruit.login, created, recruiters.login, declined" +
                    " FROM alliances_invitations" +
                    "       INNER JOIN users AS recruit ON recruit.id = alliances_invitations.userid" +
                    "       LEFT JOIN users AS recruiters ON recruiters.id = alliances_invitations.recruiterid" +
                    " WHERE allianceid=%s" +
                    " ORDER BY created DESC", [gcontext['exile_user'].alliance_id])
                res = cursor.fetchall()
                i = 0
                for re in res:
                    invit = {
                        "name": re[0],
                        "date": re[1],
                        "recruiter": re[2],
                    }
                    if re[3]:
                        invit["declined"] = True
                    else:
                        invit["waiting"] = True
                    gcontext['invitations']['inv'][i] = invit.copy()
                    i = i + 1
                if i == 0:
                    gcontext['invitations']['noinvitations'] = True
                if gcontext['invitation_success'] != "":
                    gcontext['invitations']['message'] = {gcontext['invitation_success']: True}
                gcontext["player"] = username
    # Load template and display the right page
    def displayPage(cat):
        gcontext["cat"] = cat
        if cat == 1:
                displayMembers()
        elif cat == 2:
                displayInvitations()
        if hasRight(request,"can_invite_player"):
            gcontext['nav'] = {
                'cat1': {'fake':True},
                'cat2': {'fake':True},
            }
            gcontext['nav']['cat' + str(cat)]["selected"] = True
    def SaveRanks():
        # retrieve alliance members' id and assign new rank
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE alliance_id=%s", [gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            for re in res:
                try:
                    ar = int(request.POST.get('player' + str(re[0]), '100'))
                except (KeyError, Exception):
                    ar = 100
                print("UPDATE users SET alliance_rank=(SELECT id FROM alliances_ranks WHERE rankid="+str(ar)+" AND allianceid="+str(gcontext['exile_user'].alliance_id)+") WHERE id="+str(re[0])+" AND alliance_id="+str(gcontext['exile_user'].alliance_id)+" AND (alliance_rank > 0 OR id="+str(gcontext['exile_user'].id)+")")
                cursor.execute("UPDATE users SET alliance_rank=(SELECT id FROM alliances_ranks WHERE rankid=%s AND allianceid=%s) WHERE id=%s AND alliance_id=%s AND (alliance_rank > 0 OR id=%s)",
                    [ar, gcontext['exile_user'].alliance_id, re[0], gcontext['exile_user'].alliance_id, gcontext['exile_user'].id])
            # if leader demotes himself
            try:
                ar = int(request.POST.get('player' + str(gcontext['exile_user'].id), '0'))
            except (KeyError, Exception):
                ar = 0
            if ar > 0:
                return HttpResponseRedirect(reverse('exile:alliance'))
            return False
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'alliance_members'
    if not gcontext['exile_user'].alliance_id:
        return HttpResponseRedirect(reverse('exile:alliance'))
    if not hasRight(request,"leader") and not hasRight(request,"can_see_members_info"):
        return HttpResponseRedirect(reverse('exile:alliance'))
    gcontext['invitation_success'] = ""
    try:
        cat = int(request.GET.get("cat", 1))
    except (KeyError, Exception):
        cat = 1
    if cat not in [1, 2]:
        cat = 1
    # Process actions
    action = request.GET.get("a", "").strip()
    username = request.POST.get("name", "").strip()
    if cat == 1:
        if hasRight(request,"leader") and request.POST.get("submit", ""):
            r = SaveRanks()
            if r:
                return r
        if hasRight(request,"leader") or hasRight(request,"can_kick_player"):
            if action == "kick":
                username = request.GET.get("name", "").strip()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT sp_alliance_kick_member(%s, %s)", [gcontext['exile_user'].id, username])
    elif cat == 2 and username:
        if hasRight(request,"can_invite_player"):
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_alliance_invite(%s, %s)", [gcontext['exile_user'].id, username])
                res = cursor.fetchone()
                if res[0] ==  0:
                    gcontext['invitation_success'] = "ok"
                    username = ""
                elif res[0] == 1:
                    gcontext['invitation_success'] = "norights"
                elif res[0] == 2:
                    gcontext['invitation_success'] = "unknown"
                elif res[0] == 3:
                    gcontext['invitation_success'] = "already_member"
                elif res[0] == 5:
                    gcontext['invitation_success'] = "already_invited"
                elif res[0] == 6:
                    gcontext['invitation_success'] = "impossible"
    displayPage(cat)
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/alliance-members.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def alliancenaps(request):
    def displayNAPs():
        reversed = False
        gcontext["naps"] = {'nap':{}}
        try:
            col = int(request.GET.get("col","1"))
        except (KeyError, Exception):
            col = 1
        if col < 1 or col > 4:
            col = 1
        if col == 2:
            col = 1
        if col == 1:
            orderby = "tag"
    #   elif col == 2:
    #       orderby = "score"
    #       reversed = true
        elif col == 3:
            orderby = "created"
            reversed = True
        elif col == 4:
            orderby = "break_interval"
        elif col == 5:
            orderby = "share_locs"
        elif col == 6:
            orderby = "share_radars"
        if request.GET.get("r",""):
            reversed = not reversed
        else:
            gcontext["naps"]["r"+str(col)] = True
        if reversed:
            orderby += " DESC"
        orderby += ", tag"
        # List Non Aggression Pacts
        with connection.cursor() as cursor:
            cursor.execute("SELECT n.allianceid2, tag, name, " +
                " (SELECT COALESCE(sum(score)/1000, 0) AS score FROM users WHERE alliance_id=allianceid2), n.created, date_part('epoch', n.break_interval)::integer, date_part('epoch', break_on-now())::integer," +
                " share_locs, share_radars" +
                " FROM alliances_naps n" +
                "   INNER JOIN alliances ON (allianceid2 = alliances.id)" +
                " WHERE allianceid1=%s" +
                " ORDER BY " + orderby, [gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            i = 0
            for re in res:
                nap = {
                    "place": i+1,
                    "tag": re[1],
                    "name": re[2],
                    "score": re[3],
                    "created": re[4],
                }
                if not re[6]:
                    nap["break_interval"] = re[5]
                    nap["time"] = True
                else:
                    nap["break_interval"] = re[6]
                    nap["countdown"] = True
                if re[7]:
                    nap["locs_shared"] = True
                else:
                    nap["locs_not_shared"] = True
                if hasRight(request,"can_create_nap"):
                    nap["toggle_share_locs"] = True
                if re[8]:
                    nap["radars_shared"] = True
                else:
                    nap["radars_not_shared"] = True
                if hasRight(request,"can_create_nap"):
                    nap["toggle_share_radars"] = True
                if hasRight(request,"can_break_nap"):
                    if not re[6]:
                        nap["break"] = True
                    else:
                        nap["broken"] = True
                gcontext["naps"]['nap'][i] = nap.copy()
                i += 1
            if hasRight(request,"can_break_nap") and (i > 0):
                gcontext["naps"]["break"] = True
            if not i:
                gcontext["naps"]["nonaps"] = True
            if gcontext['break_success']:
                gcontext["naps"]["message"] = {gcontext['break_success']:True}
    def displayPropositions():
        # List NAPs that other alliances have offered
        with connection.cursor() as cursor:
            cursor.execute("SELECT alliances.tag, alliances.name, alliances_naps_offers.created, recruiters.login, declined, date_part('epoch', break_interval)::integer" +
                " FROM alliances_naps_offers" +
                "           INNER JOIN alliances ON alliances.id = alliances_naps_offers.allianceid" +
                "           LEFT JOIN users AS recruiters ON recruiters.id = alliances_naps_offers.recruiterid" +
                " WHERE targetallianceid=%s AND NOT declined" +
                " ORDER BY created DESC", [gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            i = 0
            gcontext["newnapps"] = {'proposition':{}}
            for re in res:
                napo = {
                    "tag": re[0],
                    "name": re[1],
                    "date": re[2],
                    "recruiter": re[3],
                    "break_interval": re[5],
                }
                if re[4]:
                    napo["declined"] = True
                else:
                    napo["waiting"] = True
                gcontext["newnapps"]["proposition"][i] = napo.copy()
                i += 1
            if not i:
                gcontext["newnapps"]["nopropositions"] = True
            if gcontext["nap_success"]:
                gcontext["newnapps"]["message"] = {gcontext["nap_success"]:True}
    def displayRequests():
        # List NAPs we proposed to other alliances
        with connection.cursor() as cursor:
            cursor.execute("SELECT alliances.tag, alliances.name, alliances_naps_offers.created, recruiters.login, declined, date_part('epoch', break_interval)::integer" +
                " FROM alliances_naps_offers" +
                "           INNER JOIN alliances ON alliances.id = alliances_naps_offers.targetallianceid" +
                "           LEFT JOIN users AS recruiters ON recruiters.id = alliances_naps_offers.recruiterid" +
                " WHERE allianceid=%s" +
                " ORDER BY created DESC", [gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            i = 0
            gcontext["newnaps"] = {'request':{}}
            for re in res:
                napp = {
                    "tag": re[0],
                    "name": re[1],
                    "date": re[2],
                    "recruiter": re[3],
                    "break_interval": re[5],
                }
                if re[4]:
                    napp["declined"] = True
                else:
                    napp["waiting"] = True
                gcontext["newnaps"]["request"][i] = napp.copy()
                i += 1
            if not i:
                gcontext["newnaps"]["norequests"] = True
            if gcontext["invitation_success"]:
                gcontext["newnaps"]["message"] = {gcontext["invitation_success"]:True}
            gcontext["tag"] = tag
            gcontext["hours"] = hours
    def displayPage(cat):
        gcontext["cat"] = cat
        if cat == 1:
            displayNAPs()
        elif cat == 2:
            displayPropositions()
        elif cat == 3:
            displayRequests()
        if hasRight(request,"can_create_nap") or hasRight(request,"can_break_nap"):
            with connection.cursor() as cursor:
                gcontext["nav"] = {'cat1':{},'cat2':{},'cat3':{}}
                cursor.execute("SELECT int4(count(*)) FROM alliances_naps_offers" +
                    " WHERE targetallianceid=%s AND NOT declined", [gcontext['exile_user'].alliance_id])
                re = cursor.fetchone()
                gcontext["propositions"] = re[0]
                if re[0] > 0:
                    gcontext["nav"]["cat2"]["propositions"] = True
                cursor.execute("SELECT int4(count(*)) FROM alliances_naps_offers" +
                        " WHERE allianceid=%s AND NOT declined", [gcontext['exile_user'].alliance_id])
                re = cursor.fetchone()
                gcontext["requests"] = re[0]
                if re[0] > 0:
                    gcontext["nav"]["cat3"]["requests"] = True
                gcontext["nav"]["cat" + str(cat)]["selected"] = True
                gcontext["nav"]["cat1"]['fake'] = True
                gcontext["nav"]["cat2"]['fake'] = True
                if hasRight(request,"can_create_nap"):
                    gcontext["nav"]["cat3"]['fake'] = True
    gcontext = request.session.get('gcontext',{})
    gcontext['invitation_success'] = gcontext['break_success'] = gcontext['nap_success'] = ""
    try:
        cat = int(request.GET.get("cat","1"))
    except (KeyError, Exception):
        cat = 1
    if cat < 1 or cat > 3:
        cat = 1
    if not hasRight(request,"can_create_nap") and cat == 3:
        cat = 1
    if not (hasRight(request,"can_create_nap") or hasRight(request,"can_break_nap")) and cat != 1:
        cat = 1
    # Process actions
    # redirect the player to the alliance page if he is not part of an alliance
    if not gcontext['exile_user'].alliance_id:
        return HttpResponseRedirect(reverse('exile:allaince'))
    action = request.GET.get("a","")
    targetalliancetag = request.GET.get("tag","").strip()
    tag = ""
    hours = 24
    if action == "accept":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_nap_accept(%s, %s)", [gcontext['exile_user'].id, targetalliancetag])
            re = cursor.fetchone()
            if re[0] == 0:
                gcontext['nap_success'] = "ok"
            elif re[0] == 5:
                gcontext['nap_success'] = "too_many"
    elif action == "decline":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_nap_decline(%s, %s)", [gcontext['exile_user'].id, targetalliancetag])
    elif action == "cancel":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_nap_cancel(%s, %s)", [gcontext['exile_user'].id, targetalliancetag])
    elif action == "sharelocs":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_nap_toggle_share_locs(%s, %s)", [gcontext['exile_user'].id, targetalliancetag])
    elif action == "shareradars":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_nap_toggle_share_radars(%s, %s)", [gcontext['exile_user'].id, targetalliancetag])
    elif action == "break":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_nap_break(%s, %s)", [gcontext['exile_user'].id, targetalliancetag])
            re = cursor.fetchone()
            if re[0] == 0:
                gcontext['break_success'] = "ok"
            elif re[0] == 1:
                gcontext['break_success'] = "norights"
            elif re[0] == 2:
                gcontext['break_success'] = "unknown"
            elif re[0] == 3:
                gcontext['break_success'] = "nap_not_found"
            elif re[0] == 4:
                gcontext['break_success'] = "not_enough_credits"
    elif action =="new":
        tag = request.POST.get("tag","").strip()
        try:
            hours = int(request.POST.get("hours", "0"))
        except (KeyError, Exception):
            hours = 0
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_nap_request(%s, %s, %s)", [gcontext['exile_user'].id, tag, hours])
            re = cursor.fetchone()
            if re[0] == 0:
                gcontext['invitation_success'] = "ok"
                tag = ""
                hours = 24
            elif re[0] == 1:
                gcontext['invitation_success'] = "norights"
            elif re[0] == 2:
                gcontext['invitation_success'] = "unknown"
            elif re[0] == 3:
                gcontext['invitation_success'] = "already_naped"
            elif re[0] == 4:
                gcontext['invitation_success'] = "request_waiting"
            elif re[0] == 6:
                gcontext['invitation_success'] = "already_requested"
    displayPage(cat)
    gcontext['selectedmenu'] = 'alliance_naps'
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/alliance-naps.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def alliancetributes(request):
    def displayTributesReceived():
        reversed = False
        gcontext["tributes_received"] = {'item':{}}
        try:
            col = int(request.GET.get("col",'1'))
        except (KeyError, Exception):
            col = 1
        if col < 1 or col > 2:
            col = 1
        if col == 1:
                orderby = "tag"
        elif col == 2:
                orderby = "created"
                reversed = True
        if request.GET.get("r",""):
            reversed = not reversed
        else:
            gcontext["tributes_received"]["r"+str(col)] = True
        if reversed:
            orderby += " DESC"
        orderby += ", tag"
        # List
        with connection.cursor() as cursor:
            cursor.execute("SELECT w.created, alliances.id, alliances.tag, alliances.name, w.credits, w.next_transfer" +
                " FROM alliances_tributes w" +
                "   INNER JOIN alliances ON (allianceid = alliances.id)" +
                " WHERE target_allianceid=%s" +
                " ORDER BY " + orderby, [gcontext['exile_user'].alliance_id])
            res =cursor.fetchall()
            i = 0
            for re in res:
                item = {
                    "place": i+1,
                    "created": re[0],
                    "tag": re[2],
                    "name": re[3],
                    "credits": re[4],
                    "next_transfer": re[5],
                }
                gcontext["tributes_received"]["item"][i] = item.copy()
                i += 1
            if i == 0:
                gcontext["tributes_received"]["none"] = True
    def displayTributesSent():
        reversed = False
        gcontext["tributes_sent"] = {'item':{}}
        try:
            col = int(request.GET.get("col",'1'))
        except (KeyError, Exception):
            col = 1
        if col < 1 or col > 2:
            col = 1
        if col == 1:
                orderby = "tag"
        elif col == 2:
                orderby = "created"
                reversed = True
        if request.GET.get("r",""):
            reversed = not reversed
        else:
            gcontext["tributes_sent"]["r"+str(col)] = True
        if reversed:
            orderby += " DESC"
        orderby += ", tag"
        # List
        with connection.cursor() as cursor:
            cursor.execute("SELECT w.created, alliances.id, alliances.tag, alliances.name, w.credits" +
                " FROM alliances_tributes w" +
                "   INNER JOIN alliances ON (target_allianceid = alliances.id)" +
                " WHERE allianceid=%s" +
                " ORDER BY " + orderby,  [gcontext['exile_user'].alliance_id])
            res =cursor.fetchall()
            i = 0
            for re in res:
                item = {
                    "place": i+1,
                    "created": re[0],
                    "tag": re[2],
                    "name": re[3],
                    "credits": re[4],
                }
                if hasRight(request,"can_break_nap"):
                    gcontext["tributes_sent"]["item"]["cancel"] = True
                gcontext["tributes_sent"]["item"][i] = item.copy()
                i += 1
            if hasRight(request,"can_break_nap") and (i > 0):
                gcontext["tributes_sent"]["cancel"] = True
            if i == 0:
                gcontext["tributes_sent"]["none"] = True
            if gcontext["cease_success"]:
                cgcontext["tributes_sent"]["message"] = {cease_success:True}
    def displayNew():
        gcontext['new'] = {'fake':True}
        if gcontext['invitation_success']:
            gcontext['new']['message'] = {gcontext['invitation_success']:True}
    def displayPage(cat):
        gcontext["cat"] = cat
        if cat == 1:
            displayTributesReceived()
        elif cat == 2:
            displayTributesSent()
        elif cat == 3:
            displayNew()
        gcontext['nav'] = {
            'cat1':{'fake':True},
            'cat2':{'fake':True},
        }
        if hasRight(request,"can_create_nap"):
            gcontext['nav']["cat3"] = {'fake':True}
        gcontext['nav']["cat"+str(cat)]["selected"] = True
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'alliance_tributes'
    gcontext['invitation_success'] = gcontext['cease_success'] = ""
    try:
        cat = int(request.GET.get("cat","1"))
    except (KeyError, Exception):
        cat = 1
    if cat < 1 or cat > 3:
        cat = 1
    if not (hasRight(request,"can_create_nap") or hasRight(request,"can_break_nap")) and cat == 3:
        cat = 1
    # Process actions
    # redirect the player to the alliance page if he is not part of an alliance
    if not gcontext['exile_user'].alliance_id:
        return HttpResponseRedirect(reverse('exile:alliance'))
    action = request.GET.get("a","")
    tag = ""
    credits = 0
    if action == "cancel":
        tag = request.GET.get("tag","").strip()
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_tribute_cancel(%s, %s)", [gcontext['exile_user'].id, tag])
            re = cursor.fetchone()
            if re[0] == 0:
                gcontext['cease_success'] = "ok"
            elif re[0] == 1:
                gcontext['cease_success'] = "norights"
            elif re[0] == 2:
                gcontext['cease_success'] = "unknown"
    if action == "new":
        tag = request.POST.get("tag","").strip()
        try:
            credits = int(request.POST.get("credits", '0'))
        except (KeyError, Exception):
            credits = 0
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_tribute_new(%s, %s, %s)", [gcontext['exile_user'].id, tag, credits])
            re = cursor.fetchone()
            if re[0] == 0:
                gcontext['invitation_success'] = "ok"
                tag = ""
            elif re[0] == 1:
                gcontext['invitation_success'] = "norights"
            elif re[0] == 2:
                gcontext['invitation_success'] = "unknown"
            elif re[0] == 3:
                gcontext['invitation_success'] = "already_exists"
    gcontext['tag'] = tag
    gcontext['credits'] = credits
    displayPage(cat)
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/alliance-tributes.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def alliancewars(request):
    def displayWars():
        reversed = False
        gcontext['wars'] = {}
        try:
            col = int(request.GET.get("col","1"))
        except (KeyError, Exception):
            col = 1
        if col < 1 or col > 2:
            col = 1
        if col == 1:
            orderby = "tag"
        elif col == 2:
            orderby = "created"
            reversed = True
        if request.GET.get("r",""):
            reversed = not reversed
        else:
            gcontext['wars']["r"+str(col)] = True
        if reversed:
            orderby += " DESC"
        orderby += ", tag"
        # List wars
        with connection.cursor() as cursor:
            cursor.execute("SELECT w.created, alliances.id, alliances.tag, alliances.name, cease_fire_requested, date_part('epoch', cease_fire_expire-now())::integer, w.can_fight < now() AS can_fight, true AS attacker, next_bill < now() + INTERVAL '1 week', sp_alliance_war_cost(allianceid2), next_bill" +
                " FROM alliances_wars w" +
                "   INNER JOIN alliances ON (allianceid2 = alliances.id)" +
                " WHERE allianceid1=%s" +
                " UNION " +
                "SELECT w.created, alliances.id, alliances.tag, alliances.name, cease_fire_requested, date_part('epoch', cease_fire_expire-now())::integer, w.can_fight < now() AS can_fight, false AS attacker, false, 0, next_bill" +
                " FROM alliances_wars w" +
                "   INNER JOIN alliances ON (allianceid1 = alliances.id)" +
                " WHERE allianceid2=%s" +
                " ORDER BY " + orderby, [gcontext['exile_user'].alliance_id, gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            i = 0
            gcontext['wars']['war'] = {}
            for re in res:
                war = {
                    "place": i+1,
                    "created": re[0],
                    "tag": re[2],
                    "name": re[3],
                }
                if hasRight(request,"can_break_nap"):
                    if not re[4]:
                        if re[7]:
                            if re[8]:
                                war["cost"] = re[9]
                                war["extend"] = True
                            war["stop"] = True
        #               else:
        #                   war["surrender"] = True
                    elif re[4] == gcontext['exile_user'].alliance_id:
                        war["time"] = re[5]
                        war["ceasing"] = True
                    else:
                        war["time"] = re[5]
                        war["cease_requested"] = True
                if re[6]:
                    war["next_bill"] = re[10]
                    if re[10]:
                        war["can_fight"] = True
                else:
                    war["cant_fight"] = True
                gcontext['wars']['war'][i] = war.copy()
                i += 1
            if hasRight(request,"can_break_nap") and (i > 0):
                gcontext['wars']['cease'] = True
            if i == 0:
                gcontext['wars']['nowars'] = True
            if gcontext['cease_success']:
                gcontext['wars']['message'] = {gcontext['cease_success']:True}
    def displayDeclaration():
        gcontext["newwar"] = {'fake':True}
        if request.GET.get("a","") == "new":
            tag = request.POST.get("tag").strip()
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, tag, name, sp_alliance_war_cost(id) + (const_coef_score_to_war()*sp_alliance_value(%s))::integer FROM alliances WHERE lower(tag)=lower(%s)", [gcontext['exile_user'].alliance_id, tag])
                re = cursor.fetchone()
                gcontext["newwar"] = {}
                if not re:
                    gcontext["tag"] = tag
                    gcontext["newwar"]['message'] = {'unknown':True}
                elif re[0] == gcontext['exile_user'].alliance_id:
                    gcontext["newwar"]['message'] = {'self':True}
                    gcontext["tag"] = tag
                else:
                    gcontext["tag"] = re[1]
                    gcontext["name"] = re[2]
                    gcontext["cost"] = re[3]
                    gcontext["newwar_confirm"] = True
        else:
            if gcontext["result"]:
                gcontext["newwar"]["message"] = {gcontext["result"]:True}
                gcontext["tag"] = tag
    def displayPage(cat):
        gcontext["cat"] = cat
        if cat == 1:
            displayWars()
        elif cat == 2:
            displayDeclaration()
        gcontext['nav'] = {'cat1':{'fake':True}}
        if hasRight(request,"can_create_nap"):
            gcontext['nav']["cat2"] = {'fake':True}
        gcontext['nav']["cat"+str(cat)]["selected"] = True
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'alliance_wars'
    gcontext['result'] = gcontext['cease_success'] = ""
    try:
        cat = int(request.GET.get("cat", "1"))
    except (KeyError, Exception):
        cat = 1
    if cat < 1 or cat > 2:
        cat = 1
    if not (hasRight(request,"can_create_nap") or hasRight(request,"can_break_nap")) and cat != 1:
        cat = 1
    # Process actions
    # redirect the player to the alliance page if he is not part of an alliance
    if not gcontext['exile_user'].alliance_id:
        return HttpResponseRedirect(reverse('exile:alliance'))
    action = request.GET.get("a","").strip()
    tag = ""
    if action == "pay":
        tag = request.GET.get("tag","").strip()
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_war_pay_bill(%s, %s)", [gcontext['exile_user'].id, tag])
            re = cursor.fetchone()
            if re[0] == 0:
                gcontext['cease_success'] = "ok"
            elif re[0] == 1:
                gcontext['cease_success'] = "norights"
            elif re[0] == 2:
                gcontext['cease_success'] = "unknown"
            elif re[0] == 3:
                gcontext['cease_success'] = "war_not_found"
    elif action == "stop":
        tag = request.GET.get("tag","").strip()
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_war_stop(%s, %s)", [gcontext['exile_user'].id, tag])
            re = cursor.fetchone()
            if re[0] == 0:
                gcontext['cease_success'] = "ok"
            elif re[0] == 1:
                gcontext['cease_success'] = "norights"
            elif re[0] == 2:
                gcontext['cease_success'] = "unknown"
            elif re[0] == 3:
                gcontext['cease_success'] = "war_not_found"
    elif action == "new2":
        tag = request.POST.get("tag","").strip()
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_war_declare(%s, %s)", [gcontext['exile_user'].id, tag])
            re = cursor.fetchone()
            if re[0] == 0:
                gcontext['result'] = "ok"
                tag = ""
            elif re[0] == 1:
                gcontext['result'] = "norights"
            elif re[0] == 2:
                gcontext['result'] = "unknown"
            elif re[0] == 3:
                gcontext['result'] = "already_at_war"
            elif re[0] == 9:
                gcontext['result'] = "not_enough_credits"
    gcontext['tag'] = tag
    displayPage(cat)
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/alliance-wars.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def alliancewallet(request):
    def can_give_money():
        with connection.cursor() as cursor:
            cursor.execute("SELECT game_started < now() - INTERVAL '2 weeks' FROM users WHERE id=%s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            if re and re[0]:
                return True
        return False
    # Display the wallet page
    def DisplayPage(cat):
        gcontext['walletpage'] = cat
        with connection.cursor() as cursor:
            cursor.execute("SELECT credits, tax FROM alliances WHERE id=%s", [gcontext['exile_user'].alliance_id])
            re = cursor.fetchone()
            gcontext["credits"] = re[0]
            gcontext["tax"] = re[1]/10
            if len(checkPlanetListCache(request)) < 2:
                gcontext["notax"] = True
            cursor.execute("SELECT COALESCE(sum(credits), 0) FROM alliances_wallet_journal WHERE allianceid=%s AND datetime >= now()-INTERVAL '24 hours'", [gcontext['exile_user'].alliance_id])
            gcontext["last24h"] = re[0]
            if gcontext["money_error"] == e_not_enough_money:
                gcontext["not_enough_money"] = True
            elif gcontext["money_error"] == e_can_give_money_after_a_week:
                gcontext["can_give_money_after_a_week"] = True
            elif gcontext["money_error"] == e_little_vilain:
                gcontext["little_vilain"] = True
            gcontext["cat1"] = {'fake':True}
            if hasRight(request,"can_ask_money"):
                gcontext["cat2"] = {'fake':True}
            gcontext["cat3"] = {'fake':True}
            if hasRight(request,"can_change_tax_rate"):
                gcontext["cat4"] = {'fake':True}
            if hasRight(request,"leader"):
                gcontext["cat5"] = {'fake':True}
            gcontext["cat"+str(cat)]["selected"] = True
            t = loader.get_template(gcontext['wallet_tpl'])
            gcontext["content2"] = t.render(gcontext, request)
    # Display a journal of the last money operations
    # This is viewable by everybody
    def DisplayJournal(cat):
        gcontext['wallet_tpl'] = 'exile/alliance-wallet-journal.html'
        gcontext["walletpage"] = cat
        reversed = False
        try:
            col = int(request.GET.get("col","1"))
        except (KeyError, Exception):
            col = 1
        if col < 1 or col > 4:
            col = 1
        if col == 1:
            orderby = "datetime"
            reversed = True
        elif col == 2:
            orderby = "type"
            reversed = True
        elif col == 3:
            orderby = "upper(source)"
            reversed = True
        elif col == 4:
            orderby = "upper(destination)"
            reversed = True
        elif col == 5:
            orderby = "credits"
        elif col == 6:
            orderby = "upper(description)"
        if request.GET.get("r"):
            reversed = not reversed
        else:
            gcontext["r"+str(col)] = True
        if reversed:
            orderby += " DESC"
        orderby += ", datetime DESC"
        if request.POST.get("refresh",""):
            displayGiftsRequests = bool(request.POST.get("gifts",""))
            displaySetTax = bool(request.POST.get("settax",""))
            displayTaxes = bool(request.POST.get("taxes",""))
            displayKicksBreaks = bool(request.POST.get("kicksbreaks",""))
            with connection.cursor() as cursor:
                cursor.execute("UPDATE users SET" +
                    " wallet_display[1]=%s" +
                    " ,wallet_display[2]=%s" +
                    " ,wallet_display[3]=%s" +
                    " ,wallet_display[4]=%s" +
                    " WHERE id=%s", [displayGiftsRequests, displaySetTax, displayTaxes, displayKicksBreaks, gcontext['exile_user'].id])
        else:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COALESCE(wallet_display[1], true)," +
                    " COALESCE(wallet_display[2], true)," +
                    " COALESCE(wallet_display[3], true)," +
                    " COALESCE(wallet_display[4], true)" +
                    " FROM users" +
                    " WHERE id=%s", [gcontext['exile_user'].id])
                re = cursor.fetchone()
                displayGiftsRequests = re[0]
                displaySetTax = re[1]
                displayTaxes = re[2]
                displayKicksBreaks = re[3]
        if displayGiftsRequests:
            gcontext["gifts_checked"] = True
        if displaySetTax:
            gcontext["settax_checked"] = True
        if displayTaxes:
            gcontext["taxes_checked"] = True
        if displayKicksBreaks:
            gcontext["kicksbreaks_checked"] = True
        query = ""
        if not displayGiftsRequests:
            query += " AND type <> 0 AND type <> 3 AND type <> 20"
        if not displaySetTax:
            query += " AND type <> 4"
        if not displayTaxes:
            query += " AND type <> 1"
        if not displayKicksBreaks:
            query += " AND type <> 2 AND type <> 5 AND type <> 10 AND type <> 11"
        # List wallet journal
        with connection.cursor() as cursor:
            cursor.execute("SELECT Max(datetime), userid, int4(sum(credits)), description, source, destination, type, groupid" +
                " FROM alliances_wallet_journal" +
                " WHERE allianceid=%s" + query + " AND datetime >= now()-INTERVAL '1 week'" +
                " GROUP BY userid, description, source, destination, type, groupid" +
                " ORDER BY Max(datetime) DESC" +
                " LIMIT 500", [gcontext['exile_user'].alliance_id])
            res =cursor.fetchall()
            if not res:
                gcontext["noentries"] = True
            i = 1
            gcontext['entry'] = {}
            for re in res:
                entry = {
                    "date": re[0],
                    "description": re[3],
                    "source": re[4],
                    "destination": re[5],
                }
                if re[2] > 0:
                    entry["income"] = re[2]
                    entry["outcome"] = 0
                else:
                    entry["income"] = 0
                    entry["outcome"] = -re[2]
                if re[6] == 0: # gift
                    entry["gift"] = True
                elif re[6] == 1: # tax
                    entry["tax"] = True
                elif re[6] == 2:
                    entry["member_left"] = True
                elif re[6] == 3:
                    entry["money_request"] = True
                elif re[6] == 4:
                    r = int(re[3])/10
                    entry["description"] = str(r) + " %"
                    entry["taxchanged"] = True
                elif re[6] == 5:
                    entry["member_kicked"] = True
                elif re[6] == 10:
                    entry["nap_broken"] = True
                elif re[6] == 11:
                    entry["nap_broken"] = True
                elif re[6] == 12:
                    entry["war_cost"] = True
                elif re[6] == 20:
                    entry["tribute"] = True
                
        #       content.Parse "entry.type" & re[5]
                gcontext['entry'][i] = entry.copy()
                i += 1
            DisplayPage(cat)
    # Display the requests page
    # Allow a player to request money from his alliance
    # Treasurer and Leader can see the list of request and accept/deny them
    def DisplayRequests(cat):
        gcontext['wallet_tpl'] = 'exile/alliance-wallet-requests.html'
        gcontext["walletpage"] = cat
        with connection.cursor() as cursor:
            cursor.execute("SELECT credits FROM users WHERE id=%s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            credits = re[0]
            gcontext["player_credits"] = credits
            cursor.execute("SELECT credits, description, result" +
                    " FROM alliances_wallet_requests" +
                    " WHERE allianceid=%s AND userid=%s", [gcontext['exile_user'].alliance_id, gcontext['exile_user'].id])
            re = cursor.fetchone()
            gcontext["request"] = {}
            if not re:
                gcontext["request"]["none"] = True
            else:
                gcontext["request"]["credits"] = re[0]
                gcontext["request"]["description"] = re[1]
                if re[2] != None and not re[2]:
                    gcontext["request"]["denied"] = True
                else:
                    gcontext["request"]["submitted"] = True
            if hasRight(request,"can_accept_money_requests"):
                # List money requests
                cursor.execute("SELECT r.id, datetime, login, r.credits, r.description" +
                        " FROM alliances_wallet_requests r" +
                        "   INNER JOIN users ON users.id=r.userid" +
                        " WHERE allianceid=%s AND result IS NULL", [gcontext['exile_user'].alliance_id])
                res = cursor.fetchall()
                i = 0
                gcontext['list'] = {'entry':{}}
                for re in res:
                    entry = {
                        "id": re[0],
                        "date": re[1],
                        "nation": re[2],
                        "credits": re[3],
                        "description": re[4],
                    }
                    gcontext['list']['entry'][i] = entry.copy()
                    i += 1
                if not i:
                    gcontext['list']["norequests"] = True
            DisplayPage(cat)
    def DisplayGifts(cat):
        gcontext['wallet_tpl'] = 'exile/alliance-wallet-give.html'
        gcontext["walletpage"] = cat
        with connection.cursor() as cursor:
            cursor.execute("SELECT credits FROM users WHERE id=%s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            gcontext["player_credits"] = re[0]
            if can_give_money():
                gcontext["give"] = {"can_give":True}
            else:
                gcontext["give"] = {"can_give_after_a_week":True}
            if hasRight(request,"can_accept_money_requests"):
                # list gifts for the last 7 days
                cursor.execute("SELECT datetime, credits, source, description" +
                    " FROM alliances_wallet_journal" +
                    " WHERE allianceid=%s AND type=0 AND datetime >= now()-INTERVAL '1 week'" +
                    " ORDER BY datetime DESC", [gcontext['exile_user'].alliance_id])
                res = cursor.fetchall()
                gcontext["list"] = {'entry':{}}
                if not res:
                    gcontext["list"]["noentries"] = True
                i = 0
                for re in res:
                    entry = {
                        "date": re[0],
                        "credits": re[1],
                        "nation": re[2],
                        "description": re[3],
                    }
                    gcontext["list"]['entry'][i] = entry.copy()
                    i += 1
            DisplayPage(cat)
    # Display the tax rates page, only viewable by treasurer and leader
    def DisplayTaxRates(cat):
        gcontext['wallet_tpl'] = 'exile/alliance-wallet-taxrates.html'
        gcontext["walletpage"] = cat
        with connection.cursor() as cursor:
            cursor.execute("SELECT tax FROM alliances WHERE id=%s", [gcontext['exile_user'].alliance_id])
            re = cursor.fetchone()
            taxe = re[0]
            # List available taxes
            gcontext['taxes'] = {}
            for i in range(21):
                tax = {
                    "tax": i*0.5,
                    "taxrates": i*5,
                }
                if i*5 == taxe:
                    tax["selected"] = True
                gcontext['taxes'][i] = tax.copy()
            DisplayPage(cat)
    def log10(n):
        return math.log(n) / math.log(100000)
    # Display credits income/outcome historic
    def DisplayHistoric(cat):
        gcontext['wallet_tpl'] = 'exile/alliance-wallet-historic.html'
        gcontext["walletpage"] = cat
        with connection.cursor() as cursor:
            cursor.execute("SELECT date_trunc('day', datetime), int4(sum(GREATEST(0, credits))), int4(-sum(LEAST(0, credits)))" +
                " FROM alliances_wallet_journal" +
                " WHERE allianceid=%s" +
                " GROUP BY date_trunc('day', datetime)" +
                " ORDER BY date_trunc('day', datetime)", [gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            maxValue = 0
            avgValue = 0
            for re in res:
                if re[1] > maxValue:
                    maxValue = re[1]
                if re[2] > maxValue:
                    maxValue = re[2]
                avgValue = avgValue + re[1] + re[2]
            if len(res):
                avgValue = avgValue / (len(res)*2)
            gcontext['day'] = {}
            i = 0
            for re in res:
                day = {
                    "income_height": int(400 * re[1] / maxValue),
                    "outcome_height": int(400 * re[2] / maxValue),
                    "income": re[1],
                    "outcome": re[2],
                    "datetime": re[0],
                }
                gcontext['day'][i] = day.copy()
                i += 1
            DisplayPage(cat)
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'alliance_wallet'
    selected_menu = "alliance.wallet"
    e_no_error = 0
    e_not_enough_money = 1
    e_can_give_money_after_a_week = 2
    e_little_vilain = 3
    gcontext["money_error"] = e_no_error
    if not gcontext['exile_user'].alliance_id:
        return HttpResponseRedirect(reverse('exile:overview'))
    # accept/deny money request
    action = request.GET.get("a","")
    idd = request.GET.get("id",0)
    if action == "accept":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_money_accept(%s, %s)", [gcontext['exile_user'].id, idd])
    elif action == "deny":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_money_deny(%s, %s)", [gcontext['exile_user'].id, idd])
    # player gives or requests credits
    try:
        gcontext['credit'] = int(request.POST.get("credits", "0"))
    except (KeyError, Exception):
        gcontext['credit'] = 0
    if gcontext['credit'] < 0:
        gcontext['credit'] = 0
        gcontext["money_error"] = e_little_vilain
    description = strip_tags(request.POST.get("description","").strip())
    if request.POST.get("cancel"):
        gcontext['credit'] = 0
        description = ""
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_money_request(%s, %s, %s)", [gcontext['exile_user'].id, gcontext['credit'], description])
    if gcontext['credit']:
        if request.POST.get("request",""):
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_alliance_money_request(%s, %s, %s)", [gcontext['exile_user'].id, gcontext['credit'], description])
        elif request.POST.get("give","") and (gcontext['credit'] > 0):
            if can_give_money():
                with connection.cursor() as cursor:
                    cursor.execute("SELECT sp_alliance_transfer_money(%s, %s, %s, 0)", [gcontext['exile_user'].id, gcontext['credit'], description])
                    re = cursor.fetchone()
                    if re[0]:
                        gcontext["money_error"] = e_not_enough_money
            else:
                gcontext["money_error"] = e_can_give_money_after_a_week
    # change of tax rates
    try:
        taxrates = int(request.POST.get("taxrates", "0"))
    except (KeyError, Exception):
        taxrates = 0
    if taxrates:
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_set_tax(%s, %s)", [gcontext['exile_user'].id, taxrates])
    # retrieve which page is displayed
    try:
        category = int(request.GET.get("cat", "1"))
    except (KeyError, Exception):
        category = 1
    if not hasRight(request,"can_ask_money") and category == 2:
        category = 1
    if not hasRight(request,"can_change_tax_rate") and category == 4:
        category = 1
    if category == 2:
        DisplayRequests(2)
    elif category == 3:
        DisplayGifts(3)
    elif category == 4:
        DisplayTaxRates(4)
    elif category == 5:
        DisplayHistoric(5)
    else:
        DisplayJournal(1)
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/alliance-wallet.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def alliancereports(request):
    # display list of messages
    def display_reports(cat):
        # Limit the list to the current category or only display 100 reports if no categories specified
        if cat == 0:
            query = " ORDER BY datetime DESC LIMIT 200"
        else:
            query = " AND type = " + str(cat) + " ORDER BY datetime DESC LIMIT 200"
        with connection.cursor() as cursor:
            cursor.execute("SELECT type, subtype, datetime, battleid, fleetid, fleet_name," +
                " planetid, planet_name, galaxy, sector, planet," +
                " researchid, 0, read_date," +
                " planet_relation, planet_ownername," +
                " ore, hydrocarbon, credits, scientists, soldiers, workers, username," +
                " alliance_tag, alliance_name," +
                " invasionid, spyid, spy_key, description, ownerid, invited_username, login, buildingid" +
                " FROM vw_alliances_reports" +
                " WHERE ownerallianceid = %s" + query, [gcontext['exile_user'].alliance_id])
            res = cursor.fetchall()
            gcontext["tabnav"] = {
                "000": {'fake':True},
                "100": {'fake':True},
                "200": {'fake':True},
                "800": {'fake':True},
            }
            gcontext["tabnav"][str(cat)+"00"]["selected"] = True
            if not res:
                gcontext["noreports"] = True
            # List the reports returned by the query
            gcontext['messages'] = {}
            i = 0
            for re in res:
                msg = {
                    "ownerid": re[29],
                    "invitedusername": re[30],
                    "nation": re[31],
                    "type": re[0]*100+re[1],
                    "date": re[2],
                    "battleid": re[3],
                    "fleetid": re[4],
                    "fleetname": re[5],
                    "planetid": re[6],
                    "researchid": re[11],
                    "ore": re[16],
                    "hydrocarbon": re[17],
                    "credits": re[18],
                    "scientists": re[19],
                    "soldiers": re[20],
                    "workers": re[21],
                    "username": re[22],
                    "alliancetag": re[23],
                    "alliancename": re[24],
                    "invasionid": re[25],
                    "spyid": re[26],
                    "spykey": re[27],
                    "description": re[28],
                    "type": re[0]*100+re[1],
                }
                if re[14] == config.rHostile or re[14] == config.rWar:
                    msg["planetname"] = re[15]
                elif re[14] == config.rFriend or re[14] == config.rAlliance or re[14] == config.rSelf:
                    msg["planetname"] = re[7]
                else:
                    msg["planetname"] = ""
                # assign planet coordinates
                if re[8]:
                    msg["g"] = re[8]
                    msg["s"] = re[9]
                    msg["p"] = re[10]
                if re[11]:
                    msg["researchname"] = getResearchLabel(re[11])
                #if not re[13]:
                #    msg["new"] = True
                if re[32]:
                    msg["building"] = getBuildingLabel(re[32])
                gcontext['messages'][i] = msg.copy()
                i += 1
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'alliance_reports'
    try:
        cat = int(request.GET.get("cat", "0"))
    except (KeyError, Exception):
        cat = 0
    if not gcontext['exile_user'].alliance_id:
        return HttpResponseRedirect(reverse('exile:alliance'))
    if not hasRight(request,"can_see_reports"):
        return HttpResponseRedirect(reverse('exile:alliance'))
    display_reports(cat)
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/reports.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def allianceinvitations(request):
    def DisplayInvitations():
        with connection.cursor() as cursor:
            cursor.execute("SELECT date_part('epoch', const_interval_before_join_new_alliance()) / 3600")
            res =cursor.fetchone()
            gcontext["hours_before_rejoin"] = res[0]
            cursor.execute("SELECT alliances.tag, alliances.name, alliances_invitations.created, users.login" +
                    " FROM alliances_invitations" +
                    "       INNER JOIN alliances ON alliances.id = alliances_invitations.allianceid" +
                    "       LEFT JOIN users ON users.id = alliances_invitations.recruiterid" +
                    " WHERE userid=%s AND NOT declined" +
                    " ORDER BY created DESC", [gcontext['exile_user'].id])
            res =cursor.fetchall()
            i = 0
            gcontext['invitation'] = {}
            for re in res:
                invitation = {
                    "tag": re[0],
                    "name": re[1],
                    "date": re[2],
                    "recruiter": re[3],
                }
                created = re[2]
                if gcontext["can_join_alliance"]:
                    if gcontext['exile_user'].alliance_id:
                        invitation['cant_accept'] = True
                    else:
                        invitation['accept'] = True
                else:
                    invitation['cant_join'] = True
                gcontext['invitation'][i] = invitation.copy()
                i += 1
            if invitation_status != "":
                gcontext['invitation_status'] = invitation_status
            if i == 0:
                gcontext["noinvitations"] = True
            # Parse "cant_join" section if the player can't create/join an alliance
            if not gcontext["can_join_alliance"]:
                gcontext["cant_join"] = True
            # Display the "leave" section if the player is in an alliance
            if gcontext['exile_user'].alliance_id and gcontext["can_join_alliance"]:
                cursor.execute("SELECT sp_alliance_get_leave_cost(%s)", [gcontext['exile_user'].id])
                res = cursor.fetchone()
                request.session[sLeaveCost] = res[0]
                if request.session.get(sLeaveCost) < 2000:
                    request.session[sLeaveCost] = 0
                gcontext["credits"] = request.session.get(sLeaveCost)
                gcontext['leave'] = {}
                if request.session.get(sLeaveCost) > 0:
                    gcontext["leave"]["charges"] = True
                if leave_status != "":
                    gcontext["leave"][leave_status] = True
        FillHeaderCredits(request)
    gcontext = request.session.get('gcontext',{})
    if not gcontext['exile_user'].alliance_id:
        gcontext['selectedmenu'] = 'noalliance_invitations'
    else:
        gcontext['selectedmenu'] = 'alliance_invitations'
    sLeaveCost = "leavealliancecost"
    leave_status = ""
    invitation_status = ""
    action = request.GET.get("a", "").strip()
    alliance_tag = request.GET.get("tag", "").strip()
    if action == "accept":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_accept_invitation(%s, %s)", [gcontext['exile_user'].id, alliance_tag])
            res = cursor.fetchone()
            if res[0] == 0:
                return HttpResponseRedirect(reverse('exile:alliance'))
            elif res[0] == 4:
                invitation_status = "max_members_reached"
            elif res[0] == 6:
                invitation_status = "cant_rejoin_previous_alliance"
    elif action == "decline":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_alliance_decline_invitation(%s, %s)", [gcontext['exile_user'].id, alliance_tag])
    elif action == "leave":
        if request.session.get(sLeaveCost, "") and request.POST.get("leave") == 1:
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_alliance_leave(%s, %s)", [gcontext['exile_user'].id, request.session.get(sLeaveCost)])
                res = cursor.fetchone()
                if res[0] == 0:
                    return HttpResponseRedirect(reverse('exile:alliance'))
                else:
                    leave_status = "not_enough_credits"
    DisplayInvitations()
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/alliance-invitations.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def alliancecreate(request):
    def isValidAllianceTag(tag):
        if len(tag) < 2 or len(tag) > 4:
            return False
        else:
            return tag.isalnum()
    def isValidDescription(description):
         return len(description) < 8192
    def DisplayAllianceCreate():
        if gcontext['can_join_alliance']:
            if create_result == -2:
                gcontext["name_already_used"] = True
            if create_result == -3:
                gcontext["tag_already_used"] = True
            if not valid_name:
                gcontext["invalid_name"] = True
            if not valid_tag:
                gcontext["invalid_tag"] = True
            gcontext["name"] = name
            gcontext["tag"] = tag
            gcontext["description"] = description
            gcontext["create"] = True
        else:
            gcontext["cant_create"] = True
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'noalliance_create'
    name = ""
    tag = ""
    description = ""
    valid_name = True
    valid_tag = True
    valid_description = True
    create_result = 0
    if request.GET.get("a", "") == "new":
        name = request.POST.get("alliancename", "").strip()
        tag = request.POST.get("alliancetag", "").strip()
        description = strip_tags(request.POST.get("description", "").strip())
        valid_name = isValidName(name,32)
        valid_tag = gcontext['exile_user'].privilege > 100 or isValidAllianceTag(tag)
        valid_description = isValidDescription(description)
        if valid_name and valid_tag:
            with connection.cursor() as cursor:
                cursor.execute("SELECT sp_create_alliance(%s, %s, %s, %s)", [gcontext['exile_user'].id, name, tag, description])
                res = cursor.fetchone()
                create_result = res[0]
                if create_result >= -1:
                    return HttpResponseRedirect(reverse('exile:alliance'))
    DisplayAllianceCreate()
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/alliance-create.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def map(request):
    def GetSector(sector, shiftX, shiftY):
        if (sector % 10 == 0) and (shiftX > 0):
            shiftX = 0
        if (sector % 10 == 1) and (shiftX < 0):
            shiftX = 0
        if (sector < 11) and (shiftY < 0):
            shiftY = 0
        if (sector > 90) and (shiftY > 0):
            shiftY = 0
        s = sector + shiftX + shiftY*10
        if s > 99:
            s = 99
        return s
    def displayRadar(galaxy, sector, radarstrength):
        with connection.cursor() as cursor:
            cursor.execute('SELECT v.id, v.name, attackonsight, engaged, size, signature, speed, remaining_time, ' +
                ' ownerid, owner_name, owner_relation, ' +
                ' planetid, planet_name, planet_galaxy, planet_sector, planet_planet, ' +
                ' planet_ownerid, planet_owner_name, planet_owner_relation, ' +
                ' destplanetid, destplanet_name, destplanet_galaxy, destplanet_sector, destplanet_planet, ' +
                ' destplanet_ownerid, destplanet_owner_name, destplanet_owner_relation, total_time, ' +
                ' from_radarstrength, to_radarstrength, alliances.tag, radar_jamming, destplanet_radar_jamming ' +
                ' FROM vw_fleets_moving v ' +
                '   LEFT JOIN alliances ON alliances.id = owner_alliance_id ' +
                ' WHERE userid=%(userid)s AND ( ' +
                '   (planetid >= sp_first_planet(%(galaxy)s,%(sector)s) AND planetid <= sp_last_planet(%(galaxy)s,%(sector)s)) OR ' +
                '   (destplanetid >= sp_first_planet(%(galaxy)s,%(sector)s) AND destplanetid <= sp_last_planet(%(galaxy)s,%(sector)s))) ' +
                ' ORDER BY remaining_time', {'userid': gcontext['exile_user'].id, 'galaxy': galaxy, 'sector': sector})
            res = cursor.fetchall()
            relation = -100 # -100 = do not display the fleet
            loosing_time = 0 # seconds before our radar loses the fleet
            remaining_time = 0 # seconds before the fleet ends its travel
            movement_type = ""
            movingfleetcount = 0 # fleets moving inside the sector
            enteringfleetcount = 0 # fleets entering the sector
            leavingfleetcount = 0 # fleets leaving the sector
            gcontext['radar'] = {
                'moving': {'fleet': {}},
                'leaving': {'fleet': {}},
                'entering': {'fleet': {}},
            }
            i=0
            for re in res:
                relation = re[10]
                remaining_time = re[7]
                loosing_time = -1
                display_from = True
                display_to = True
                # do not display NAP/enemy fleets moving to/from unknown planet if fleet is not within radar range
                if relation <= config.rFriend:
                    # compute how far our radar can detect fleets
                    # highest radar strength * width of a sector / speed * nbr of second in one hour
                    radarSpotting = math.sqrt(radarstrength)*6*1000/re[6]*3600
                    if re[28] == 0:
                        if re[7] < radarSpotting:
                            # incoming fleet is detected by our radar
                            display_from = False
                        else:
                            relation = -100
                    elif re[29] == 0:
                        if re[27]-re[7] < radarSpotting:
                            # outgoing fleet is still detected by our radar
                            loosing_time = int(radarSpotting-(re[27]-re[7]))
                            display_to = False
                        else:
                            relation = -100
                    else:
                        remaining_time = re[7]
                if relation > -100:
                    radar = {
                        "id": re[8],
                        "name": re[9],
                        "fleetid": re[0],
                        "fleetname": re[1],
                        "signature": re[5],
                        "relation": relation,
                        "moving": {},
                        "leaving": {},
                        "entering": {},
                        "alliancetag": '',
                    }
                    if re[30]:
                        radar["alliancetag"] = re[30]
                    # determine the type of movement : intrasector, intersector (entering, leaving)
                    # also don't show signature of enemy fleets if we don't know or can't spy on the source AND target coords
                    # re[18]
                    if re[13] == galaxy and re[14] == sector:
                        if re[21] == galaxy and re[22] == sector:
                            movement_type = "moving"
                            movingfleetcount += 1
                            if ((re[31] >= re[28] and re[18] < config.rAlliance) or not display_from) and \
                                ((re[32] >= re[29] and re[26] < config.rAlliance) or not display_to) and re[10] < config.rAlliance:
                                radar["signature"] = 0
                        else:
                            movement_type = "leaving"
                            leavingfleetcount += 1
                            if ((re[31] and re[31] >= re[28] and re[18] < config.rAlliance) or not display_from) and \
                                ((re[32] and re[32] >= re[29] and re[26] < config.rAlliance) or not display_to) and re[10] < config.rAlliance:
                                radar["signature"] = 0
                    else:
                        movement_type = "entering"
                        enteringfleetcount += 1
                        if ((re[31] and re[31] >= re[28] and re[18] < config.rAlliance) or not display_from) and \
                            ((re[32] and re[32] >= re[29] and re[26] < config.rAlliance) or not display_to) and re[10] < config.rAlliance:
                            radar["signature"] = 0
                    # Assign From and To planets info
                    if display_from:
                        # Assign the name of the owner if is not an ally planet
        #               if (re[18] < rAlliance) and not IsNull(re[17]):
        #                   if re[28] > 0 or re[18] = rFriend:
        #                       content.AssignValue "f_planetname", re[17]
        #                   else
        #                       content.AssignValue "f_planetname", ""
        #                   end if
        #               else
        #                   content.AssignValue "f_planetname", re[12]
        #               end if
                        radar["f_planetname"] = getPlanetName(request,re[18], re[28], re[17], re[12])
                        radar["f_planetid"] = re[11]
                        radar["f_g"] = re[13]
                        radar["f_s"] = re[14]
                        radar["f_p"] = re[15]
                        radar["f_relation"] = re[18]
                    else:
                        radar["f_planetname"] = ""
                        radar["f_planetid"] = ""
                        radar["f_g"] = ""
                        radar["f_s"] = ""
                        radar["f_p"] = ""
                        radar["f_relation"] = "0"
                    if display_to:
                        # Assign the planet name if possible otherwise the name of the owner
        #               if (re[26] < rAlliance) and not IsNull(re[25]):
        #                   if re[29] > 0 or re[26] = rFriend:
        #                       content.AssignValue "t_planetname", re[25]
        #                   else
        #                       content.AssignValue "t_planetname", ""
        #                   end if
        #               else
        #                   content.AssignValue "t_planetname", re[20]
        #               end if
                        radar["t_planetname"] = getPlanetName(request,re[26], re[29], re[25], re[20])
                        radar["t_planetid"] = re[19]
                        radar["t_g"] = re[21]
                        radar["t_s"] = re[22]
                        radar["t_p"] = re[23]
                        radar["t_relation"] = re[26]
                    else:
                        radar["t_planetname"] = ""
                        radar["t_planetid"] = ""
                        radar["t_g"] = ""
                        radar["t_s"] = ""
                        radar["t_p"] = ""
                        radar["t_relation"] = "0"
                    # Assign remaining travel time
                    if loosing_time > -1:
                        radar["time"] = loosing_time
                        radar['losing'] = True
                    else:
                        radar["time"] = remaining_time
                        radar['timeleft'] = True
                    gcontext['radar'][movement_type]['fleet'][i] = radar.copy()
                i += 1
            if movingfleetcount == 0:
                gcontext['radar']['moving']['nofleets'] = True
            if enteringfleetcount == 0:
                gcontext['radar']['entering']['nofleets'] = True
            if leavingfleetcount == 0:
                gcontext['radar']['leaving']['nofleets'] = True
    # Display the map : Galaxies, sectors or a sector
    def DisplayMap(galaxy, sector):
        # Assign the displayed galaxy/sector
        gcontext['nav'] = {
            "galaxy": galaxy,
            "sector": sector,
        }
        # Verify which map will be displayed
        if galaxy == "":
            # Display map of galaxies with 8 galaxies per row
            with connection.cursor() as cursor:
                cursor.execute('SELECT n.id,  n.colonies > 0, ' +
                    ' FALSE AND EXISTS(SELECT 1 FROM nav_planet WHERE galaxy=n.id AND ownerid IN (SELECT friend FROM vw_friends WHERE vw_friends.userid=%(UserID)s) LIMIT 1), ' +
                    ' EXISTS(SELECT 1 FROM nav_planet WHERE galaxy=n.id AND ownerid IN (SELECT ally FROM vw_allies WHERE vw_allies.userid=%(UserID)s) LIMIT 1), ' +
                    ' EXISTS(SELECT 1 FROM nav_planet WHERE galaxy=n.id AND ownerid = %(UserID)s LIMIT 1) AS hasplanets, visible ' +
                    ' FROM nav_galaxies AS n ' +
                    ' ORDER BY n.id', {'UserID': gcontext['exile_user'].id})
                res = cursor.fetchall()
                gcontext['universe'] = {
                    'galaxy': {}
                }
                for re in res:
                    galaxy = {
                        "galaxyid": re[0],
                        "visible": re[5],
                    }
                    # check if enemy or friendly planets are in the galaxies
                    if re[4]:
                        galaxy['hasplanet'] = True
                    elif re[3]:
                        galaxy['hasally'] = True
                    elif re[2]:
                        galaxy['hasfriend'] = True
                    elif re[1]:
                        galaxy['hasnothing'] = True
                    gcontext['universe']['galaxy'][re[0]] = galaxy.copy()
            return
        if sector == "":
            # Display map of sectors for the given galaxy
            with connection.cursor() as cursor:
                cursor.execute('SELECT sp_get_galaxy_planets(%s, %s)', [galaxy, gcontext['exile_user'].id])
                re = cursor.fetchone()
                gcontext['galaxy'] = {
                    "id": galaxy,
                    "map": re[0],
                    "mapgalaxy": re[0],
                    "protected_until": 0,
                }
                cursor.execute('SELECT alliances.tag, round(100.0 * sum(n.score) / (SELECT sum(score) FROM nav_planet WHERE galaxy=n.galaxy)) ' +
                        ' FROM nav_planet AS n ' +
                        '   INNER JOIN users ON (users.id = n.ownerid) ' +
                        '   INNER JOIN alliances ON (users.alliance_id = alliances.id) ' +
                        ' WHERE galaxy=%s ' +
                        ' GROUP BY galaxy, alliances.tag ' +
                        ' ORDER BY sum(n.score) DESC', [galaxy])
                res = cursor.fetchall()
                nb = 1
                for re in res:
                    if nb >= 4:
                        break
                    gcontext['galaxy']["sov_tag_" + str(nb)] = re[0]
                    gcontext['galaxy']["sov_perc_" + str(nb)] = re[1]
                    nb += 1
                cursor.execute('SELECT date_part(\'epoch\', protected_until-now()) FROM nav_galaxies WHERE id=%s', [galaxy])
                re = cursor.fetchone()
                if re and re[0]:
                    gcontext['galaxy']["protected_until"] = int(re[0])
                cursor.execute('SELECT sell_ore, sell_hydrocarbon FROM sp_get_resource_price(%s, %s, false)', [gcontext['exile_user'].id, galaxy])
                re = cursor.fetchone()
                if re:
                    gcontext['galaxy']["price_ore"] = int(re[0])
                    gcontext['galaxy']["price_hydrocarbon"] = int(re[1])
                    gcontext["galaxy_link"] = gcontext['galaxy'].copy()
            return
        # Display the planets in the given sector
        # Assign the arrows values
        gcontext['sector'] = {
            'galaxy': galaxy,
            "sector0": GetSector(sector,-1,-1),
            "sector1": GetSector(sector, 0,-1),
            "sector2": GetSector(sector, 1,-1),
            "sector3": GetSector(sector, 1, 0),
            "sector4": GetSector(sector, 1, 1),
            "sector5": GetSector(sector, 0, 1),
            "sector6": GetSector(sector,-1, 1),
            "sector7": GetSector(sector,-1, 0),
            'planet':{},
        }
        # Retrieve/Save fleets in the sector
        with connection.cursor() as cursor:
            cursor.execute('SELECT f.planetid, f.id, f.name, sp_relation(f.ownerid, %(UserID)s), f.signature, ' +
                '   EXISTS(SELECT 1 FROM fleets AS fl WHERE fl.planetid=f.planetid and fl.action != 1 and fl.action != -1 and fl.ownerid IN (SELECT ally FROM vw_allies WHERE userid=%(UserID)s) LIMIT 1), ' +
                ' action=1 OR action=-1, (SELECT tag FROM alliances WHERE id=users.alliance_id), login, shared, ' +
                '   EXISTS(SELECT 1 FROM fleets AS fl WHERE fl.planetid=f.planetid and fl.action != 1 and fl.action != -1 and fl.ownerid =%(UserID)s LIMIT 1) ' +
                ' FROM fleets as f ' +
                '   INNER JOIN users ON (f.ownerid=users.id) ' +
                ' WHERE ((action != 1 AND action != -1) OR engaged) AND ' +
                '   planetid >= sp_first_planet(%(galaxy)s,%(sector)s) AND planetid <= sp_last_planet(%(galaxy)s,%(sector)s) ' +
                ' ORDER BY f.planetid, upper(f.name)', {'UserID': gcontext['exile_user'].id, 'galaxy': galaxy, 'sector': sector})
            res = cursor.fetchall()
            if res:
                fleetsArray = res.copy()
                fleetsCount = len(fleetsArray)
            else:
                fleetsArray = {}
                fleetsCount = 0
            # Retrieve/Save planet elements in the sector
            cursor.execute('SELECT planetid, label, description ' +
                ' FROM planet_buildings ' +
                '   INNER JOIN db_buildings ON db_buildings.id=buildingid ' +
                ' WHERE planetid >= sp_first_planet(%(galaxy)s,%(sector)s) AND planetid <= sp_last_planet(%(galaxy)s,%(sector)s) AND is_planet_element ' +
                ' ORDER BY planetid, upper(label)', {'galaxy': galaxy, 'sector': sector})
            res = cursor.fetchall()
            if res:
                elementsArray = res.copy()
                elementsCount = len(fleetsArray)
            else:
                elementsArray = {}
                elementsCount = 0
            # Retrieve biggest radar strength in the sector that the player has access to
            cursor.execute('SELECT * FROM sp_get_user_rs(%(UserID)s,%(galaxy)s,%(sector)s)', {'UserID': gcontext['exile_user'].id, 'galaxy': galaxy, 'sector': sector})
            re =cursor.fetchone()
            radarstrength = re[0]
            if not gcontext['exile_user'].alliance_id:
                aid = -1
            else:
                aid = gcontext['exile_user'].alliance_id
            # Main query : retrieve planets info in the sector
            cursor.execute('SELECT nav_planet.id, nav_planet.planet, nav_planet.name, nav_planet.ownerid, ' + # 0 1 2 3
                    ' users.login, sp_relation(nav_planet.ownerid,%(UserID)s), floor, space, GREATEST(0, radar_strength), radar_jamming, ' + # 4 5 6 7 8 9
                    ' orbit_ore, orbit_hydrocarbon, alliances.tag, ' + # 10 11 12
                    ' (SELECT SUM(quantity*signature) FROM planet_ships LEFT JOIN db_ships ON (planet_ships.shipid = db_ships.id) WHERE planet_ships.planetid=nav_planet.id), ' + # 13
                    ' floor_occupied, planet_floor, production_frozen, warp_to IS NOT NULL OR vortex_strength > 0, ' + # 14 15 16 17
                    ' planet_pct_ore, planet_pct_hydrocarbon, spawn_ore, spawn_hydrocarbon, vortex_strength, ' + # 18 19 20 21 22
                    ' COALESCE(buy_ore, 0) AS buy_ore, COALESCE(buy_hydrocarbon, 0) as buy_hydrocarbon, ' + # 23 24
                    ' sp_locs_shared(COALESCE(%(aid)s, -1), COALESCE(users.alliance_id, -1)) AS locs_shared ' + # 25 26
                    ' FROM nav_planet ' +
                    '   LEFT JOIN users ON (users.id = ownerid) ' +
                    '   LEFT JOIN alliances ON (users.alliance_id=alliances.id) ' +
                    ' WHERE galaxy=%(galaxy)s AND sector=%(sector)s' +
                    ' ORDER BY planet', {'UserID': gcontext['exile_user'].id, 'aid': aid, 'galaxy': galaxy, 'sector': sector})
            res = cursor.fetchall()
            planets = 1
            # in case there is no planets, redirect player to the map of the galaxies
            if not res:
                return HttpResponseRedirect(reverse('exile:map') + '?')

            for re in res:
                planetid = re[0]
                pla = {
                    "planetid": planetid,
                    "planet": re[1],
                    "relation": re[5],
                    "alliancetag": '',
                    "buy_ore": re[23],
                    "buy_hydrocarbon": re[24],
                    "orbit": {'fleet':{}},
                }
                if re[12]:
                    pla["alliancetag"] = re[12]
                rel = re[5]
                if rel == config.rAlliance and not hasRight(request,"can_use_alliance_radars"):
                    rel = config.rWar
                if rel == config.rFriend and not re[25] and re[3] != 3:
                    rel = config.rWar
                displayElements = False # hasElements is true if the planet has some particularities like magnetic cloud or sun radiation ..
                displayPlanetInfo = False
                displayResources = False # displayResources is true if there is some ore/hydrocarbon on planet orbit
                hasPlanetInfo = True
                # list all the fleets around the current planet
                allyfleetcount = 0
                friendfleetcount = 0
                enemyfleetcount = 0
                fleetcount = 0
                for fleet in fleetsArray:
                    if fleet[0] == planetid:
                        # display fleets on : 
                        #    alliance and own planets 
                        #    planets where we got a fleet or (a fleet of an alliance member and can_use_alliance_radars)
                        #    planets that our radar can detect
                        if (hasRight(request,"can_use_alliance_radars") and ( (rel >= config.rAlliance) or fleet[5] )) or radarstrength > re[9] or fleet[10]:
                            fleetcount += 1
                            fle = {
                                "fleetid": 0,
                                "fleetname": fleet[2],
                                "relation": fleet[3],
                                "fleetowner": fleet[8],
                            }
                            if (re[5] > config.rFriend) or (fleet[3] > config.rFriend) or (radarstrength > re[9]) or (fleet[5] and re[9] == 0):
                                fle["signature"] = fleet[4]
                            else:
                                fle["signature"] = -1
                            if fleet[6]:
                                fle["fleeing"] = True
                            if not fleet[7]:
                                fle["alliancetag"] = ""
                            else:
                                fle["alliancetag"] = fleet[7]
                            if fleet[3] == config.rSelf:
                                fle["fleetid"] = fleet[1]
                                allyfleetcount += 1
                                friendfleetcount += 1
                            elif fleet[3] == config.rAlliance:
                                allyfleetcount += 1
                                friendfleetcount += 1
                                if hasRight(request,"can_order_other_fleets") and fleet[9]:
                                    fle["fleetid"] = fleet[1]
                            elif fleet[3] == config.rFriend:
                                friendfleetcount += 1
                            else:
                                # if planet is owned by the player: increase enemy fleet
                                enemyfleetcount = enemyfleetcount + 1
                            pla['orbit']['fleet'][fleetcount] = fle.copy()
                # assign the planet representation
                if re[6] == 0 and re[7] == 0:
                    # if floor and space are null: it is either an asteroid field, empty square or a vortex
                    pla["planet_img"] = ""
                    if re[17]: #and (radarstrength > 0 or allyfleetcount > 0):
                        pla["vortex"] = True
                    elif re[20] > 0:
                        pla["asteroids"] = True
                    elif re[21] > 0:
                        pla["clouds"] = True
                    else:
                        pla["empty"] = True
                    hasPlanetInfo = False
                else:
                    hasPlanetInfo = True
                    p_img = 1+(re[15] + re[0]) % 21
                    if p_img < 10:
                        p_img = "0" + str(p_img)
                    pla["planet_img"] = p_img
                # retrieve planets non assigned ships and display their signature if we/an ally own the planet or we have a radar,
                # which is more powerfull than jammer, or if we/an ally have a fleet on this planet
                ShowGround = False      
                pla["orbit"]["parked"] = 0
                if re[13] and ( radarstrength > re[9] or rel >= config.rAlliance or allyfleetcount > 0 ):
                    ground = int(re[13])
                    if ground != 0:
                        ShowGround = True
                        pla["orbit"]["parked"] = ground
                #if fleetcount > 0 or ShowGround:
                #    pla["orbit"] = True
                if not re[3]:
                    # if there is no owner
                    displayPlanetInfo = radarstrength > 0 or allyfleetcount > 0
                    displayElements = displayPlanetInfo
                    displayResources = displayPlanetInfo
                    pla["ownerid"] = ""
                    pla["ownername"] = ""
                    pla["planetname"] = ""
                    if hasPlanetInfo:
                        pla["uninhabited"] = True
                    pla["noradar"] = True
                else:
                    pla["ownerid"] = re[3]
                    pla["ownername"] = re[4]
                    # display planet info
                    if rel == config.rSelf:
                        pla["planetname"] = re[2]
                        displayElements = True
                        displayPlanetInfo = True
                        displayResources = True
                    elif rel == config.rAlliance:
                        if gcontext['exile_user'].display_alliance_planet_name:
                            pla["planetname"] = re[2]
                        else:
                            pla["planetname"] = ""
                        displayElements = True
                        displayPlanetInfo = True
                        displayResources = True
                    elif rel == config.rFriend:
                        pla["planetname"] = ""
                        displayElements = radarstrength > re[9] or allyfleetcount > 0
                        displayPlanetInfo = displayElements
                        displayResources = radarstrength > 0 or allyfleetcount > 0
                    else:
                        if radarstrength > 0 or allyfleetcount > 0:
                            pla["planetname"] = re[4]
                            displayElements = radarstrength > re[9] or allyfleetcount > 0
                            displayPlanetInfo = displayElements
                            displayResources = radarstrength > 0 or allyfleetcount > 0
                        else:
                            pla["relation"] = -1
                            pla["alliancetag"] = ""
                            pla["ownerid"] = ""
                            pla["ownername"] = ""
                            pla["planetname"] = ""
                            displayElements = False
                            displayPlanetInfo = False
                            displayResources = False
                if re[3] == 3:
                    pla["planetname"] = "Planète Marchande"
                    pla["planet_img"] = "merchant"
                if rel >= config.rAlliance:
                    pla["radarstrength"] = re[8]
                    pla["radarjamming"] = re[9]
                else:
                    if radarstrength == 0:
                        pla["radarstrength"] = -1
                        pla["radarjamming"] = 0
                    elif re[9] > 0:
                        if re[9] >= radarstrength: # check if radar is jammed
                            pla["radarstrength"] = 1
                            pla["radarjamming"] = -1
                        elif radarstrength > re[9]:
                            pla["radarstrength"] = re[8]
                            pla["radarjamming"] = re[9]
                    elif re[8] == 0:
                        pla["radarstrength"] = 0
                        pla["radarjamming"] = 0
                    else:
                        pla["radarstrength"] = re[8]
                        pla["radarjamming"] = re[9]
                if hasPlanetInfo and displayPlanetInfo:
                    pla["floor"] = re[6]
                    pla["space"] = re[7]
                    pla["a_ore"] = re[18]
                    pla["a_hydrocarbon"] = re[19]
                    pla["vortex_strength"] = re[22]
                    pla["info"] = True
                else:
                    pla["floor"] = ""
                    pla["space"] = ""
                    pla["vortex_strength"] = re[22]
                    pla["noinfo"] = True
                if displayResources and (re[10] > 0 or re[11] > 0):
                    pla["ore"] = re[10]
                    pla["hydrocarbon"] = re[11]
                    pla["resources"] = True
                else:
                    pla["ore"] = 0
                    pla["hydrocarbon"] = 0
                    pla["noresources"] = True
                # list all the planet elements
                if displayElements:
                    pla["elements"] = {}
                    count = 0
                    for elt in elementsArray:
                        if elt[0] == planetid:
                            count += 1
                            pla["elements"][count] = elt[1]
                    displayElements = count > 0
                if not displayElements:
                    pla["noelements"] = True
                if re[16]:
                    pla["frozen"] = True
                else:
                    pla["active"] = True
                # display planet
                gcontext["sector"]["planet"][planetid] = pla.copy()
                planets += 1
            if not IsPlayerAccount(request):
                gcontext["sector"]["dev"] = True
            gcontext["galaxy_link"] = gcontext['sector'].copy()
            # Display fleets movements according to player radar strength
            if radarstrength > 0:
                displayRadar(galaxy, sector, radarstrength)
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'map'
    gcontext['menu'] = menu(request)
    # Retrieve galaxy/sector to display
    galaxy = request.GET.get("g", '')
    sector = request.GET.get("s", '')
    # If the player is on the map and change the current planet, find the galaxy/sector
    planet = request.GET.get("planet", '')
    if planet != "":
        galaxy = gcontext['CurrentGalaxy']
        sector = gcontext['CurrentSector']
    else:
        fleet = request.GET.get("fleet", '')
        if fleet != "":
            fleet = Fleets.objects.get(pk=fleet)
            dest = fleet.dest_planetid
            if dest:
                galaxy = dest.galaxy_id
                sector = dest.sector
            else:
                galaxy = fleet.planetid.galaxy_id
                sector = fleet.planetid.sector
        else:
            if galaxy != "":
                if galaxy.isdigit():
                    galaxy = int(galaxy)
                else:
                    galaxy = gcontext['CurrentGalaxy']
            if sector != "":
                if sector.isdigit():
                    sector = int(sector)
                else:
                    sector = gcontext['CurrentSector']
    redirect = False
    if sector != '' and ( int(sector) < 1 or int(sector) > 99):
        redirect = True
        sector = gcontext['CurrentSector']
    if galaxy != '' and not galaxy in retrieveGalaxyCache().keys():
        redirect = True
        galaxy = gcontext['CurrentGalaxy']
    if redirect:
        return HttpResponseRedirect(reverse('exile:map') + '?g=' + str(galaxy) + '&s=' + str(sector))
    DisplayMap(galaxy, sector)
    context = gcontext
    gcontext['contextinfo'] = header(request)
    fh = fleetheader(request)
    if fh:
        gcontext['contextinfo2'] = fleetheader(request)
    t = loader.get_template('exile/map.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def rankingalliances(request):
    def DisplayRankingAlliances(search_tag, search_name):
        # search by parameter
        searchb = request.GET.get("a", "")
        if searchb != "":
            # if the page is a search result, add the search params to ordering column links
            gcontext["param_a"] = searchb
            gcontext["search_params"] = True
            searchby = " AND alliance_id IN (SELECT id FROM alliances WHERE upper(alliances.name) LIKE upper(%(searchb)s) OR upper(alliances.tag) LIKE upper(%(searchb)s))"
        else:
            searchby = ""
        # ordering column
        reversed = False
        col = int(request.GET.get("col", 1))
        if col < 1 or col > 7:
            col = 1
        # hide scores
        if col == 2 or col == 5:
            col = 1
        if col == 1:
                orderby = "upper(alliances.name)"
        #elif col == 2:
        #   orderby = "score"
        #   reversed = True
        elif col == 3:
                orderby = "members"
                reversed = True
        elif col == 4:
                orderby = "planets"
                reversed = True
        #elif col == 5:
        #   orderby = "score_average"
        #   reversed = True
        elif col ==  6:
                orderby = "created"
        elif col == 7:
                orderby = "upper(alliances.tag)"
        if request.GET.get("r", "") != "":
            reversed = not reversed
        else:
            gcontext["r" + str(col)] = True
        if reversed:
            orderby += " DESC"
        orderby += ", upper(alliances.name)"
        gcontext["sort_column"] = col
        # start offset
        #offset = request.GET.get("start")
        offset = int(request.GET.get("start", -1))
        if offset < 0:
            offset = 0
        displayed = 25 # number of nations on each page
        # retrieve number of alliances
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(DISTINCT alliance_id) FROM users INNER JOIN alliances ON alliances.id=alliance_id WHERE alliances.visible" + searchby, {'searchb': searchb})
            res = cursor.fetchone()
            size = int(res[0])            
            nb_pages = int(size/displayed)
            if nb_pages*displayed < size:
                nb_pages += 1
            if offset >= nb_pages:
                offset = nb_pages - 1
            if offset < 0:
                offset = 0            
            cursor.execute("SELECT alliances.id, alliances.tag, alliances.name, alliances.score, count(*) AS members, sum(planets) AS planets," +
                    " int4(alliances.score / count(*)) AS score_average, alliances.score-alliances.previous_score as score_delta," +
                    " created, EXISTS(SELECT 1 FROM alliances_naps WHERE allianceid1=alliances.id AND allianceid2=%(AllianceId)s)," +
                    " max_members, EXISTS(SELECT 1 FROM alliances_wars WHERE (allianceid1=alliances.id AND allianceid2=%(AllianceId)s) OR (allianceid1=%(AllianceId)s AND allianceid2=alliances.id))" +
                    " FROM users INNER JOIN alliances ON alliances.id=alliance_id" +
                    " WHERE alliances.visible" + searchby +
                    " GROUP BY alliances.id, alliances.name, alliances.tag, alliances.score, alliances.previous_score, alliances.created, alliances.max_members" +
                    " ORDER BY " + orderby +
                    " OFFSET " + str(offset*displayed) + " LIMIT " + str(displayed), {'AllianceId': gcontext['exile_user'].alliance_id})
            res = cursor.fetchall()
            if not res:
                gcontext["noresult"] = True
            gcontext["page_displayed"] = offset+1
            gcontext["page_first"] = offset*displayed+1
            gcontext["page_last"] = min(size, (offset+1)*displayed)
            idx_from = offset+1 - 10
            if idx_from < 1:
                idx_from = 1
            idx_to = offset+1 + 10
            if idx_to > nb_pages:
                idx_to = nb_pages
            gcontext["nav"] = {"p":{}}
            for i in range(1, nb_pages+1):
                page = {}
                if (i==1) or (i >= idx_from and i <= idx_to) or (i % 10 == 0):
                    page["page_id"] = i
                    page["page_link"] = i-1
                    if i-1 != offset:
                            page["link"] = {
                                "search_params": searchb,
                                "link.reversed": request.GET.get("r", ""),
                            }
                    else:
                        page["selected"] = True
                gcontext["nav"]["p"][i] = page.copy()
            # display only if there are more than 1 page
            if not nb_pages > 1:
                gcontext["nav"] = False
            i = 1
            gcontext['alliances'] = {}
            for re in res:
                alli = {
                    "place": offset*displayed+i,
                    "tag": re[1],
                    "name": re[2],
                    "score": re[3],
                    "score_average": re[6],
                    "score_delta": re[7],
                    "members": re[4],
                    "stat_colonies": re[5],
                    "created": re[8],
                    "max_members": re[10],
                }
                if re[6] > 0:
                    alli["plus"] = True
                if re[6] < 0:
                    alli["minus"] = True
                if re[0] == gcontext['exile_user'].alliance_id:
                    alli["playeralliance"] = True
                if re[9]:
                    alli["nap"] = True
                elif re[11]:
                    alli["war"] = True
                gcontext['alliances'][re[0]] = alli.copy()
                i += 1
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'ranking'
    DisplayRankingAlliances(request.GET.get("tag",""), request.GET.get("name", ""))
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/ranking-alliances.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def rankingplayers(request):
    def DisplayRanking():
        # Setup search by Alliance and Nation query string
        searchbyA = searchbyN = ''
        reversed = False
        if False:
            searchbyA = request.GET.get("a", "")
            if searchbyA:
                gcontext["param_a"] = searchbyA
                searchbyA = " AND alliance_id IN (SELECT id FROM alliances WHERE upper(alliances.name) LIKE upper(%(searchbyA)s) OR upper(alliances.tag) LIKE upper(%(searchbyA)s))"
            searchbyN = "" # request.GET.get("n")
            if searchbyN:
                gcontext["param_n"] = searchbyN
                searchbyN = " AND upper(login) LIKE upper(%(searchbyN)s) "
        searchby = searchbyA + searchbyN
        # if the page is a search result, add the search params to column ordering links
        if searchby:
            gcontext["search_params"] = True
        # Setup column ordering
        try:
            col = int(request.GET.get("col", 3))
        except (KeyError, Exception):
            col = 3
        if col < 1 or col > 4:
            col = 3
        if col == 1:
            orderby = "CASE WHEN score_visibility=2 OR v.id=%(user_id)s THEN upper(login) ELSE '' END, upper(login)"
        elif col == 2:
            orderby = "upper(alliances.name)"
        elif col == 3:
            orderby = "v.score"
            reversed = True
        elif col == 4:
            orderby = "v.score_prestige"
            reversed = True
        if request.GET.get("r", ""):
            reversed = not reversed
        else:
           gcontext["r" + str(col)] = True
        if reversed:
            orderby = orderby + " DESC"
        orderby += ", upper(login)"
        gcontext["sort_column"] = col
        # get the score of the tenth user to only show the avatars of the first 10 players
        with connection.cursor() as cursor:
            cursor.execute("SELECT score FROM vw_players WHERE true "+searchby+" ORDER BY score DESC OFFSET 9 LIMIT 1", {'searchbyA':searchbyA, 'searchbyN':searchbyN})
            res = cursor.fetchone()
            if not res:
                TenthUserScore = 0
            else:
                TenthUserScore = res[0]
            displayed = 100 # number of nations displayed per page
            # Retrieve the offset from where to begin the display
            try:
                offset = int(request.GET.get("start", "-1"))
            except (KeyError, Exception):
                offset = -1
            if offset < 0:
                cursor.execute("SELECT v.id FROM vw_players v LEFT JOIN alliances ON alliances.id=v.alliance_id" +
                        " WHERE true "+searchby+" ORDER BY "+orderby, {'searchbyA':searchbyA, 'searchbyN':searchbyN, 'user_id':gcontext['exile_user'].id})
                res = cursor.fetchall()
                index = 0
                found = False
                for re in res:
                    if re[0] == gcontext['exile_user'].id:
                        found = True
                        break
                    index += 1
                if not found:
                    myOffset=0
                else:
                    myOffset = int(index/displayed)
                offset = myOffset
            # get total number of players that could be displayed
            cursor.execute("SELECT count(1) FROM vw_players WHERE true "+searchby, {'searchbyA':searchbyA, 'searchbyN':searchbyN})
            res = cursor.fetchone()
            size = res[0]
            if size > request.session.get('stat_players', 0):
                cursor.execute('SELECT int4(count(1)), (SELECT int4(count(1)) FROM vw_players WHERE score >= %s) FROM vw_players', [gcontext['exile_user'].score])
                res2 = cursor.fetchone()
                if res2:
                    request.session['stat_players'] = res2[0]
                    request.session['stat_rank'] = res2[1]
                    gcontext['stat_rank'] = request.session.get('stat_rank', 0)
                    gcontext['stat_players'] = request.session.get('stat_players', 0)
            nb_pages = int(size/displayed)
            if nb_pages*displayed < size:
                nb_pages += 1
            if offset >= nb_pages:
                offset -= 1
            if offset < 0:
                offset = 0
            gcontext["page_displayed"] = offset+1
            gcontext["page_first"] = offset*displayed+1
            gcontext["page_last"] = min(size, (offset+1)*displayed)
            idx_from = offset+1 - 10
            if idx_from < 1:
                idx_from = 1
            idx_to = offset+1 + 10
            if idx_to > nb_pages:
                idx_to = nb_pages
            gcontext['nav'] = {'p':{}}
            for i in range(1,nb_pages+1):
                if (i==1) or (i >= idx_from and i <= idx_to) or (i % 10 == 0):
                    page = {
                        "page_id": i,
                        "page_link": i-1,
                    }
                    if i-1 != offset:
                        if searchby:
                            page['link'] = {"search_params":True}
                        if request.GET.get("r",""):
                            page['link'] = {"reversed":True}
                    else:
                        page["selected"] = True
                    gcontext['nav']['p'][i] = page.copy()
            # display only if there are more than 1 page
            if nb_pages <= 1:
                gcontext['nav'] = False
            # Retrieve players to display
            cursor.execute("SELECT login, v.score, v.score_prestige," +
                    "COALESCE(date_part('day', now()-lastactivity), 15), alliances.name, alliances.tag, v.id, avatar_url, v.alliance_id, v.score-v.previous_score AS score_delta," +
                    "v.score >= %(TenthUserScore)s OR score_visibility = 2 OR (score_visibility = 1 AND alliance_id IS NOT NULL AND alliance_id=%(AllianceId)s) OR v.id=%(user_id)s" +
                    " FROM vw_players v" +
                    "   LEFT JOIN alliances ON ((v.score >= %(TenthUserScore)s OR score_visibility = 2 OR v.id=%(user_id)s OR (score_visibility = 1 AND alliance_id IS NOT NULL AND alliance_id=%(AllianceId)s)) AND alliances.id=v.alliance_id)" +
                    " WHERE true "+searchby+" ORDER BY "+orderby+" OFFSET "+str(offset*displayed)+" LIMIT "+str(displayed), {'TenthUserScore':TenthUserScore,'AllianceId':gcontext['exile_user'].alliance_id,'searchbyA':searchbyA, 'searchbyN':searchbyN, 'user_id':gcontext['exile_user'].id})
            res = cursor.fetchall()
            if not res:
                gcontext["noresult"] = True
            gcontext["player"] = {}
            i = 1
            for re in res:
                player = {
                    "place": offset*displayed+i,
                    "name": re[0],
                }
                visible = re[10] #or Session(sprivilege) > 100' or TenthUserScore <= re[1]
                if visible and re[4]:
                    player["alliancename"] = re[4]
                    player["alliancetag"] = re[5]
                    player["alliance"] = True
                else:
                    player["noalliance"] = True
                player["score"] = re[1]
                player["score_battle"] = re[2]
                if visible:
                    player["score_delta"] = re[9]
                    if re[9] > 0:
                        player["plus"] = True
                    if re[9] < 0:
                        player["minus"] = True
                else:
                    player["score_delta"] = ""
                player["stat_colonies"] = re[2]
                player["last_login"] = re[3]
                if re[3] <= 7:
                    player["recently"] = True
                elif re[3] <= 14:
                    player["1weekplus"] = True
                elif re[3] > 14:
                    player["2weeksplus"] = True
                if visible:
                    if re[6] == gcontext['exile_user'].id:
                        player["self"] = True
                    elif gcontext['exile_user'].alliance_id and re[8] == gcontext['exile_user'].alliance_id:
                        player["ally"] = True
                    # show avatar only if top 10
                    if re[1] >= TenthUserScore:
                        if not re[7]:
                            player["top10avatar"] = {"noavatar":True}
                        else:
                            player["avatar_url"] = re[7]
                            player["top10avatar"] = {"avatar":True}
                else:
                    player["name_na"] = True
                    player['name'] = ''
                gcontext["player"][i] = player.copy()
                i += 1
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'ranking_players'
    #if gcontext['exile_user'].privilege < 100:
    #   return HttpResponseRedirect(reverse('exile:overview'))
    DisplayRanking()
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/ranking-players.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def rankinggalaxies(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/ranking-galaxies.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def rankingsearch(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/ranking-search.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def production(request):
    # Display bonus given by a commander (typ=0), building (typ=1) or a research (typ=2)
    def DisplayBonus(overview, res, typ):
        for re in res:
            item = {
                "id": re[0],
                "name": re[1],
                "mod_production_ore": round(re[2]*100),
                "mod_production_hydrocarbon": round(re[3]*100),
                "mod_production_energy": round(re[4]*100),
            }
            if re[2] > 0:
                item["mod_production_ore"]= "+" + str(round(re[2]*100))
                item['ore_positive'] = True
            elif re[2] < 0:
                item['ore_negative'] = True
            if re[3] > 0:
                item['mod_production_hydrocarbon'] = "+" + str(round(re[3]*100))
                item['hydrocarbon_positive'] = True
            elif re[3] < 0:
                item['hydrocarbon_negative'] = True
            if re[4] > 0:
                item['mod_production_energy'] = "+" + str(round(re[4]*100))
                item['energy_positive'] = True
            elif re[4] < 0:
                item['energy_negative'] = True
            if typ == 0:
                item['commander'] = True
                overview['bonus']['itemms']['c'+str(re[0])] = item.copy()
            elif typ == 1:
                item['building'] = True
                item["name"] = getBuildingLabel(re[0])
                item["description"] = getBuildingDescription(re[0])
                overview['bonus']['itemms']['b'+str(re[0])] = item.copy()
            else:
                item['research'] = True
                item["name"] = getResearchLabel(re[0])
                item["description"] = getResearchDescription(re[0])
                item["level"] = re[5]
                overview['bonus']['itemms']['r'+str(re[0])] = item.copy()
    def displayOverview(RecomputeIfNeeded):
        # Assign total production variables
        with connection.cursor() as cursor:
            cursor.execute('SELECT workers, workers_for_maintenance, int4(workers/GREATEST(1.0, workers_for_maintenance)*100), int4(previous_buildings_dilapidation / 100.0), ' +
                ' int4(production_percent*100), ' +
                ' pct_ore, pct_hydrocarbon ' +
                ' FROM vw_planets WHERE id=%s', [gcontext['CurrentPlanet']])
            re = cursor.fetchone()
            if not re:
                return
            overview = {
                "bonus": {"itemms":{}},
                "workers": re[0],
                "workers_required": re[1],
                "production": re[2],
                "final_production": re[4],
                "a_ore": re[5],
                "a_hydrocarbon": re[6],
                "buildings": {},
            }
            if re[3] <= 1:
                overview['condition_excellent'] = True
            elif re[3] < 20:
                overview['condition_good'] = True
            elif re[3] < 45:
                overview['condition_fair'] = True
            elif re[3] < 80:
                overview['condition_bad'] = True
            else:
                overview['condition_catastrophic'] = True
            if re[0] >= re[1]:
                overview['repairing'] = True
            else:
                overview['decaying'] = True
            if RecomputeIfNeeded and re[4] > re[2]:
                cursor.execute('SELECT sp_update_planet(%s)', [gcontext['CurrentPlanet']])
                displayPage(False)
                return
            # List buildings that produce a resource : ore, hydrocarbon or energy
            cursor.execute('SELECT id, production_ore*working_quantity, production_hydrocarbon*working_quantity, energy_production*working_quantity, working_quantity ' +
                    ' FROM vw_buildings ' +
                    ' WHERE planetid=%s AND (production_ore > 0 OR production_hydrocarbon > 0 OR energy_production > 0) AND working_quantity > 0', [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            totalOre = 0
            totalHydrocarbon = 0
            totalEnergy = 0
            for re in res:
                building = {
                    "id": re[0],
                    "name": getBuildingLabel(re[0]),
                    "description": getBuildingDescription(re[0]),
                    "production_ore": round(re[1], 2),
                    "production_hydrocarbon": round(re[2], 2),
                    "production_energy": round(re[3], 2),
                    "quantity": re[4],
                }
                totalOre += re[1]
                totalHydrocarbon += re[2]
                totalEnergy += re[3]
                overview['buildings'][re[0]] = building.copy()
            # Retrieve commander assigned to the planet if any
            cursor.execute('SELECT commanders.id, commanders.name, ' +
                    ' commanders.mod_production_ore-1, commanders.mod_production_hydrocarbon-1, commanders.mod_production_energy-1 ' +
                    ' FROM commanders INNER JOIN nav_planet ON (commanders.id = nav_planet.commanderid) ' +
                    ' WHERE nav_planet.id=%s', [gcontext['CurrentPlanet']])
            re = cursor.fetchall()
            if re:
                DisplayBonus(overview,re,0)
            # List production bonus given by buildings
            cursor.execute('SELECT buildingid, \'\', mod_production_ore*quantity, mod_production_hydrocarbon*quantity, mod_production_energy*quantity ' +
                    ' FROM planet_buildings ' +
                    '   INNER JOIN db_buildings ON (db_buildings.id = planet_buildings.buildingid) ' +
                    ' WHERE planetid=%s AND (mod_production_ore != 0 OR mod_production_hydrocarbon != 0 OR mod_production_energy != 0)', [gcontext['CurrentPlanet']])
            re = cursor.fetchall()
            if re:
                DisplayBonus(overview,re,1)
            # List researches that gives production bonus
            cursor.execute('SELECT researchid, \'\', level*mod_production_ore, level*mod_production_hydrocarbon, level*mod_production_energy, level ' +
                    ' FROM researches INNER JOIN db_research ON researches.researchid=db_research.id ' +
                    ' WHERE userid=%s AND ((mod_production_ore > 0) OR (mod_production_hydrocarbon > 0) OR (mod_production_energy > 0)) AND (level > 0)', [gcontext['exile_user'].id])
            re = cursor.fetchall()
            if re:
                DisplayBonus(overview,re,2)
            # Display buildings sub total if there are bonus and more than 1 building that produces resources
            if len(overview['bonus']['itemms']) > 0 and len(overview['buildings']) > 1:
                overview['subtotal'] = {
                    "production_ore": round(totalOre, 2),
                    "production_hydrocarbon": round(totalHydrocarbon, 2),
                    "production_energy": round(totalEnergy, 2),
                }
            cursor.execute('SELECT int4(COALESCE(sum(effective_energy), 0)) FROM planet_energy_transfer WHERE target_planetid=%s', [gcontext['CurrentPlanet']])
            re = cursor.fetchone()
            if re:
                EnergyReceived = re[0]
            else:
                EnergyReceived = 0
            # Assign total production variables
            cursor.execute('SELECT ore_production, hydrocarbon_production, energy_production-%s FROM nav_planet WHERE id=%s', [EnergyReceived, gcontext['CurrentPlanet']])
            re = cursor.fetchone()
            if re:
                # display bonus sub-total
                if len(overview['bonus']['itemms']) > 0:
                    if RecomputeIfNeeded and (re[0]-totalOre < 0 or re[1]-totalHydrocarbon < 0 or re[2]-totalEnergy < 0):
                        cursor.execute('SELECT sp_update_planet(%s)', [gcontext['CurrentPlanet']])
                        displayPage(False)
                        return
                    overview['bonus']["production_ore"] = round(re[0]-totalOre, 2)
                    overview['bonus']["production_hydrocarbon"] = round(re[1]-totalHydrocarbon, 2)
                    overview['bonus']["production_energy"] = round(re[2]-totalEnergy, 2)
                overview["production_ore"] = round(re[0], 2)
                overview["production_hydrocarbon"] = round(re[1], 2)
                overview["production_energy"] = round(re[2], 2)
                if gcontext['tpl_header']["energy_production"] < 0 and gcontext['tpl_header']["energy"] == 0:
                    energy_produced = gcontext['tpl_header']["energy_production"]
                    energy_used = gcontext['tpl_header']["energy_consumption"]
                    mod_energy = round((energy_produced / max(energy_used, 1)) *100);
                    overview['malus'] = {'itemms':{'g0':{
                        'context': True,
                        'typ':'context',
                        'name':'Manque d\'énergie',
                        'description':'Votre planête est à cours d\'énergie. Celà impacte également les travailleurs, la recherche et les vitesses de constructions.',
                        'mod_production_ore':mod_energy,
                        'mod_production_hydrocarbon':mod_energy,
                        'mod_production_energy':0,
                        'ore_negative':True,
                        'hydrocarbon_negative':True,
                    }}}
            gcontext['overview'] = overview
    def displayManage(action):
        if action == "submit":
            with connection.cursor() as cursor:
                cursor.execute('SELECT buildingid, quantity - CASE WHEN destroy_datetime IS NULL THEN 0 ELSE 1 END, disabled ' +
                    ' FROM planet_buildings ' +
                    '   INNER JOIN db_buildings ON (planet_buildings.buildingid=db_buildings.id) ' +
                    ' WHERE can_be_disabled AND planetid=%s', [gcontext['CurrentPlanet']])
                res = cursor.fetchall()
                for re in res:
                    quantity = re[1] - int(request.POST.get('enabled' + str(re[0])), request.GET.get('enabled' + str(re[0]), 0))
                    cursor.execute('UPDATE planet_buildings SET ' +
                        ' disabled=LEAST(quantity - CASE WHEN destroy_datetime IS NULL THEN 0 ELSE 1 END, %s) ' +
                        ' WHERE planetid=%s AND buildingid = %s', [quantity, gcontext['CurrentPlanet'], re[0]])
        with connection.cursor() as cursor:
            cursor.execute('SELECT buildingid, quantity - CASE WHEN destroy_datetime IS NULL THEN 0 ELSE 1 END, disabled, energy_consumption, int4(workers*maintenance_factor/100.0), upkeep ' +
                ' FROM planet_buildings ' +
                '   INNER JOIN db_buildings ON (planet_buildings.buildingid=db_buildings.id) ' +
                ' WHERE can_be_disabled AND planetid=%s ' +
                ' ORDER BY buildingid', [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            manage = {'buildings':{}}
            for re in res:
                if re[1] > 0:
                    enabled = re[1] - re[2]
                    quantity = re[1] - re[2]*0.95
                    building = {
                        "id": re[0],
                        "building": getBuildingLabel(re[0]),
                        "quantity": re[1],
                        "energy": re[3],
                        "maintenance": re[4],
                        "upkeep": re[5],
                        "energy_total": round(quantity * re[3]),
                        "maintenance_total": round(quantity * re[4]),
                        "upkeep_total": round(quantity * re[5]),
                        "enabled": 0,
                        "range": range(re[1]+1),
                    }
                    if re[2] > 0:
                        building['not_all_enabled'] = True
                    for i in range(re[1]+1):
                        if i == enabled:
                            building['enabled'] = i
                            break
                manage['buildings'][re[0]] = building.copy()
            gcontext['manage'] = manage
    def displayReceiveSendEnergy(action):
        with connection.cursor() as cursor:
            cursor.execute('SELECT energy_receive_antennas, energy_send_antennas FROM nav_planet WHERE id=%s', [gcontext['CurrentPlanet']])
            re = cursor.fetchone()
            if not re:
                return
            max_receive = re[0]
            max_send = re[1]
            update_planet = False
            if action == "cancel":
                energy_from = int(request.POST.get("from", request.GET.get('from', 0)))
                energy_to = int(request.POST.get("to", request.GET.get('to', 0)))
                if energy_from != 0:
                    cursor.execute('DELETE FROM planet_energy_transfer WHERE planetid=%s AND target_planetid=%s', [energy_from, gcontext['CurrentPlanet']])
                else:
                    cursor.execute('DELETE FROM planet_energy_transfer WHERE planetid=%s AND target_planetid=%s', [gcontext['CurrentPlanet'], energy_to])
                update_planet = True
            elif action == "submit":
                cursor.execute('SELECT target_planetid, energy, enabled FROM planet_energy_transfer WHERE planetid=%s', [gcontext['CurrentPlanet']])
                res = cursor.fetchall()
                for re in res:
                    query = ""
                    I = int(request.POST.get("energy_" + str(re[0]), request.GET.get("energy_" + str(re[0]), 0)))
                    if I != re[1]:
                        query = "energy=" + str(I)
                    I = int(request.POST.get("enabled_" + str(re[0]), request.GET.get("enabled_" + str(re[0]), 0)))
                    if I == 1:
                        I = 1
                    else:
                        I = 0
                    if I != re[2]:
                        if query != "":
                            query += ", "
                        if I:
                            query += "enabled=true"
                        else:
                            query += "enabled=false"
                    if query != "":
                        cursor.execute('UPDATE planet_energy_transfer SET ' + query + ' WHERE planetid=%s AND target_planetid=%s', [gcontext['CurrentPlanet'], re[0]])
                        update_planet = True
                to_g = request.POST.getlist("to_g")
                to_s = request.POST.getlist("to_s")
                to_p = request.POST.getlist("to_p")
                nrj = request.POST.getlist("energy")
                for I in range(0,len(to_g)):
                    g = int(to_g[I], 0)
                    s = int(to_s[I], 0)
                    p = int(to_p[I], 0)
                    energy = int(nrj[I], 0)
                    if g != 0 and s != 0 and p != 0 and energy > 0:
                        cursor.execute('INSERT INTO planet_energy_transfer(planetid, target_planetid, energy) VALUES(%s, sp_planet(%s, %s, %s), %s)', [gcontext['CurrentPlanet'], g, s, p, energy])
                        update_planet = True
            if update_planet:
                cursor.execute('SELECT sp_update_planet(%s)', [gcontext['CurrentPlanet']])
            cursor.execute('SELECT t.planetid, sp_get_planet_name(%s, n1.id), sp_relation(n1.ownerid, %s), n1.galaxy, n1.sector, n1.planet, ' +
                    '       t.target_planetid, sp_get_planet_name(%s, n2.id), sp_relation(n2.ownerid, %s), n2.galaxy, n2.sector, n2.planet, ' +
                    '       t.energy, t.effective_energy, enabled ' +
                    ' FROM planet_energy_transfer t ' +
                    '   INNER JOIN nav_planet n1 ON (t.planetid=n1.id) ' +
                    '   INNER JOIN nav_planet n2 ON (t.target_planetid=n2.id) ' +
                    ' WHERE planetid=%s OR target_planetid=%s ' +
                    ' ORDER BY not enabled, planetid, target_planetid', [gcontext['exile_user'].id, gcontext['exile_user'].id, gcontext['exile_user'].id, gcontext['exile_user'].id, gcontext['CurrentPlanet'], gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            receiving = 0
            sending = 0
            sending_enabled = 0
            sendreceive = {'sent':{},'received':{}}
            for re in res:
                if re[0] == CurrentPlanet:
                    sending = sending + 1
                    if re[14]:
                        sending_enabled += 1
                    sendreceive['sent'][re[6]] = {
                        "planetid": re[6],
                        "name": re[7],
                        "rel": re[8],
                        "g": re[9],
                        "s": re[10],
                        "p": re[11],
                        "energy": re[12],
                        "effective_energy": re[13],
                        "loss": getpercent(re[12]-re[13], re[12], 1),
                    }
                    if re[14]:
                        sendreceive['sent'][re[6]]['enabled'] = True
                elif re[14]: # if receiving and enabled, display it
                    receiving += 1
                    sendreceive['received'][re[0]] = {
                        "planetid": re[0],
                        "name": re[1],
                        "rel": re[2],
                        "g": re[3],
                        "s": re[4],
                        "p": re[5],
                        "energy": re[12],
                        "effective_energy": re[13],
                        "loss": getpercent(re[12]-re[13], re[12], 1),
                    }
            sendreceive["planetid"] = ""
            sendreceive["name"] = ""
            sendreceive["rel"] = ""
            sendreceive["g"] = ""
            sendreceive["s"] = ""
            sendreceive["p"] = ""
            sendreceive["energy"] = 0
            sendreceive["effective_energy"] = 0
            sendreceive["loss"] = 0
            sendreceive["antennas_receive_used"] = receiving
            sendreceive["antennas_receive_total"] = max_receive
            sendreceive["antennas_send_used"] = sending_enabled
            sendreceive["antennas_send_total"] = max_send
            if max_send == 0:
                sendreceive['send_no_antenna'] = True
            if max_receive == 0:
                sendreceive['receive_no_antenna'] = True
            if receiving > 0:
                sendreceive['cant_send_when_receiving'] = True
                max_send = 0
            if sending_enabled > 0:
                sendreceive['cant_receive_when_sending'] = True
                max_receive = 0
            elif receiving == 0 and max_receive > 0:
                sendreceive['receiving_none'] = True
            sendreceive['receive'] = range(max_receive - receiving)
            sendreceive['send'] = range(max_send - sending)
            if max_send > 0:
                sendreceive['submit'] = True
            gcontext['sendreceive'] = sendreceive
    def displayPage(RecomputeIfNeeded):
        action = request.POST.get('a', request.GET.get('a', ''))
        cat = int(request.POST.get('cat', request.GET.get('cat', 1)))
        if cat < 1 or cat > 3:
            cat = 1
        gcontext['cat'] = cat
        if cat == 1:
                displayOverview(RecomputeIfNeeded)
                gcontext['nav'] = {'cat1': True}
        elif cat == 2:
                displayManage(action)
                gcontext['nav'] = {'cat2': True}
        elif cat == 3:
                displayReceiveSendEnergy(action)
                gcontext['nav'] = {'cat3': True}
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'production'
    gcontext['menu'] = menu(request)
    context = gcontext
    gcontext['contextinfo'] = header(request)
    displayPage(True)
    t = loader.get_template('exile/production.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def buildings(request):
    def RetrievePlanetInfo():
        # Retrieve recordset of current planet
        with connection.cursor() as cursor:
            cursor.execute('SELECT ore, hydrocarbon, workers-workers_busy, workers_capacity - workers, energy, ' +
                ' floor - floor_occupied, space - space_occupied, ' +
                ' mod_production_ore, mod_production_hydrocarbon, mod_production_energy, ' +
                ' ore_capacity, hydrocarbon_capacity, ' +
                ' scientists, scientists_capacity, soldiers, soldiers_capacity, energy_production-energy_consumption ' +
                ' FROM vw_planets ' +
                ' WHERE id=%s', [gcontext['CurrentPlanet']])
            re = cursor.fetchone()
            if not re:
                return
            gcontext['planetinfo'] = {
                'OreBonus': re[7],
                'HydroBonus': re[8],
                'EnergyBonus': re[9],
                'pOre': re[0],
                'pHydrocarbon': re[1],
                'pWorkers': re[2],
                'pVacantWorkers': re[3],
                'pEnergy': re[4],
                'pFloor': re[5],
                'pSpace': re[6],
                'pBonusEnergy': re[9],
                'pOreCapacity': re[10],
                'pHydrocarbonCapacity': re[11],
                'pScientists': re[12],
                'pScientistsCapacity': re[13],
                'pSoldiers': re[14],
                'pSoldiersCapacity': re[15],
            }
            # Retrieve buildings of current planet
            cursor.execute('SELECT planetid, buildingid, quantity FROM planet_buildings WHERE quantity > 0 AND planetid=%s', [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            if not res:
                gcontext['planetinfo']['buildings'] = {}
            else:
                gcontext['planetinfo']['buildings'] = res.copy()
    # check if we already have this building on the planet and return the number of this building on this planet
    def BuildingQuantity(BuildingId):
        for b in gcontext['planetinfo']['buildings']:
            if BuildingId == b[1]:
                return b[2]
        return 0
    # check if some buildings on the planet requires the presence of the given building
    def HasBuildingThatDependsOn(BuildingId):
        for b in retrieveBuildingsReqCache():
            if BuildingId == b[1]:
                requiredBuildId = b[0]
                if BuildingQuantity(requiredBuildId) > 0:
                    return True
        return False
    # if the building produces energy, check that there will be enough energy after
    # the building destruction
    #   for i = 0 to retrieveBuildingsCache()
    #       if BuildingId = dbbuildingsArray(0, i):
    #           if (dbbuildingsArray(2, i) > 0) and (pEnergy < dbbuildingsArray(2, i)*pBonusEnergy/100-dbbuildingsArray(10, i)):
    #               HasBuildingThatDependsOn = True
    #               exit function
    #           end if
    #       end if
    #   next
    def HasEnoughWorkersToDestroy(BuildingId):
        for b in retrieveBuildingsCache():
            if BuildingId == b[0]:
                if b[5]/2 > gcontext['planetinfo']['pWorkers']:
                    return False
        return True
    def HasEnoughStorageAfterDestruction(BuildingId):
        # 1/ if we want to destroy a building that increase max population: check that 
        # the population is less than the limit after the building destruction
        # 2/ if the building produces energy, check that there will be enough energy after
        # the building destruction
        # 3/ if the building increases the capacity of ore or hydrocarbon, check that there is not
        # too much ore/hydrocarbon
        for b in retrieveBuildingsCache():
            if BuildingId == b[0]:
                if b[1] > 0 and gcontext['planetinfo']['pVacantWorkers'] < b[1]:
                    return True
                # check if scientists/soldiers are lost
                if gcontext['planetinfo']['pScientists'] > gcontext['planetinfo']['pScientistsCapacity']-b[6]:
                    return True
                if gcontext['planetinfo']['pSoldiers'] > gcontext['planetinfo']['pSoldiersCapacity']-b[7]:
                    return True
                # check if a storage building is destroyed
                if gcontext['planetinfo']['pOre'] > gcontext['planetinfo']['pOreCapacity']-b[3]:
                    return True
                if gcontext['planetinfo']['pHydrocarbon'] > gcontext['planetinfo']['pHydrocarbonCapacity']-b[4]:
                    return True
        return False
    def getBuildingMaintenanceWorkers(buildingid):
        getBuildingMaintenanceWorkers = 0
        for b in retrieveBuildingsCache():
            if buildingid == b[0]:
                return b[11]
        return 0
    # List all the available buildings
    def ListBuildings():
        # count number of buildings under construction
        with connection.cursor() as cursor:
            cursor.execute('SELECT int4(count(*)) FROM planet_buildings_pending WHERE planetid=%s LIMIT 1', [gcontext['CurrentPlanet']])
            res = cursor.fetchone()
            if res:
                underConstructionCount = res[0]
            else:
                underConstructionCount = 0
            # list buildings that can be built on the planet
            cursor.execute('SELECT id, category, cost_prestige, cost_ore, cost_hydrocarbon, cost_energy, cost_credits, workers, floor, space, ' +
                    ' construction_maximum, quantity, build_status, construction_time, destroyable, \'\', production_ore, production_hydrocarbon, ' +
                    ' energy_production, buildings_requirements_met, destruction_time, upkeep, energy_consumption, buildable, research_requirements_met ' +
                    ' FROM vw_buildings ' +
                    ' WHERE planetid=%s AND ((buildable AND research_requirements_met) or quantity > 0)', [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            index = 1
            gcontext['category'] = {}
            for re in res:
                # if can be built or has some already built, display it
                if re[19] or re[11] > 0:
                    BuildingId = re[0]
                    category = re[1]
                    building = {
                        "id": BuildingId,
                        "name": getBuildingLabel(BuildingId),
                        "ore": re[3],
                        "hydrocarbon": re[4],
                        "energy": re[5],
                        "credits": re[6],
                        "workers": re[7],
                        "prestige": re[2],
                        "floor": re[8],
                        "space": re[9],
                        "time": re[13],
                        "description": getBuildingDescription(BuildingId),
                        "quantity": re[11],
                        "remainingtime": "",
                        "nextdestroytime": "",
                        "ore_prod": int(re[16]),
                        "hydro_prod": int(re[17]),
                        "energy_prod": int(re[18]),
                        "ore_modifier": int(re[16]*(gcontext['planetinfo']['OreBonus']-100)/100),
                        "hydro_modifier": int(re[17]*(gcontext['planetinfo']['HydroBonus']-100)/100),
                        "energy_modifier": int(re[18]*(gcontext['planetinfo']['EnergyBonus']-100)/100),
                        "workers_for_maintenance": getBuildingMaintenanceWorkers(BuildingId),
                        "upkeep": re[21],
                        "upkeep_energy": re[22],
                    }
                    OreProd = re[16]
                    HydroProd = re[17]
                    EnergyProd = re[18]
                    if OreProd != 0 or HydroProd != 0 or EnergyProd != 0:
                            building['tipprod'] = {
                                "ore": {},
                                "hydro": {},
                                "energy": {},
                            }
                            if gcontext['planetinfo']['OreBonus'] < 100 and OreProd != 0:
                                building['tipprod']['ore']['malus'] = True
                            else:
                                building['tipprod']['ore']['bonus'] = True
                            if gcontext['planetinfo']['HydroBonus'] < 100 and HydroProd != 0:
                                building['tipprod']['hydro']['malus'] = True
                            else:
                                building['tipprod']['hydro']['bonus'] = True
                            if gcontext['planetinfo']['EnergyBonus'] < 100 and EnergyProd != 0:
                                building['tipprod']['energy']['malus'] = True
                            else:
                                building['tipprod']['energy']['bonus'] = True
                    maximum = re[10]
                    quantity = re[11]
                    status = re[12]
                    if status:
                        if status < 0:
                            status = 0
                        building["remainingtime"] = status
                        building['underconstruction'] = True
                        building['isbuilding'] = True
                    elif not re[23]:
                        building['limitreached'] = True
                    elif quantity > 0 and quantity >= maximum:
                        if quantity == 1:
                            building['built'] = True
                        else:
                            building['limitreached'] = True
                    elif not re[19]:
                        building['buildings_required'] = True
                    elif not re[24]:
                        building['researches_required'] = True
                    else:
                        notenoughspace = False
                        notenoughresources = False
                        if re[8] > gcontext['planetinfo']['pFloor']:
                            building['not_enough_floor'] = True
                            notenoughspace = True
                        if re[9] > gcontext['planetinfo']['pSpace']:
                            building['not_enough_space'] = True
                            notenoughspace = True
                        if re[2] > 0 and re[2] > gcontext['exile_user'].prestige_points:
                            building['not_enough_prestige'] = True
                            notenoughresources = True
                        if re[3] > 0 and re[3] > gcontext['planetinfo']['pOre']:
                            building['not_enough_ore'] = True
                            notenoughresources = True
                        if re[4] > 0 and re[4] > gcontext['planetinfo']['pHydrocarbon']:
                            building['not_enough_hydrocarbon'] = True
                            notenoughresources = True
                        if re[5] > 0 and re[5] > gcontext['planetinfo']['pEnergy']:
                            building['not_enough_energy'] = True
                            notenoughresources = True
            #           if re[6] > oPlayerInfo("credits"):
            #               content.Parse "category.building.not_enough_credits"
            #               notenoughresources = True
                        if re[7] > 0 and re[7] > gcontext['planetinfo']['pWorkers']:
                            building['not_enough_workers'] = True
                            notenoughresources = True
                        if notenoughspace:
                            building['not_enough_space'] = True
                        if notenoughresources:
                            building['not_enough_resources'] = True
                        if notenoughspace or notenoughresources:
                            building['not_enough'] = True
                        else:
                            building['build'] = True
                    if quantity > 0 and re[14]:
                        if re[20] and re[20] > 0:
                            building["nextdestroytime"] = re[20]
                            building['next_destruction_in'] = True
                            building['isdestroying'] = True
                        elif not HasEnoughWorkersToDestroy(BuildingId):
                            building['workers_required'] = True
            #           elif pNextDestroyTime > 0:
            #               content.Parse "category.building.destroying"
            #           elif underConstructionCount > 0:
            #               content.Parse "category.building.alreadybuilding"
                        elif HasBuildingThatDependsOn(BuildingId):
                            building['required'] = True
                        elif HasEnoughStorageAfterDestruction(BuildingId):
                            building['capacity'] = True
                        else:
                            building['destroy'] = True
                    else:
                        building['empty'] = True
                    building["index"] = index
                    index += 1
                    ck = 'category' + str(category)
                    if not ck in gcontext['category']:
                        gcontext['category'][ck] = {}
                    gcontext['category'][ck][BuildingId] = building.copy()
            if gcontext['exile_user'].privilege > 100:
                gcontext["dev"] = True
    def StartBuilding(BuildingId):
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_start_building(%s, %s, %s, false)', [gcontext['exile_user'].id, gcontext['CurrentPlanet'], BuildingId ])
            res = cursor.fetchone()
            if res and res[0] > 0:
                if res[0] == 1:
                    log_notice(request, "buildings", "can't build buildingid " + BuildingId, 1)
                elif res[0] == 2:
                    log_notice(request, "buildings", "not enough energy, resources, money or space/floor", 0)
                elif res[0] == 3:
                    log_notice(request, "buildings", "building or research requirements not met", 1)
                elif res[0] == 4:
                    log_notice(request, "buildings", "already building this type of building", 0)
    def CancelBuilding(BuildingId):
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_cancel_building(%s, %s, %s)', [gcontext['exile_user'].id, gcontext['CurrentPlanet'],BuildingId ])
    def DestroyBuilding(BuildingId):
        with connection.cursor() as cursor:
            cursor.execute('SELECT sp_destroy_building(%s, %s, %s)', [gcontext['exile_user'].id, gcontext['CurrentPlanet'],BuildingId ])
    gcontext = request.session.get('gcontext',{})
    retrieveBuildingsReqCache()
    context = gcontext
    gcontext['selectedmenu'] = 'buildings'
    gcontext['menu'] = menu(request)
    Action = request.GET.get("a",'').lower()
    BuildingId = int(request.GET.get("b", 0))
    if BuildingId != 0:
        if Action == "build":
            StartBuilding(BuildingId)
        elif Action == "cancel":
            CancelBuilding(BuildingId)
        elif Action == "destroy":
            DestroyBuilding(BuildingId)
    try:
        y = int(request.GET.get("y","0"))
    except (KeyError, Exception):
        y = 0
    gcontext['scrolly'] = y
    RetrievePlanetInfo()
    ListBuildings()
    gcontext['contextinfo'] = header(request)
    t = loader.get_template('exile/buildings.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def shipyard(request):
    # tech tree
    #select s.name, r.name, dsrr.required_researchlevel from db_ships_req_research as dsrr join db_ships as s on s.id=dsrr.shipid join db_research as r on r.id=dsrr.required_researchid order by s.name
    #
    # retrieve planet and player information
    def RetrieveData():
        # Retrieve recordset of current planet
        #, GREATEST(workers-GREATEST(workers_busy,500,workers_for_maintenance/2), 0)" +
        with connection.cursor() as cursor:
            cursor.execute("SELECT ore_capacity, hydrocarbon_capacity, energy_capacity, workers_capacity" +
                " FROM vw_planets WHERE id=%s", [gcontext['CurrentPlanet']])
            gcontext['oPlanet'] = cursor.fetchone()
    #   query = "SELECT credits FROM users WHERE id=" & UserId
    #   set oPlayer = oConn.Execute(query)
    def displayQueue(planetid):
        # list queued ships and ships under construction
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, shipid, remaining_time, quantity, end_time, recycle, required_shipid, int4(cost_ore*const_recycle_ore(ownerid)), int4(cost_hydrocarbon*const_recycle_hydrocarbon(ownerid)), cost_ore, cost_hydrocarbon, cost_energy, crew" +
                " FROM vw_ships_under_construction" +
                " WHERE planetid=%s" +
                " ORDER BY start_time, shipid", [planetid])
            res = cursor.fetchall()
            buildingcount = 0
            queuecount = 0
            gcontext['queue'] = {}
            gcontext['underconstruction'] = {}
            for re in res:
                ship = {
                    "queueid": re[0],
                    "id": re[1],
                    "name": getShipLabel(re[1]),
                    "quantity": re[3],
                }
                if re[2] > 0:
                    ship["remainingtime"] = re[2]
                else:
                    ship["remainingtime"] = 0
                if re[5]:
                    ship["ore"] = re[3]*re[7]
                    ship["hydrocarbon"] = re[3]*re[8]
                    ship["energy"] = 0
                    ship["crew"] = 0
                else:
                    ship["ore"] = re[3]*re[9]
                    ship["hydrocarbon"] = re[3]*re[10]
                    ship["energy"] = re[3]*re[11]
                    ship["crew"] = re[3]*re[12]
                if re[6]:
                    ship["required_ship_name"] = getShipLabel(re[6])
                if re[4]:
                    if re[5]:
                        ship["recycle"] = True
                    else:
                        ship["cancel"] = True
                    if re[6]:
                        ship["required_ship"] = True
                    gcontext['underconstruction'][re[0]] = ship.copy()
                else:
                    if re[5]:
                        ship["recycle"] = True
                    if re[6]:
                        ship["required_ship"] = True
                    ship["cancel"] = True
                    gcontext['queue'][re[0]] = ship.copy()
    # List all the available ships for construction
    def ListShips():
        add = ''
        if ShipFilter == 1:
            gcontext['selected_menu'] = "shipyard_military"
            add = " AND weapon_power > 0 AND required_shipid IS NULL" # military ships only
        elif ShipFilter == 2:
            gcontext['selected_menu'] = "shipyard_unarmed"
            add = " AND weapon_power = 0 AND required_shipid IS NULL" # non-military ships
        elif ShipFilter == 3:
            gcontext['selected_menu'] = "shipyard_upgrade"
            add = " AND required_shipid IS NOT NULL" # upgrade ships only
            gcontext['action_button'] = 'Upgrader'
            gcontext['action_column'] = 'Upgrade'
        # list ships that can be built on the planet
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, category, name, cost_ore, cost_hydrocarbon, cost_energy, workers, crew, capacity," +
                " construction_time, hull, shield, weapon_power, weapon_ammo, weapon_tracking_speed, weapon_turrets, signature, speed," +
                " handling, buildingid, recycler_output, droppods, long_distance_capacity, quantity, buildings_requirements_met, research_requirements_met," +
                " required_shipid, required_ship_count, COALESCE(new_shipid, id) AS shipid, cost_prestige, upkeep, required_vortex_strength, mod_leadership" +
                " FROM vw_ships WHERE planetid=%s " + add, [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            gcontext["planetid"] = gcontext['CurrentPlanet']
            gcontext["filter"] = ShipFilter
            # number of ships types that can be built
            buildable = 0
            count = 0
            gcontext['category'] = {}
            for re in res:
                if  re[23] > 0 or re[25]:
                    category = re[1]
                    ShipId = re[28]
                    ship = {
                        "id": re[0],
                        "name": getShipLabel(ShipId),
                        "ore": re[3],
                        "hydrocarbon": re[4],
                        "energy": re[5],
                        "workers": re[6],
                        "crew": re[7],
                        "upkeep": re[30],
                        "quantity": re[23],
                        "time": re[9],
                        # assign ship description
                        "description": getShipDescription(re[28]),
                        "ship_signature": re[16],
                        "ship_cargo": re[8],
                        "ship_handling": re[18],
                        "ship_speed": re[17],
                        "ship_turrets": re[15],
                        "ship_power": re[12],
                        "ship_tracking_speed": re[14],
                        "ship_hull": re[10],
                        "ship_shield": re[11],
                        "ship_recycler_output": re[20],
                        "ship_long_distance_capacity": re[22],
                        "ship_droppods": re[21],
                        "ship_required_vortex_strength": re[31],
                        "ship_leadership": re[32],
                    }
                    if re[26]:
                        ship["required_ship_name"] = getShipLabel(re[26])
                        ship["required_ship_available"] = re[27]
                        if re[27] == 0:
                            ship["required_ship.none_available"] = True
                        ship["required_ship"] = True
                    if re[29] > 0:
                        ship["required_pp"] = re[29]
                        ship["pp"] = gcontext['exile_user'].prestige_points
                        if re[29] > gcontext['exile_user'].prestige_points:
                            ship["required_pp.not_enough"] = True
                    if re[25]:
                        ship["construction_time"] = True
                        notenoughresources = False
                        if re[3] > gcontext['oPlanet'][0]:
                            ship["not_enough_ore"] = True
                            notenoughresources = True
                        if re[4] > gcontext['oPlanet'][1]:
                            ship["not_enough_hydrocarbon"] = True
                            notenoughresources = True
                        if re[5] > gcontext['oPlanet'][2]:
                            ship["not_enough_energy"] = True
                            notenoughresources = True
                        if re[6] > gcontext['oPlanet'][3]:
                            ship["not_enough_crew"] = True
                            notenoughresources = True
                        can_build = True
                        if not re[24]:
                            ship["buildings_required"] = True
                            can_build = False
                        if not re[25]:
                            ship["researches_required"] = True
                            can_build = False
                        if notenoughresources:
                            ship["notenoughresources"] = True
                            can_build = False
                        if can_build:
                            ship["build"] = True
                            buildable = buildable + 1
                    else:
                        ship["no_construction_time"] = True
                        ship["cant_build"] = True
                    if gcontext['exile_user'].privilege >= 100:
                        ship["dev"] = True
                    if not re[24]:
                        ship["buildings_required"] = True
                        can_build = False
                        ship["building"] = {}
                        for i in retrieveShipsReqCache():
                            if i[0] == ShipId:
                                ship["building"][i[1]] = getBuildingLabel(i[1])
                    if not re[25]:
                        ship["researches_required"] = True
                        can_build = False
                        ship["research"] = {}
                        for i in retrieveShipsReqRCache():
                            if i[0] == ShipId:
                                ship["research"][i[1]] = getResearchLabel(i[1]) + ' niveau ' + str(i[2])
                    ck = 'category' + str(category)
                    if not ck in gcontext['category']:
                        gcontext['category'][ck] = {}
                    gcontext['category'][ck][re[0]] = ship.copy()
                    count = count + 1
            if buildable > 0:
                gcontext["shipnumber"] = buildable
                gcontext["build"] = True
            else:
                gcontext["nobuild"] = True
            if count == 0:
                gcontext["no_shipyard"] = True
            displayQueue(gcontext['CurrentPlanet'])
    # List all the available ships for recycling
    def ListRecycleShips():
        gcontext["selected_menu"] = "shipyard_recycle"
        # list ships that are on the planet
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, category, name, int4(cost_ore * const_recycle_ore(planet_ownerid)) AS cost_ore," +
                " int4(cost_hydrocarbon * const_recycle_hydrocarbon(planet_ownerid)) AS cost_hydrocarbon, cost_credits, workers, crew, capacity," +
                " int4(const_ship_recycling_multiplier() * construction_time) as construction_time, hull, shield, weapon_power, weapon_ammo," +
                " weapon_tracking_speed, weapon_turrets, signature, speed," +
                " handling, buildingid, recycler_output, droppods, long_distance_capacity, quantity, true, true," +
                " null, 0, COALESCE(new_shipid, id) AS shipid" +
                " FROM vw_ships" +
                " WHERE quantity > 0 AND planetid=%s", [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            gcontext["planetid"] = gcontext['CurrentPlanet']
            gcontext["filter"] = ShipFilter
            # number of items in category
            itemCount = 0
            # number of ships types that can be built
            buildable = 0
            count = 0
            gcontext['category'] = {}
            for re in res:
                category = re[1]
                itemCount = itemCount + 1
                ship = {
                    "id": re[0],
                    "name": getShipLabel(re[28]),
                    "ore": re[3],
                    "hydrocarbon": re[4],
                    "credits": re[5],
                    "workers": re[6],
                    "crew": re[7],
                    "quantity": re[23],
                    "time": re[9],
                # assign ship description
                    "description": getShipDescription(re[28]),
                    "ship_signature": re[16],
                    "ship_cargo": re[8],
                    "ship_handling": re[18],
                    "ship_speed": re[17],
                    "ship_turrets": re[15],
                    "ship_power": re[12],
                    "ship_tracking_speed": re[14],
                    "ship_hull": re[10],
                    "ship_shield": re[11],
                    "ship_recycler_output": re[20],
                    "ship_long_distance_capacity": re[22],
                    "ship_droppods": re[21],
                }
                ship["construction_time"] = True
                ship["build"] = True
                buildable = buildable + 1
                if gcontext['exile_user'].privilege >= 100:
                    ship["dev"] = True
                count = count + 1
                ck = 'category' + str(category)
                if not ck in gcontext['category']:
                    gcontext['category'][ck] = {}
                gcontext['category'][ck][re[0]] = ship.copy()
            if buildable > 0:
                gcontext["shipnumber"] = buildable
                gcontext["build"] = True
            else:
                gcontext["nobuild"] = True
            if count == 0:
                gcontext["no_shipyard"] = True
            displayQueue(gcontext['CurrentPlanet'])
    # build ships
    def StartShip(ShipId, quantity):
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_start_ship(%s, %s, %s, false)", [gcontext['CurrentPlanet'], ShipId, quantity])
    def BuildShips():
        for i in retrieveShipsCache():
            shipid = i[0]
            quantity = request.POST.get("s" + str(shipid), '')
            if quantity == '' or not quantity.isdigit():
                quantity =0
            else:
                quantity = int(quantity)
            if quantity > 0:
                StartShip(shipid, quantity)
        return HttpResponseRedirect(reverse('exile:shipyard') + "?f=" + str(ShipFilter))
    # recycle ships
    def RecycleShip(ShipId, quantity):
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_start_ship_recycling(%s, %s, %s)", [gcontext['CurrentPlanet'], ShipId, quantity])
    def RecycleShips():
        for i in retrieveShipsCache():
            shipid = i[0]
            quantity = int(request.POST.get("s" + shipid, 0))
            if quantity > 0:
                RecycleShip(shipid, quantity)
        return HttpResponseRedirect(reverse('exile:shipyard') + "?recycle=1")
    def CancelQueue(QueueId):
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_cancel_ship(%s, %s)", [gcontext['CurrentPlanet'], QueueId])
        if request.GET.get("recycle", "") != "":
            return HttpResponseRedirect(reverse('exile:shipyard') + "?recycle=1")
        else:
            return HttpResponseRedirect(reverse('exile:shipyard') + "?f=" + str(ShipFilter))
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = "shipyard_all"
    Action = request.GET.get("a", "").lower()
    gcontext['action_button'] = 'Construire'
    gcontext['action_column'] = 'Construction'
    # retrieve which page to display
    ShipFilter = request.GET.get("f", "")
    if ShipFilter == "" or not ShipFilter.isdigit():
        ShipFilter = 0
    else:
        ShipFilter = int(ShipFilter)
    if ShipFilter < 0 or ShipFilter > 3:
        ShipFiler = 0
    if Action == "build" or Action == "bui1d":
        if Action != "bui1d":
            log_notice(request, "shipyard", "used BAD 'build' action", 2)
        return BuildShips()
    if Action == "recycle":
        return RecycleShips()
    if Action == "cancel":
        QueueId = int(request.GET.get("q", 0))
        if QueueId != 0:
            return CancelQueue(QueueId)
    RetrieveData()
    if request.GET.get("recycle", "") != "":
        gcontext['action_button'] = 'Recycler'
        gcontext['action_column'] = 'Recyclage'
        ListRecycleShips()
    else:
        ListShips()
    context = gcontext
    gcontext['menu'] = menu(request)
    gcontext['contextinfo'] = header(request)
    t = loader.get_template('exile/shipyard.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def training(request):
    def DisplayTraining():
        gcontext["planetid"] = gcontext['CurrentPlanet']
        with connection.cursor() as cursor:
            cursor.execute("SELECT scientist_ore, scientist_hydrocarbon, scientist_credits," +
                " soldier_ore, soldier_hydrocarbon, soldier_credits" +
                " FROM sp_get_training_price(%s)", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            if re:
                gcontext["scientist_ore"] = re[0]
                gcontext["scientist_hydrocarbon"] = re[1]
                gcontext["scientist_credits"] = re[2]
                gcontext["soldier_ore"] = re[3]
                gcontext["soldier_hydrocarbon"] = re[4]
                gcontext["soldier_credits"] = re[5]
            cursor.execute("SELECT scientists, scientists_capacity, soldiers, soldiers_capacity, workers FROM vw_planets WHERE id=%s", [gcontext['CurrentPlanet']])
            re = cursor.fetchone()
            if re:
                gcontext["scientists"] = re[0]
                gcontext["scientists_capacity"] = re[1]
                gcontext["soldiers"] = re[2]
                gcontext["soldiers_capacity"] = re[3]
                if re[2]*250 < re[0]+re[4]:
                    gcontext["not_enough_soldiers"] = True
                if re[0] < re[1]:
                    gcontext["input_scientists"] = True
                else:
                    gcontext["max_scientists"] = True
                if re[2] < re[3]:
                    gcontext["input_soldiers"] = True
                else:
                    gcontext["max_soldiers"] = True
            if gcontext["train_error"]:
                if gcontext["train_error"] == 5:
                    gcontext["error"] = {"cant_train_now":True}
                else:
                    gcontext["error"] = {"not_enough_workers":True}
            # training in process
            cursor.execute("SELECT id, scientists, soldiers, int4(date_part('epoch', end_time-now()))" +
                    " FROM planet_training_pending WHERE planetid=%s AND end_time IS NOT NULL" +
                    " ORDER BY start_time", [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            i = 0
            gcontext['training'] = {'item':{}}
            for re in res:
                item = {
                    "queueid": re[0],
                    "remainingtime": re[3],
                }
                if re[1] > 0:
                    item["scientists"] = {"quantity": re[1]}
                if re[2] > 0:
                    item["soldiers"] = {"quantity": re[2]}
                gcontext['training']['item'][i] = item.copy()
                i += 1
            # queue
            cursor.execute("SELECT planet_training_pending.id, planet_training_pending.scientists, planet_training_pending.soldiers," +
                    "   int4(ceiling(1.0*planet_training_pending.scientists/GREATEST(1, training_scientists)) * date_part('epoch', INTERVAL '1 hour'))," +
                    "   int4(ceiling(1.0*planet_training_pending.soldiers/GREATEST(1, training_soldiers)) * date_part('epoch', INTERVAL '1 hour'))" +
                    " FROM planet_training_pending" +
                    "   JOIN nav_planet ON (nav_planet.id=planet_training_pending.planetid)" +
                    " WHERE planetid=%s AND end_time IS NULL" +
                    " ORDER BY start_time", [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            i = 0
            gcontext['queue'] = {'item':{}}
            for re in res:
                item = {
                    "queueid": re[0],
                }
                if re[1] > 0:
                    item["scientists"] = {"quantity": re[1], "remainingtime": re[3]}
                if re[2] > 0:
                    item["soldiers"] = {"quantity": re[2], "remainingtime": re[4]}
                gcontext['queue']['item'][i] = item.copy()
                i += 1
    def Train(Scientists, Soldiers):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sp_start_training(%s, %s, %s, %s)", [gcontext['exile_user'].id, gcontext['CurrentPlanet'], Scientists, Soldiers])
            res = cursor.fetchone()
            if res:
                gcontext['train_error'] = res[0]
            else:
                gcontext['train_error'] = 1
    def CancelTraining(queueId):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sp_cancel_training(%s, %s)", [gcontext['CurrentPlanet'], queueId])
    gcontext = request.session.get('gcontext',{})
    gcontext['train_error'] = ''
    gcontext['showHeader'] = True
    train_error = 0
    Action = request.GET.get("a","").lower()
    try:
        trainScientists = int(request.POST.get("scientists","0"))
    except (KeyError, Exception):
        trainScientists = 0
    try:
        trainSoldiers = int(request.POST.get("soldiers","0"))
    except (KeyError, Exception):
        trainSoldiers = 0
    try:
        queueId = int(request.GET.get("q","0"))
    except (KeyError, Exception):
        queueId = 0
    if Action == "train":
        Train(trainScientists, trainSoldiers)
    elif Action ==  "cancel":
        CancelTraining(queueId)
        return HttpResponseRedirect(reverse('exile:training'))
    gcontext['selectedmenu'] = 'training'
    gcontext['menu'] = menu(request)
    gcontext['contextinfo'] = header(request)
    DisplayTraining()
    context = gcontext
    t = loader.get_template('exile/training.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def orbit(request):
    e_no_error = 0
    e_bad_name = 1
    e_already_exists = 2
    def DisplayFleets():
        # list the fleets near the planet
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name, attackonsight, engaged, size, signature, speed, remaining_time, commanderid, commandername," +
                " planetid, planet_name, planet_galaxy, planet_sector, planet_planet, planet_ownerid, planet_owner_name, planet_owner_relation," +
                " destplanetid, destplanet_name, destplanet_galaxy, destplanet_sector, destplanet_planet, destplanet_ownerid, destplanet_owner_name, destplanet_owner_relation," +
                " action, cargo_ore, cargo_hydrocarbon, cargo_scientists, cargo_soldiers, cargo_workers" +
                " FROM vw_fleets " +
                " WHERE planetid=%s AND action != 1 AND action != -1" +
                " ORDER BY upper(name)", [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            if not res:
                gcontext["nofleets"] = True
            gcontext['fleets'] = {}
            for re in res:
                manage = False
                trade = False
                fleet = {
                    "id": re[0],
                    "name": re[1],
                    "size": re[4],
                    "signature": re[5],
                    "ownerid": re[20],
                    "ownername": re[21],
                    "cargo": re[27]+re[28]+re[29]+re[30]+re[31],
                    "cargo_ore": re[27],
                    "cargo_hydrocarbon": re[28],
                    "cargo_scientists": re[29],
                    "cargo_soldiers": re[30],
                    "cargo_workers": re[31],
                }
                if re[8]:
                    fleet["commanderid"] = re[8]
                    fleet["commandername"] = re[9]
                    fleet["commander"] = True
                else:
                    fleet["nocommander"] = True
                if re[26] == 2:
                    fleet["recycling"] = True
                elif re[3]:
                    fleet["fighting"] = True
                else:
                    fleet["patrolling"] = True
                if re[17] == config.rHostile or re[17] == config.rWar:
                        fleet["enemy"] = True
                elif re[17] == config.rAlliance:
                        fleet["ally"] = True
                elif re[17] == config.rFriend:
                        fleet["friend"] = True
                elif re[17] == config.rSelf:
                        if re[26] == 0:
                            fake = True
                            #   manage = True
                            #   trade = True
                        fleet["owner"] = True
                if manage:
                    fleet["manage"] = True
                else:
                    fleet["cant_manage"] = True
                if trade:
                    fleet["trade"] = True
                else:
                    fleet["cant_trade"] = True
                gcontext['fleets'][re[0]] = fleet.copy()
            # list the ships on the planet to create a new fleet
            cursor.execute("SELECT shipid, quantity," +
                    " signature, capacity, handling, speed, (weapon_dmg_em + weapon_dmg_explosive + weapon_dmg_kinetic + weapon_dmg_thermal) AS weapon_power," +
                    " weapon_turrets, weapon_tracking_speed, hull, shield, recycler_output, long_distance_capacity, droppods" +
                    " FROM planet_ships LEFT JOIN db_ships ON (planet_ships.shipid = db_ships.id)" +
                    " WHERE planetid=%s" +
                    " ORDER BY category, label", [gcontext['CurrentPlanet']])
            res = cursor.fetchall()
            if not res:
                gcontext["noships"] = True
            gcontext['new'] = {}
            for re in res:
                ship = {
                    "id": re[0],
                    "quantity": re[1],
                    "name": getShipLabel(re[0]),
                    "description": getShipDescription(re[0]),
                    "ship_signature": re[2],
                    "ship_cargo": re[3],
                    "ship_handling": re[4],
                    "ship_speed": re[5],
                    "ship_hull": re[9],
                }
                if gcontext['fleet_creation_error'] != "":
                    ship["ship_quantity"] = request.POST.get("s" + str(re[0]), "0")
                    if not ship["ship_quantity"].isdigit():
                        ship["ship_quantity"] = "0"
                if re[6] > 0:
                    ship["ship_turrets"] = re[7]
                    ship["ship_power"] = re[6]
                    ship["ship_tracking_speed"] = re[8]
                    ship["attack"] = True
                if re[10] > 0:
                    ship["ship_shield"] = re[10]
                    ship["shield"] = True
                if re[11] > 0:
                    ship["ship_recycler_output"] = re[11]
                    ship["recycler_output"] = True
                if re[12] > 0:
                    ship["ship_long_distance_capacity"] = re[12]
                    ship["long_distance_capacity"] = True
                if re[13] > 0:
                    ship["ship_droppods"] = re[13]
                    ship["droppods"] = True
                gcontext['new'][re[0]] = ship.copy()
            # Assign the fleet name passed in form body
            if gcontext['fleet_creation_error'] != "":
                gcontext["fleetname"] = request.POST.get("name", "")
                gcontext["error"] = gcontext['fleet_creation_error']
    # Create the new fleet
    def NewFleet():
        fleetname = request.POST.get("name", "").strip()
        if not isValidName(fleetname):
            gcontext['fleet_creation_error'] = "fleet_name_invalid"
            return
        # create a new fleet at the current planet with the given name
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_create_fleet(%s, %s, %s)", [gcontext['exile_user'].id, gcontext['CurrentPlanet'], fleetname])
            res = cursor.fetchone()
            if not res:
                return
            fleetid = res[0]
            if fleetid < 0:
                if fleetid == -3:
                    gcontext['fleet_creation_error'] = "fleet_too_many"
                else:
                    gcontext['fleet_creation_error'] = "fleet_name_already_used"
                return
            cant_use_ship = False
            for i in retrieveShipsCache():
                shipid = i[0]
                try:
                    quantity = int(request.POST.get("s" + str(shipid)), 0)
                except (KeyError, Exception):
                    quantity = 0
                # add the ships type by type
                if quantity > 0:
                    cursor.execute("SELECT * FROM sp_transfer_ships_to_fleet(%s, %s, %s, %s)", [gcontext['exile_user'].id, fleetid, shipid, quantity])
                    cant_use_ship = cant_use_ship or res[0] == 3
            #oConn.Execute "UPDATE fleets SET attackonsight=firepower>0 WHERE id=" & fleetid & " AND ownerid=" & UserID, , adExecuteNoRecords
            # delete the fleet if there is no ships in it
            cursor.execute("DELETE FROM fleets WHERE size=0 AND id=%s AND ownerid=%s", [fleetid, gcontext['exile_user'].id])
            if cant_use_ship and gcontext['fleet_creation_error'] == "":
                gcontext['fleet_creation_error'] = "ship_cant_be_used"
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['fleet_creation_error'] = ""
    gcontext['selectedmenu'] = 'orbit'
    gcontext['menu'] = menu(request)
    if request.GET.get("a", "") == "new":
        NewFleet()
    DisplayFleets()
    gcontext['contextinfo'] = header(request)
    context = gcontext
    t = loader.get_template('exile/orbit.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def mails(request):
    # display mails received by the player
    def display_mails():
    #   if session(sprivilege) < 100 then
    #       response.write "en maintenance"
    #       response.End
    #   end if
        gcontext['selectedmenu'] = 'mails_inbox'
        gcontext['mail_tpl'] = "mail-list"
        #content.addAllowedImageDomain "https://*.zod.fr/*"
        #content.addAllowedImageDomain "https://img.exil.pw/*"
        #content.addAllowedImageDomain "https://forum.exil.pw/img/*"
        displayed = 30 # number of messages displayed per page
        # Retrieve the offset from where to begin the display
        try:
            offset = int(request.GET.get("start", "0"))
        except (KeyError, Exception):
            offset = 0
        if offset > 50:
            offset=50
        search_cond = ""
        if gcontext['exile_user'].privilege < 100:
            search_cond = "not deleted AND "
        # get total number of mails that could be displayed
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(1) FROM messages WHERE " + search_cond + " ownerid = %s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            size = re[0]
            nb_pages = int(size/displayed)
            if nb_pages*displayed < size:
                nb_pages += 1
            if offset >= nb_pages:
                offset = nb_pages - 1
            gcontext["offset"] = offset
            if nb_pages > 50:
                nb_pages = 50
            #if nb_pages <= 10 then display all links only if there are a few pages
            gcontext['nav'] = {'p':{}}
            for i in range(1,nb_pages+1):
                page = {
                    "page_id": i,
                    "page_link": i-1,
                    "offset": offset,
                }
                
                if i != offset+1:
                    page["link"] = True
                else:
                    page["selected"] = True
                gcontext['nav']["p"][i] = page.copy()
            gcontext["min"] = offset*displayed+1
            if offset+1 == nb_pages:
                gcontext["max"] = size
            else :
                gcontext["max"] = (offset+1)*displayed
            gcontext["page_display"] = offset+1
            #end if
            #display only if there are more than 1 page
            cursor.execute("SELECT sender, subject, body, datetime, messages.id, read_date, avatar_url, users.id, messages.credits," +
                    " users.privilege, bbcode, owner, messages_ignore_list.added, alliances.tag" +
                    " FROM messages" +
                    "   LEFT JOIN users ON (upper(users.login) = upper(messages.sender) AND messages.datetime >= users.game_started)" +
                    "   LEFT JOIN alliances ON (users.alliance_id = alliances.id)" +
                    "   LEFT JOIN messages_ignore_list ON (userid=%s AND ignored_userid = users.id)" +
                    " WHERE " + search_cond + " ownerid = %s" +
                    " ORDER BY datetime DESC, messages.id DESC" +
                    " OFFSET " + str(offset*displayed) + " LIMIT " + str(displayed), [gcontext['exile_user'].id, gcontext['exile_user'].id])
            res = cursor.fetchall()
            i = 0
            gcontext["mail"] = {}
            for re in res:
                mail = {
                    "index": i,
                    "from": re[0],
                    "subject": re[1],
                    "date": re[3],
                    "mailid": re[4],
                    "moneyamount": re[8],
                }
                #if re[10]:
                mail["bodybb"] = True
                mail["body"] = re[2]
                #else:
                #    mail["html"] = True
                #    mail["body"] = re[2].replace("\r\n", "<br/>")
                if re[8] > 0:
                    mail["money"] = True # sender has given money
                if re[9] and re[9] >= 500:
                    mail["from_admin"] = True
                if not re[6]:
                    mail["noavatar"] = True
                else:
                    mail["avatar_url"] = re[6]
                    mail["avatar"] = True
                if not re[5]:
                    mail["new_mail"] = True # if there is no value for read_date then it is a new mail
                if re[7]:
                    mail["reply"] = {'fake':True}
                    # allow the player to block/ignore another player
                    if re[12]:
                        mail["reply"]["ignored"] = True
                    else:
                        mail["reply"]["ignore"] = True
                    if re[13]:
                        mail["alliancetag"] = re[13]
                        mail["reply"]["alliance"] = True
                if re[11] == ":admins":
                    mail["to_admins"] = True
                elif re[11] == ":alliance":
                    mail["to_alliance"] = True
                if gcontext['exile_user'].privilege > 100:
                    mail["admin"] = True
                gcontext["mail"][i] = mail.copy()
                i += 1
            if i == 0:
                gcontext["nomails"] = True
            if not gcontext["IsImpersonating"]:
                cursor.execute("UPDATE messages SET read_date = now() WHERE ownerid = %s AND read_date is NULL", [gcontext['exile_user'].id])
    # display mails sent by the player
    def display_mails_sent():
        gcontext['selectedmenu'] = 'mails_sent'
        gcontext['mail_tpl'] = "mail-sent"
        displayed = 30 # number of nations displayed per page
        # Retrieve the offset from where to begin the display
        try:
            offset = int(request.GET.get("start", "0"))
        except (KeyError, Exception):
            offset = 0
        if offset > 50:
            offset=50
        messages_filter = "datetime > now()-INTERVAL '2 weeks' AND "
        # if gcontext['exile_user'].privilege >= 100:
        #     messages_filter = ""
        # get total number of mails that could be displayed
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(1) FROM messages WHERE " + messages_filter + "senderid = %s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            size = re[0]
            nb_pages = int(size/displayed)
            if nb_pages*displayed < size:
                nb_pages += 1
            if nb_pages > 50:
                nb_pages = 50
            # if nb_pages <= 10 then display all links only if there are a few pages
            gcontext['nav'] = {'p':{}}
            for i in range(1,nb_pages+1):
                page = {
                    "page_id": i,
                    "page_link": i-1,
                    "offset": offset,
                }
                
                if i != offset+1:
                    page["link"] = True
                else:
                    page["selected"] = True
                gcontext['nav']["p"][i] = page.copy()
            gcontext["min"] = offset*displayed+1
            if offset+1 == nb_pages:
                gcontext["max"] = size
            else :
                gcontext["max"] = (offset+1)*displayed
            gcontext["page_display"] = offset+1
            # end if
            # display only if there are more than 1 page
            cursor.execute("SELECT messages.id, owner, avatar_url, datetime, subject, body, messages.credits, users.id, bbcode, alliances.tag" +
                    " FROM messages" +
                    "   LEFT JOIN users ON (/*upper(users.login) = upper(messages.owner)*/ users.id = messages.ownerid AND messages.datetime >= users.game_started)" +
                    "   LEFT JOIN alliances ON (users.alliance_id = alliances.id)" +
                    " WHERE " + messages_filter + "senderid = %s" +
                    " ORDER BY datetime DESC OFFSET " + str(offset*displayed) + " LIMIT " + str(displayed), [gcontext['exile_user'].id])
            res = cursor.fetchall()
            i = 0
            gcontext["mail"] = {}
            for re in res:
                mail = {
                    "index": i,
                    "sent_to": re[1],
                    "date": re[3],
                    "subject": re[4],
                    "mailid": re[0],
                    "moneyamount": re[6],
                }
                if re[1] == ":admins":
                    mail["admins"] = True
                elif re[1] == ":alliance":
                    mail["alliance"] = True
                else:
                    mail["nation"] = True
                #if re[8]:
                mail["bodybb"] = re[5]
                #else:
                #    mail["body"] = re[5].replace("\r\n", "<br/>")
                #    mail["html"] = True
                if re[6] > 0: # sender has given money
                    mail["money"] = True
                if not re[2]:
                    mail["noavatar"] = True
                else:
                    mail["avatar_url"] = re[2]
                    mail["avatar"] = True
                if re[7]:
                    mail["reply"] = True
                    if re[9]:
                        mail["alliancetag"] = re[9]
                        mail["reply.alliance"] = True
                gcontext["mail"][i] = mail.copy()
                i += 1
            if i == 0:
                gcontext["nomails"] = True
    def display_ignore_list():
        gcontext['selectedmenu'] = 'mails_ignorelist'
        gcontext['mail_tpl'] = "mail-ignorelist"
        selected_menu = "mails.ignorelist"
        with connection.cursor() as cursor:
            cursor.execute("SELECT ignored_userid, sp_get_user(ignored_userid), added, blocked FROM messages_ignore_list WHERE userid=%s", [gcontext['exile_user'].id])
            res = cursor.fetchall()
            i = 0
            gcontext['ignorednation'] = {}
            for re in res:
                na = {
                    "index": i,
                    "userid": re[0],
                    "name": re[1],
                    "added": re[2],
                    "blocked": re[3],
                }
                gcontext['ignorednation'][i] = na.copy()
                i += 1
            if i == 0:
                gcontext['noignorednations'] = True
            gcontext['menu'] = menu(request)
            t = loader.get_template('exile/'+gcontext['mail_tpl']+'.html')
            return t.render(gcontext, request)
    def return_ignored_users():
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_get_user(ignored_userid) FROM messages_ignore_list WHERE userid=%s", [gcontext['exile_user'].id])
            res = cursor.fetchall()
            i = 0
            gcontext['ignored_user'] = {}
            for re in res:
                gcontext['ignored_user'][i] = {"user": re[0]}
                i += 1
            gcontext['menu'] = menu(request)
            t = loader.get_template('exile/mails.html')
            return t.render(gcontext, request)
    # fill combobox with previously sent to
    def display_compose_form(mailto, subject, body, credits):
        gcontext['selectedmenu'] = 'mails_compose'
        gcontext['mail_tpl'] = "mail-compose"
        # fill the recent addressee list
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM sp_get_addressee_list(%s)", [gcontext['exile_user'].id])
            res = cursor.fetchall()
            gcontext['to'] = {"to_user":{}}
            for re in res:
                gcontext['to']["to_user"][re[0]] = re[0]
            if gcontext['hasRight']:
                if hasRight(request,"can_mail_alliance"):
                    gcontext["sendalliance"] = {'fake':True}
            if config.hasAdmins:
                gcontext["sendadmins"] = {'fake':True}
            if mailto == ":admins" and gcontext["sendadmins"]:
                gcontext["sendadmins"]["selected"] = True
                gcontext["hidenation"] = True
                gcontext["send_credits"] = {"hide":True}
                mailto = ""
            elif mailto == ":alliance" and gcontext["sendalliance"]:
                gcontext["sendalliance"]["selected"] = True
                gcontext["hidenation"] = True
                gcontext["send_credits"] = {"hide":True}
                mailto = ""
            else:
                gcontext["nation_selected"] = True
            # if is a payed account, append the autosignature text to message body
            #if oPlayerInfo("paid"):
            cursor.execute("SELECT autosignature FROM users WHERE id=%s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            if re:
                body += " \r\n \r\n" + re[0]
            # re-assign previous values
            gcontext["mailto"] = mailto
            gcontext["subject"] = subject
            gcontext["message"] = strip_tags(body)
            gcontext["credit"] = credits
            #retrieve player's credits
            cursor.execute("SELECT credits, now()-game_started > INTERVAL '2 weeks' AND security_level >= 3 FROM users WHERE id=%s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            gcontext["player_credits"] = re[0]
            if re[1]:
                gcontext["send_credits"] = True
            if sendmail_status:
                gcontext["error"] = {sendmail_status:True}
            if bbcode:
                gcontext["bbcode"] = True
            FillHeaderCredits(request)
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'mails'
    gcontext['mail_tpl'] = 'mails'
    sendmail_status=""
    selected_menu = "mails"
    compose = False
    mailto = ""
    mailsubject = ""
    mailbody = ""
    moneyamount = 0
    bbcode = False
    # new email
    if request.POST.get("compose",""):
        compose = True
    elif request.GET.get("to",""):
        mailto = request.GET.get("to")
        mailsubject = request.GET.get("subject","")
        compose = True
    elif request.GET.get("a","") == "new":
        mailto = request.GET.get("b","")
        if not mailto:
            mailto = request.GET.get("to","")
        mailsubject = request.GET.get("subject","")
        compose = True
    # reply
    elif request.GET.get("a","") == "reply":
        try:
            Id = int(request.GET.get("mailid", "0"))
        except (KeyError, Exception):
            Id = 0
        with connection.cursor() as cursor:
            cursor.execute("SELECT sender, subject, body FROM messages WHERE ownerid=%s AND id=%s LIMIT 1", [gcontext['exile_user'].id, Id])
            #Session("details") = query
            re = cursor.fetchone()
            if re:
                mailto = re[0]
                # adds 'Re: ' to new reply
                if re[1].find("Re:") == 0: 
                    mailsubject = re[1]
                else:
                    mailsubject = "Re: " + re[1]
                mailbody = re[2]
                mailbody = " \r\n > " + mailbody.replace("\r\n","\r\n > ")
                compose = True
    # send email
    elif request.POST.get("sendmail","") and not gcontext['IsImpersonating']:
        compose = True
        mailto = request.POST.get("to","").strip()
        mailsubject = strip_tags(request.POST.get("subject","").strip())
        mailbody = strip_tags(request.POST.get("message","").strip().replace('<br/>',"\r\n"))
        if request.POST.get("sendcredits",""):
            try:
                moneyamount = int(request.POST.get("amount", "0"))
            except (KeyError, Exception):
                moneyamount = 0
        else:
            moneyamount = 0
        bbcode = bool(request.POST.get("bbcode",""))
        if not mailbody:
            sendmail_status = "mail_empty"
        else:
            if request.POST.get("type","") == "admins":
                mailto = ":admins"
                moneyamount = 0
            if request.POST.get("type","") == "alliance":
                # send the mail to all members of the alliance except 
                mailto = ":alliance"
                moneyamount = 0
            if not mailto:
                sendmail_status = "mail_missing_to"
            else:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT sp_send_message(%s, %s, %s, %s, %s, %s)", [gcontext['exile_user'].id, mailto, mailsubject, mailbody, moneyamount, bbcode])
                    re = cursor.fetchone()
                    if re[0] != 0:
                        if re[0] == 1:
                            sendmail_status = "mail_unknown_from" # from not found
                        elif re[0] == 2:
                            sendmail_status = "mail_unknown_to" # to not found
                        elif re[0] == 3:
                            sendmail_status = "mail_same" # send to same person
                        elif re[0] == 4:
                            sendmail_status = "not_enough_credits" # not enough credits
                        elif re[0] == 9:
                            sendmail_status = "blocked" # messages are blocked
                    else:
                        sendmail_status = "mail_sent"
                        mailsubject = ""
                        mailbody = ""
                        moneyamount = 0
    # delete selected emails
    elif request.POST.get("delete",""):
        # build the query of which mails to delete
        query = "false"
        for mailid in request.POST.getlist("checked_mails"):
            try:
                mailid = int(mailid)
            except (KeyError, Exception):
                mailid = 0
            query += " OR id=" + str(mailid)
        if query != "false":
            with connection.cursor() as cursor:
                cursor.execute("UPDATE messages SET deleted=true WHERE (" + query + ") AND ownerid = %s", [gcontext['exile_user'].id])
    if request.GET.get("a","") == "ignore":
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_ignore_sender(%s, %s)", [gcontext['exile_user'].id, request.GET.get("user")])
        return return_ignored_users()
    if request.GET.get("a","") == "unignore":
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM messages_ignore_list WHERE userid=%s AND ignored_userid=(SELECT id FROM users WHERE lower(login)=lower(%s))", [gcontext['exile_user'].id, request.GET.get("user")])
        return return_ignored_users()
    if compose:
        display_compose_form(mailto, mailsubject, mailbody, moneyamount)
    elif request.GET.get("a","") == "ignorelist":
        display_ignore_list()
    elif request.GET.get("a","") == "unignorelist":
        for mailto in request.POST.getlist("unignore"):
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM messages_ignore_list WHERE userid=%s AND ignored_userid=%s", [gcontext['exile_user'].id, mailto])
        display_ignore_list()
    elif request.GET.get("a","") == "sent":
        display_mails_sent()
    else:
        display_mails()
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/'+gcontext['mail_tpl']+'.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def nation(request):
    def display_nation_search(nation):
        gcontext['addAllowedImageDomain'] = "*"
        with connection.cursor() as cursor:
            cursor.execute("SELECT login FROM users WHERE upper(login) ILIKE upper(%s) ORDER BY upper(login)", ['%'+nation+'%'])
            res = cursor.fetchall()
            gcontext['nation'] = {}
            for re in res:
                gcontext['nation'][re[0]] = {'nation':re[0]}
            t = loader.get_template('exile/nation-search.html')
            gcontext['content'] = t.render(gcontext, request)
            return render(request, 'exile/layout.html', gcontext)
    def display_nation():
        nation = request.GET.get("name", "").strip()
        # if no nation is given then display info on the current player
        if not nation:
            nation = gcontext['exile_user'].login
        gcontext['s_nation'] = nation
        gcontext['addAllowedImageDomain'] = "*"
        with connection.cursor() as cursor:
            cursor.execute("SELECT u.login, u.avatar_url, u.description, sp_relation(u.id, %s), " + # 0 1 2 3
                " u.alliance_id, a.tag, a.name, u.id, GREATEST(u.regdate, u.game_started) AS regdate, r.label," + # 4 5 6 7 8 9
                " COALESCE(u.alliance_joined, u.regdate), u.alliance_taxes_paid, u.alliance_credits_given, u.alliance_credits_taken," + # 10 11 12 13
                " u.id" + # 14
                " FROM users AS u" +
                " LEFT JOIN alliances AS a ON (u.alliance_id = a.id) " +
                " LEFT JOIN alliances_ranks AS r ON (u.alliance_id = r.allianceid AND u.alliance_rank = r.id) " +
                " WHERE upper(u.login) = upper(%s) LIMIT 1", [gcontext['exile_user'].id, nation])
            re = cursor.fetchone()
            if not re:
                if nation:
                    return display_nation_search(nation)
                else:
                    return HttpResponseRedirect(reverse('exile:nation'))
            nationId = re[14]
            gcontext["name"] = re[0]
            gcontext["regdate"] = re[8]
            gcontext["alliance_joined"] = re[10]
            if not re[1]:
                gcontext["noavatar"] = True
            else:
                gcontext["avatar_url"] = re[1]
                gcontext["avatar"] = True
            if re[7] != gcontext['exile_user'].id:
                gcontext["sendmail"] = True
            if re[2]:
                gcontext["description"] = re[2]
            if re[3] < config.rFriend:
                gcontext["enemy"] = True
            elif re[3] == config.rFriend:
                gcontext["friend"] = True
            elif re[3] > config.rFriend: # display planets & fleets of alliance members if has the rights for it
                if re[3] == config.rAlliance:
                    gcontext["ally"] = True
                    show_details = hasRight(request,"leader") or hasRight(request,"can_see_members_info")
                else:
                    gcontext["self"] = True
                    show_details = True
                if show_details:
                    gcontext["allied"] = {'planet':{},'fleet':{}}
                    if re[3] == config.rAlliance:
                        if not hasRight(request,"leader"):
                            show_details = False
                    if show_details: #re[3] = rSelf or hasRight(request,"leader") ) then
                        # view current nation planets
                        cursor.execute("SELECT name, galaxy, sector, planet, id FROM vw_planets WHERE ownerid=%s ORDER BY id", [re[7]])
                        oPlanetsRs = cursor.fetchall()
                        if not oPlanetsRs:
                            gcontext["allied"]["noplanets"] = True
                        for oPlanet in oPlanetsRs:
                            pla = {
                                "planetname": oPlanet[0],
                                "g": oPlanet[1],
                                "s": oPlanet[2],
                                "p": oPlanet[3],
                            }
                            gcontext["allied"]['planet'][oPlanet[4]] = pla.copy()
                    # view current nation fleets
                    query = "SELECT id, name, attackonsight, engaged, remaining_time, " \
                        " planetid, planet_name, planet_galaxy, planet_sector, planet_planet, planet_ownerid, planet_owner_name, sp_relation(planet_ownerid, ownerid)," \
                        " destplanetid, destplanet_name, destplanet_galaxy, destplanet_sector, destplanet_planet, destplanet_ownerid, destplanet_owner_name, sp_relation(destplanet_ownerid, ownerid)," \
                        " action, signature, sp_get_user_rs(ownerid, planet_galaxy, planet_sector), sp_get_user_rs(ownerid, destplanet_galaxy, destplanet_sector), shared" \
                        " FROM vw_fleets WHERE ownerid=" + str(re[7])
                    if re[3] == config.rAlliance:
                        if not hasRight(request,"leader"):
                            query += " AND action <> 0"
                    query += " ORDER BY planetid, upper(name)"
                    cursor.execute(query)
                    oFleetsRs = cursor.fetchall()
                    if not oFleetsRs:
                        gcontext["allied"]["nofleets"] = True
                    for oFleet in oFleetsRs:
                        fleet = {
                            "fleetid": oFleet[0],
                            "fleetname": oFleet[1],
                            "planetid": oFleet[5],
                            "signature": oFleet[22],
                            "g": oFleet[7],
                            "s": oFleet[8],
                            "p": oFleet[9],
                        }
                        if oFleet[25]:
                            fleet['shared'] = True
                        else:
                            fleet['shared'] = False
                        if oFleet[4]:
                            fleet["time"] = oFleet[4]
                        else:
                            fleet["time"] = 0
                        fleet["relation"] = oFleet[12]
                        fleet["planetname"] = getPlanetName(request,oFleet[12], oFleet[23], oFleet[11], oFleet[6])
            #           if oFleetsRs(12) < rAlliance and not IsNull(oFleetsRs(11)) then
            #               if oFleetsRs(23) > 0 or oFleetsRs(12) = rFriend then
            #                   content.AssignValue "planetname", oFleetsRs(11)
            #               else
            #                   content.AssignValue "planetname", ""
            #               end if
            #           else
            #               content.AssignValue "planetname", oFleetsRs(6)
            #           end if
                        if re[3] == config.rAlliance:
                            fleet["ally"] = True
                        else:
                            fleet["owned"] = True
                        if oFleet[3]:
                            fleet["fighting"] = True
                        elif oFleet[21] == 2:
                            fleet["recycling"] = True
                        elif oFleet[13]:
                            # Assign destination planet
                            fleet["t_planetid"] = oFleet[13]
                            fleet["t_g"] = oFleet[15]
                            fleet["t_s"] = oFleet[16]
                            fleet["t_p"] = oFleet[17]
                            fleet["t_relation"] = oFleet[20]
                            fleet["t_planetname"] = getPlanetName(request,oFleet[20], oFleet[24], oFleet[19], oFleet[14])
            #               if oFleetsRs(20) < rAlliance and not IsNull(oFleetsRs(19)) then
            #                   if oFleetsRs(24) > 0 or oFleetsRs(20) = rFriend then
            #                       content.AssignValue "t_planetname", oFleetsRs(19)
            #                   else
            #                       content.AssignValue "t_planetname", ""
            #                   end if
            #               else
            #                   content.AssignValue "t_planetname", oFleetsRs(14)
            #               end if
                            fleet["moving"] = True
                        else:
                            fleet["patrolling"] = True
                        gcontext["allied"]["fleet"][oFleet[0]] = fleet.copy()            
            if re[4]:
                gcontext["alliancename"] = re[6]
                gcontext["alliancetag"] = re[5]
                gcontext["rank_label"] = re[9]
                if re[3] == config.rSelf:
                    gcontext["alliance"] = {"self":True}
                elif re[3] == config.rAlliance:
                    gcontext["alliance"] = {"ally":True}
                elif re[3] == config.rFriend:
                    gcontext["alliance"] = {"friend":True}
                else:
                    gcontext["alliance"] = {"enemy":True}
            else:
                gcontext["noalliance"] = True
            cursor.execute("SELECT alliance_tag, alliance_name, joined, \"left\"" +
                    " FROM users_alliance_history" +
                    " WHERE userid = %s AND joined > (SELECT GREATEST(regdate, game_started) FROM users WHERE privilege < 100 AND id=%s)" +
                    " ORDER BY joined DESC", [nationId, nationId])
            res = cursor.fetchall()
            gcontext['alliances'] = {}
            i = 0
            for re in res:
                ally = {
                    "history_tag": re[0],
                    "history_name": re[1],
                    "joined": re[2],
                    "left": re[3],
                }
                gcontext['alliances'][i] = ally.copy()
                i += 1
        return False
    global config
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'nation'
    gcontext['menu'] = menu(request)
    r = display_nation()
    if r:
        return r
    t = loader.get_template('exile/nation.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def reports(request):
    # display list of messages
    def display_mails(cat):
        with connection.cursor() as cursor:
            # Limit the list to the current category or only display 100 reports if no categories specified
            if cat == 0:
                add = " ORDER BY datetime DESC LIMIT 100"
            else:
                add = " AND type = " + str(cat) + " ORDER BY datetime DESC LIMIT 1000"
            cursor.execute("SELECT type, subtype, datetime, battleid, fleetid, fleet_name," +
                " planetid, planet_name, galaxy, sector, planet," +
                " researchid, 0, read_date," +
                " planet_relation, planet_ownername," +
                " ore, hydrocarbon, credits, scientists, soldiers, workers, username," +
                " alliance_tag, alliance_name," +
                " invasionid, spyid, spy_key, description, buildingid," +
                " upkeep_commanders, upkeep_planets, upkeep_scientists, upkeep_ships, upkeep_ships_in_position, upkeep_ships_parked, upkeep_soldiers," +
                " name" +
                " FROM vw_reports" +
                " WHERE ownerid = %s " + add, [gcontext['exile_user'].id])
            gcontext["ownerid"] = gcontext['exile_user'].id
            res = cursor.fetchall()
            gcontext['tabnav'] = {
                "000": {'new':{}},
                "100": {'new':{}},
                "200": {'new':{}},
                "300": {'new':{}},
                "400": {'new':{}},
                "500": {'new':{}},
                "600": {'new':{}},
                "700": {'new':{}},
                "800": {'new':{}},
            }
            gcontext["tabnav"][str(cat)+"00"]["selected"] = True
            if not res:
                gcontext["noreports"] = True
            # List the reports returned by the query
            gcontext['messages'] = {}
            cpt = 0
            for re in res:
                reportType = re[0]*100+re[1]
                if reportType != 140 and reportType != 141 and reportType != 133:
                    report = {
                        "type": reportType,
                        "date": re[2].astimezone(),
                        "battleid": re[3],
                        "fleetid": re[4],
                        "fleetname": re[5],
                        "planetid": re[6],
                        "ore": re[16],
                        "hydrocarbon": re[17],
                        "credits": re[18],
                        "scientists": re[19],
                        "soldiers": re[20],
                        "workers": re[21],
                        "username": re[22],
                        "alliancetag": re[23],
                        "alliancename": re[24],
                        "invasionid": re[25],
                        "spyid": re[26],
                        "spykey": re[27],
                        "description": re[28],
                        "upkeep_commanders": re[30],
                        "upkeep_planets": re[31],
                        "upkeep_scientists": re[32],
                        "upkeep_ships": re[33],
                        "upkeep_ships_in_position": re[34],
                        "upkeep_ships_parked": re[35],
                        "upkeep_soldiers": re[36],
                        "commandername": re[37],
                    }
                    if re[14] == config.rHostile or re[14] == config.rWar or re[14] == config.rFriend:
                            report["planetname"] = re[15]
                    elif re[14] == config.rAlliance or re[14] == config.rSelf:
                            report["planetname"] = re[7]
                    else:
                            report["planetname"] = ""
                    # assign planet coordinates
                    if re[8]:
                        report["g"] = re[8]
                        report["s"] = re[9]
                        report["p"] = re[10]
                    report["researchid"] = re[11]
                    if re[11]:
                        report["researchname"] = getResearchLabel(re[11])
                    if not re[13]:
                        report["new"] = True
                    if re[29]:
                        report["building"] = getBuildingLabel(re[29])
                    gcontext['messages'][cpt] = report.copy()
                cpt += 1
            # List how many new reports there are for each category
            cursor.execute("SELECT r.type, int4(COUNT(1)) " +
                    " FROM reports AS r" +
                    " WHERE datetime <= now()" +
                    " GROUP BY r.type, r.ownerid, r.read_date" +
                    " HAVING r.ownerid = %s AND read_date is NULL", [gcontext['exile_user'].id])
            res = cursor.fetchall()
            total_newreports = 0
            cpt = 0
            for re in res:
                gcontext["tabnav"][str(re[0])+"00"]['new']["cat_newreports"] = re[1]
                total_newreports += re[1]
            if total_newreports != 0:
                gcontext["tabnav"]["000"]['new']["total_newreports"] = total_newreports
            if not gcontext['IsImpersonating']:
                # flag only the current category of reports as read
                if cat != 0:
                    cursor.execute("UPDATE reports SET read_date = now() WHERE ownerid = %s AND type = %s AND read_date is NULL AND datetime <= now()", [gcontext['exile_user'].id, cat])
                # flag all reports as read
                if cat == 0:
                    cursor.execute("UPDATE reports SET read_date = now() WHERE ownerid = %s AND read_date is NULL AND datetime <= now()", [gcontext['exile_user'].id])
    gcontext = request.session.get('gcontext',{})
    try:
        cat = int(request.GET.get("cat", 0))
    except (KeyError, Exception):
        cat = 0
    display_mails(cat)
    context = gcontext
    gcontext['selectedmenu'] = 'reports'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/reports.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def chat(request):
    def getChatId(id):
        if not id and gcontext['exile_user'].alliance_id:
            allychatid = retrieveAllianceChat(gcontext['exile_user'].alliance_id)
            if allychatid:
                addChat(allychatid)
            return allychatid
        return id
    def addLine(chatid, msg):
        msg = msg.strip()[:260]
        if msg:
    #       set oRs = connExecuteRetry("SELECT sp_chat_append
    #       set oRs = connExecuteRetry("INSERT INTO chat_lines(chatid, allianceid, userid, login, message) VALUES(" & chatid & "," & sqlValue(AllianceId) & "," & dosql(UserId) & "," & dosql(oPlayerInfo("login")) & "," & dosql(msg) & ") RETURNING id")
    #       Application("chat_lastmsg_" & getChatId(chatid)) = re[0]
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO chat_lines(chatid, allianceid, userid, login, message) VALUES(%s, %s, %s, %s, %s)",
                    [chatid,gcontext['exile_user'].alliance_id,gcontext['exile_user'].id,gcontext['exile_user'].login,msg])
    #       chatid = getChatId(chatid)
    #       connExecuteRetryNoRecords "INSERT INTO chat_onlineusers(chatid, userid) VALUES(" & chatid & "," & UserId & ")"
    def refreshContent(chatid):
        if chatid and not request.session.get("chat_joined_" + str(chatid), False):
            return
        chatid = getChatId(chatid)
        if not chatid:
            return
        refresh_userlist = (time.time() - request.session.get("lastchatactivity_" + str(chatid), 0)) > config.onlineusers_refreshtime
    #   if IsEmpty(Application("chat_lastmsg_" & chatid)) then Application("chat_lastmsg_" & chatid) = "0"
    #   if Session("lastchatmsg_" & chatid) <> Application("chat_lastmsg_" & chatid) then
        # retrieve new chat lines
        lastmsgid = request.session.get("lastchatmsg_" + str(chatid), 0)
        with connection.cursor() as cursor:
            cursor.execute("SELECT chat_lines.id, datetime, allianceid, login, message" +
                " FROM chat_lines" +
                " WHERE chatid=%s AND chat_lines.id > GREATEST((SELECT id FROM chat_lines WHERE chatid=%s ORDER BY datetime DESC OFFSET 100 LIMIT 1), %s)" +
                " ORDER BY chat_lines.id", [chatid, chatid, lastmsgid])
            res = cursor.fetchall()
            if not res and not refresh_userlist:
                return
            # load the template
            gcontext["login"] = gcontext['exile_user'].login
            #gcontext["chatid"] = chatid
            gcontext['refresh'] = {'line':{},'online_users':{}}
            if res:
                for re in res:
                    request.session["lastchatmsg_" + str(chatid)] = re[0]
                    line = {
                        "lastmsgid": re[0],
                        "datetime": re[1],
                        "author": re[3],
                        "line": re[4],
                        "alliancetag": getAllianceTag(re[2]),
                    }
                    gcontext['refresh']["line"][re[0]] = line.copy()
            # update user lastactivity in the DB and retrieve users online only every 3 minutes
            if refresh_userlist:
                if gcontext['exile_user'].privilege < 100: # prevent admin from showing their presence in chat
                    cursor.execute("INSERT INTO chat_onlineusers(chatid, userid) VALUES(%s, %s)", [chatid, gcontext['exile_user'].id])
                request.session["lastchatactivity_" + str(chatid)] = time.time()
                # retrieve online users in chat
                cursor.execute("SELECT users.alliance_id, users.login, date_part('epoch', now()-chat_onlineusers.lastactivity)" +
                    " FROM chat_onlineusers" +
                    "   INNER JOIN users ON (users.id=chat_onlineusers.userid)" +
                    " WHERE chat_onlineusers.lastactivity > now()-INTERVAL '10 minutes' AND chatid=%s", [chatid])
                res = cursor.fetchall()
                if not res:
                    return
                for re in res:
                    chater = {
                        "alliancetag": getAllianceTag(re[0]),
                        "user": re[1],
                        "lastactivity": re[2],
                    }
                    gcontext['refresh']['online_users'][re[1]] = chater.copy()
    def refreshChat(chatid):
    #   if session(sprivilege) > 100 then RedirectTo "/"
        refreshContent(chatid)
    def displayChatList():
        gcontext["login"] = gcontext['exile_user'].login
        with connection.cursor() as cursor:
            cursor.execute("SELECT name, topic, count(chat_onlineusers.userid)" +
                " FROM chat" +
                "   LEFT JOIN chat_onlineusers ON (chat_onlineusers.chatid = chat.id AND chat_onlineusers.lastactivity > now()-INTERVAL '10 minutes')" +
                " WHERE name IS NOT NULL AND password = '' AND public" +
                " GROUP BY name, topic" +
                " ORDER BY length(name), name")
            res = cursor.fetchall()
            gcontext['publicchats'] = {'chat':{}}
            cpt = 0
            for re in res:
                chat = {
                    "name": re[0],
                    "topic": re[1],
                    "online": re[2],
                }
                gcontext['publicchats']['chat'][cpt] = chat.copy()
                cpt += 1
    # add a chat to the joined chat list
    def addChat(chatid):
        request.session["lastchatactivity_" + str(chatid)] = time.time()-config.onlineusers_refreshtime
        if not request.session.get("chat_joined_" + str(chatid),False):
            request.session["chat_joined_count"] += 1
            request.session["chat_joined_" + str(chatid)] = True
    # remove a chat from list
    def removeChat(chatid):
        if request.session.get("chat_joined_" + str(chatid),False):
            request.session["chat_joined_" + str(chatid)] = False
            request.session["chat_joined_count"] -= 1
    def displayChat():
        request.session["chatinstance"] += 1
        gcontext["login"] = gcontext['exile_user'].login
        gcontext["chatinstance"] = request.session.get("chatinstance",0)
        if gcontext['exile_user'].alliance_id:
            chatid = getChatId(0)
            request.session["lastchatmsg_" + str(chatid)] = 0
            request.session["lastchatactivity_" + str(chatid)] = time.time()-config.onlineusers_refreshtime
            gcontext["alliance"] = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT chat.id, chat.name, chat.topic" +
                " FROM users_chats" +
                "   INNER JOIN chat ON (chat.id=users_chats.chatid AND ((chat.password = '') OR (chat.password = users_chats.password)))" +
                " WHERE userid = %s" +
                " ORDER BY users_chats.added", [gcontext['exile_user'].id])
            res = cursor.fetchall()
            gcontext['join'] = {}
            for re in res:
                addChat(re[0])
                join = {
                    "id": re[0],
                    "name": re[1],
                    "topic": re[2],
                }
                gcontext['join'][re[0]] = join.copy()
                request.session["lastchatmsg_" + str(re[0])] = 0
    #   if session(sprivilege) > 100 then content.Parse "chat.dev"
        gcontext["now"] = datetime.datetime.now()
        gcontext["chat"] = True
    def joinChat():
        gcontext["login"] = gcontext['exile_user'].login
        passw = request.GET.get("pass","").strip()
        # join chat
        with connection.cursor() as cursor:
            cursor.execute("SELECT sp_chat_join(%s, %s)", [request.GET.get("chat","").strip(), passw])
            re = cursor.fetchone()
            if not re or not re[0]:
                return
            chatid = re[0]
            addChat(re[0])
            if chatid:
                # save the chatid to the user chatlist
                cursor.execute("INSERT INTO users_chats(userid, chatid, password) VALUES(%s, %s, %s)", [gcontext['exile_user'].id, chatid, passw])
                cursor.execute("SELECT name, topic FROM chat WHERE id=%s", [chatid])
                re = cursor.fetchone()
                if re:
                    gcontext["join"] = {}
                    gcontext["join"][chatid] = {
                        "id": chatid,
                        "name": re[0],
                        "topic": re[1],
                        "setactive": True,
                    }
                    request.session["lastchatmsg_" + str(chatid)] = 0
            else:
                gcontext["join_badpassword"] = True
    def leaveChat(chatid):
        request.session["lastchatmsg_" + str(chatid)] = 0
        removeChat(chatid)
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM users_chats WHERE userid=%s AND chatid=%s", [gcontext['exile_user'].id, chatid])
            cursor.execute("DELETE FROM chat WHERE id > 0 AND NOT public AND name IS NOT NULL AND id=%s AND (SELECT count(1) FROM users_chats WHERE chatid=chat.id) = 0", [chatid])
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'chat'
    if request.session.get("chatinstance",-1) == -1:
        request.session["chatinstance"] = 0
    if request.session.get("chat_joined_count", -1) == -1:
        request.session["chat_joined_count"] = 0
    try:
        chatid = int(request.GET.get("id", "0"))
    except (KeyError, Exception):
        chatid = 0
    gcontext["chatid"] = chatid
    #chatid = getChatId(chatid)
    action = request.GET.get("a","")
    if action == "send":
        addLine(chatid, request.GET.get("l",""))
        return render(request, 'exile/chat.html', gcontext)
    elif action == "refresh":
        refreshChat(chatid)
        return render(request, 'exile/chat.html', gcontext)
    elif action == "join":
        joinChat()
        return render(request, 'exile/chat.html', gcontext)
    elif action == "leave":
        leaveChat(chatid)
        return render(request, 'exile/chat.html', gcontext)
    elif action == "chatlist":
        displayChatList()
        return render(request, 'exile/chat.html', gcontext)
    displayChat()
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/chat.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def notes(request):
    def display_notes():
        gcontext["maxlength"] = 5000
        with connection.cursor() as cursor:
            cursor.execute("SELECT notes FROM users WHERE id = %s LIMIT 1", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            if re[0]:
                gcontext["notes"] = re[0]
            else:
                gcontext["notes"] = ""
            if gcontext["notes_status"]:
                gcontext["error"] = True
    gcontext = request.session.get('gcontext',{})
    gcontext['notes_status'] = gcontext["notes"] = ""
    notes = request.POST.get("notes","").strip()
    if request.POST.get("submit",""):
        if len(notes) <= 5000:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE users SET notes=%s WHERE id = %s", [notes, gcontext['exile_user'].id])
                gcontext['notes_status'] = "done"
        else:
            gcontext['notes_status'] = "toolong"
    display_notes()
    context = gcontext
    gcontext['selectedmenu'] = 'notes'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/notes.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def mercenaryintelligence(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'mercenaryintelligence'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/mercenary-intelligence.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def exileversion(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'exileversion'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/exile-version.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def devlogerrors(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'log_errors'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/dev-log-errors.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def devlognotices(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'log_notices'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/dev-log-notices.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def devmulti(request):
    def DisplayForm():
        with connection.cursor() as cursor:
            cursor.execute("SELECT datetime, userid, login, sp__itoa(address), forwarded_address, browser," +
                " datetime2, userid2, login2, sp__itoa(address2), forwarded_address2, browser2," +
                " sent_to, received_from, samepassword," +
                " regdate, email, regdate2, email2, samealliance, a_given1, a_taken1, a_given2, a_taken2," +
                " browserid, disconnected, browserid2, disconnected2, browserid = browserid2," +
                " privilege, privilege2, tag, tag2, fingerprint1, fingerprint2" +
                " FROM admin_view_multi_accounts" +
                " WHERE datetime > now()-INTERVAL '7 days' LIMIT 2000")
            res = cursor.fetchall()
            gcontext['item'] = {}
            i = 0
            for re in res:
                item = {
                    "timestamp": re[0],
                    "userid": re[1],
                    "login": re[2],
                    "address": re[3],
                    "forwarded_address": re[4],
                    "browser": re[5],
                    "timestamp2": re[6],
                    "userid2": re[7],
                    "login2": re[8],
                    "address2": re[9],
                    "forwarded_address2": re[10],
                    "browser2": re[11],
                    "sent_to": re[12],
                    "received_from": re[13],
                    "regdate": re[15],
                    "email": re[16],
                    "regdate2": re[17],
                    "email2": re[18],
                    "browserid": re[24],
                    "browserid2": re[26],
                    "alliance1": re[31],
                    "alliance2": re[32],
                    "fingerprint": re[33],
                    "fingerprint2": re[34],
                }
                if re[14]:
                    item["samepassword"] = True
                if re[19]:
                    item["given1"] = re[20]
                    item["taken1"] = re[21]
                    item["given2"] = re[22]
                    item["taken2"] = re[23]
                    item["samealliance"] = True
                if re[25]:
                    item["disconnected"] = re[25]
                if re[27]:
                    item["disconnected2"] = re[27]
                if re[28] and re[29] == 0 and re[30] == 0:
                    item["samebrowserid"] = True
                if re[33] and re[33] == re[34]:
                    item["samefingerprint"] = True
                if re[29] == 0:
                    item["can_ban_multi"] = True
                if re[30] == 0:
                    item["can_ban_multi2"] = True
                gcontext["item"][i] = item.copy()
                i += 1
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'log_multi'
    gcontext['menu'] = menu(request)
    DisplayForm()
    context = gcontext
    t = loader.get_template('exile/dev-multi.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def devoptions(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'help'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/dev-options.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def devfleets(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'help'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/dev-fleets.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def devconnections(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'help'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/dev-connections.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def devmultiusers(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'help'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/dev-multi-users.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def devexpenses(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'help'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/dev-expenses.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def devplayas(request):
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'help'
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/dev-playas.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
@admin
def devstats(request):
    def display_galaxies():
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, colonies, planets, float4(100.0*colonies / planets)," +
                " visible, allow_new_players, (SELECT count(*) FROM nav_planet WHERE galaxy=nav_galaxies.id AND warp_to IS NOT NULL)" +
                " FROM nav_galaxies ORDER BY id")
            res = cursor.fetchall()
            gcontext['galaxies'] = {}
            for re in res:
                galaxy = {
                    "galaxy": re[0],
                    "colonies": re[1],
                    "planets": re[2],
                    "colonies_pct": re[3],
                    "vortex": re[6],
                }
                if re[4]:
                    galaxy["visible"] = True
                else:
                    galaxy["invisible"] = True
                if re[5]:
                    galaxy["allow_new_players"] = True
                else:
                    galaxy["deny_new_players"] = True
                gcontext['galaxies'][re[0]] = galaxy.copy()
    # display statistics
    def display_stats():
        gcontext["general"] = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM users WHERE privilege=0 OR privilege>100 AND credits_bankruptcy > 0")
            re = cursor.fetchone()
            players = re[0]
            gcontext["players"] = players
            cursor.execute("SELECT count(*) FROM users WHERE privilege=0 OR privilege>100 AND lastlogin > now()-INTERVAL '2 day'")
            re = cursor.fetchone()
            gcontext["recent_players"] = re[0]
            cursor.execute("SELECT count(*) FROM nav_planet WHERE ownerid > 100")
            re = cursor.fetchone()
            colonies = re[0]
            cursor.execute("SELECT count(*) FROM nav_planet")
            re = cursor.fetchone()
            planets = re[0]
            gcontext["colonies"] = colonies
            gcontext["planets"] = planets
            gcontext["colonized"] = 100.0*colonies / planets
            gcontext["colonies_per_player"] = 1.0*colonies / players
            cursor.execute("SELECT login, planets FROM users WHERE privilege=0 OR privilege>100 AND id > 100 ORDER BY planets DESC LIMIT 1")
            re = cursor.fetchone()
            gcontext["max_colonies_playername"] = re[0]
            gcontext["max_colonies"] = re[1]
            cursor.execute("SELECT sum(quantity) FROM planet_buildings")
            re = cursor.fetchone()
            buildings = re[0]
            gcontext["buildings"] = buildings
            gcontext["buildings_average"] = 1.0*buildings / colonies
            cursor.execute("SELECT count(*) FROM planet_buildings_pending")
            re = cursor.fetchone()
            buildings_pending = re[0]
            gcontext["buildings_pending"] = buildings_pending
            gcontext["buildings_pending_average"] = 1.0*buildings_pending / colonies
            cursor.execute("SELECT sum(scientists), sum(soldiers), sum(workers) FROM vw_planets WHERE ownerid IS NOT NULL")
            re = cursor.fetchone()
            cursor.execute("SELECT "+str(re[0])+"+sum(cargo_scientists), "+str(re[1])+"+sum(cargo_soldiers), "+str(re[2])+"+sum(cargo_workers) FROM fleets WHERE ownerid IS NOT NULL")
            re = cursor.fetchone()
            gcontext["scientists"] = re[0]
            gcontext["soldiers"] = re[1]
            gcontext["workers"] = re[2]
            cursor.execute("SELECT count(*) FROM fleets WHERE ownerid > 100")
            re = cursor.fetchone()
            fleets = re[0]
            cursor.execute("SELECT sum(quantity) FROM fleets JOIN fleets_ships ON (fleets.id=fleets_ships.fleetid) WHERE fleets.ownerid > 100")
            re = cursor.fetchone()
            ships = re[0]
            gcontext["fleets"] = fleets
            gcontext["ships"] = ships
            cursor.execute("SELECT sum(signature) FROM fleets WHERE fleets.ownerid > 100")
            re = cursor.fetchone()
            gcontext["ships_signature"] = re[0]
            gcontext["ships_average"] = 1.0*ships/fleets
            cursor.execute("SELECT sum(quantity) FROM planet_ships")
            re = cursor.fetchone()
            ships_not_in_fleet = re[0]
            gcontext["ships_not_in_fleet"] = ships_not_in_fleet
            cursor.execute("SELECT sum(signature*quantity) FROM planet_ships INNER JOIN db_ships ON (db_ships.id=planet_ships.shipid)")
            re = cursor.fetchone()
            gcontext["ships_not_in_fleet_signature"] =re[0]
            gcontext["ships_not_in_fleet_percent"] = 1.0*(ships_not_in_fleet) / (ships_not_in_fleet+ships) * 100
            cursor.execute("SELECT count(*) FROM fleets WHERE action=0 AND ownerid > 100")
            re = cursor.fetchone()
            gcontext["fleets_patrolling"] = re[0]
            cursor.execute("SELECT count(*) FROM fleets WHERE action=1 or action=-1 AND ownerid > 100")
            re = cursor.fetchone()
            gcontext["fleets_moving"] = re[0]
            cursor.execute("SELECT count(*) FROM fleets WHERE action=2 AND ownerid > 100")
            re = cursor.fetchone()
            gcontext["fleets_recycling"] = re[0]
            cursor.execute("SELECT count(*) FROM battles WHERE time > now()-INTERVAL '1 days'")
            re = cursor.fetchone()
            gcontext["battles"] = re[0]
            cursor.execute("SELECT count(*) FROM invasions WHERE time > now()-INTERVAL '1 days'")
            re = cursor.fetchone()
            gcontext["invasions"] = re[0]
            cursor.execute("SELECT count(*) FROM reports WHERE type=7 AND datetime > now()-INTERVAL '1 days'")
            re = cursor.fetchone()
            gcontext["alerts"] = re[0]
            cursor.execute("SELECT sum(displays_ads) FROM users WHERE privilege=0 AND credits_bankruptcy > 0")
            re = cursor.fetchone()
            gcontext["displayed_ads"] = re[0]
            cursor.execute("SELECT sum(displays_pages) FROM users WHERE privilege=0 AND credits_bankruptcy > 0")
            re = cursor.fetchone()
            gcontext["displayed_pages"] = re[0]
            #cursor.execute("SELECT float4(1.0*sum(displays_ads)/sum(displays_pages)*100) FROM users WHERE privilege=0 AND credits_bankruptcy > 0")
            #re = cursor.fetchone()
            #gcontext["ads_pct"] = re[0]
            cursor.execute("SELECT count(1) FROM users WHERE privilege=0  AND credits_bankruptcy > 0 AND displays_ads < 0.9*displays_pages")
            re = cursor.fetchone()
            gcontext["players_blocking_ads"] = re[0]
            cursor.execute("SELECT float4(100.0*count(1)/"+str(players)+") FROM users WHERE privilege=0  AND credits_bankruptcy > 0 AND displays_ads < 0.9*displays_pages")
            re = cursor.fetchone()
            gcontext["players_blocking_ads_pct"] = re[0]
    def display_alliances_production():
        gcontext["alliances_production"] = {}
        with connection.cursor() as cursor:
            cursor.execute("SELECT alliances.tag, alliances.name," +
                " sum(ore_production), float4(100.0*sum(ore_production)/(select sum(ore_production) from nav_planet where ownerid > 100))," +
                " sum(hydrocarbon_production), float4(100.0*sum(hydrocarbon_production)/(select sum(hydrocarbon_production) from nav_planet where ownerid > 100))" +
                " FROM nav_planet" +
                "   INNER JOIN users on nav_planet.ownerid=users.id" +
                "   LEFT JOIN alliances on users.alliance_id=alliances.id" +
                " GROUP BY users.alliance_id, alliances.tag, alliances.name" +
                " ORDER BY sum(ore_production) DESC")
            res = cursor.fetchall()
            for re in res:
                if not re[0]:
                    continue
                ally = {
                    "tag": re[0],
                    "name": re[1],
                    "ore": re[2],
                    "ore_pct": re[3], # total univers production
                    "hydrocarbon": re[4], # total univers production
                    "hydrocarbon_pct": re[5], # total univers production
                }
                gcontext["alliances_production"][re[0]] = ally.copy()
    def display_server_stats():
        gcontext["db_buildings"] = datetime.datetime.fromtimestamp(cache.get('db_buildings_retrieved',0))
        gcontext["db_buildings_lastupdate"] = datetime.datetime.fromtimestamp(cache.get('db_buildings_last_retrieve',0))
        gcontext["db_buildings_req"] = datetime.datetime.fromtimestamp(cache.get('db_buildings_req_retrieved',0))
        gcontext["db_buildings_req_lastupdate"] = datetime.datetime.fromtimestamp(cache.get('db_buildings_req_last_retrieve',0))
        gcontext["db_buildings_req_r"] = datetime.datetime.fromtimestamp(cache.get('db_buildings_req_r_retrieved',0))
        gcontext["db_buildings_req_r_lastupdate"] = datetime.datetime.fromtimestamp(cache.get('db_buildings_req_r_last_retrieve',0))
        gcontext["db_ships"] = datetime.datetime.fromtimestamp(cache.get('db_ships_retrieved',0))
        gcontext["db_ships_lastupdate"] = datetime.datetime.fromtimestamp(cache.get('db_ships_last_retrieve',0))
        gcontext["db_ships_req"] = datetime.datetime.fromtimestamp(cache.get('db_ships_req_retrieved',0))
        gcontext["db_ships_req_lastupdate"] = datetime.datetime.fromtimestamp(cache.get('db_ships_req_last_retrieve',0))
        gcontext["db_ships_req_r"] = datetime.datetime.fromtimestamp(cache.get('db_ships_req_r_retrieved',0))
        gcontext["db_ships_req_r_lastupdate"] = datetime.datetime.fromtimestamp(cache.get('db_ships_req_r_last_retrieve',0))
        gcontext["db_research"] = datetime.datetime.fromtimestamp(cache.get('db_research_retrieved',0))
        gcontext["db_research_lastupdate"] = datetime.datetime.fromtimestamp(cache.get('db_research_last_retrieve',0))
        with connection.cursor() as cursor:
            cursor.execute("SELECT category, procedure, enabled, last_runtime, last_result, average_executiontime, last_runtime + run_every + INTERVAL '1 minute' <= now() FROM sys_executions")
            res = cursor.fetchall()
            gcontext["server"] = {}
            i = 0
            for re in res:
                proc = {
                    "category": re[0],
                    "procedure": re[1],
                    "last_runtime": re[3],
                    "last_result": re[4],
                    "average_executetime": re[5],
                }
                if not re[2]:
                    proc["disabled"] = True
                if re[6]:
                    proc["error"] = True
                gcontext["server"][i] = proc.copy()
                i += 1
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'stats'
    try:
        cat = int(request.GET.get("cat", "0"))
    except (KeyError, Exception):
        cat = 0
    if cat < 0 or cat > 3:
        cat = 0
    gcontext['tabnav'] = {
        '0':{'fake':True},
        '1':{'fake':True},
        '2':{'fake':True},
        '3':{'fake':True},
    }
    gcontext['tabnav'][str(cat)]["selected"] = True
    if cat == 0:
            display_galaxies()
    elif cat == 1:
            display_stats()
    elif cat == 2:
            display_alliances_production()
    elif cat == 3:
            display_server_stats()
    gcontext['menu'] = menu(request)
    context = gcontext
    t = loader.get_template('exile/dev-stats.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def help(request):
    def display_help(cat):
        if cat == "buildings": # display help on buildings
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, category," +
                    "cost_ore, cost_hydrocarbon, workers, floor, space, production_ore, production_hydrocarbon, energy_production, workers*maintenance_factor/100.0, upkeep, energy_consumption," +
                    "storage_ore, storage_hydrocarbon, storage_energy" +
                    " FROM sp_list_available_buildings(%s) WHERE not is_planet_element", [gcontext['exile_user'].id])
                res = cursor.fetchall()
                gcontext['category'] = {}
                for re in res:
                    category = re[1]
                    building = {
                        "id": re[0],
                        "category": re[1],
                        "name": getBuildingLabel(re[0]),
                        "description": getBuildingDescription(re[0]),
                        "ore": re[2],
                        "hydrocarbon": re[3],
                        "workers": re[4],
                        "floor": re[5],
                        "space": re[6],
                        "ore_production": re[7],
                        "hydrocarbon_production": re[8],
                        "energy_production": re[9],
                        "upkeep_workers": int(re[10]),
                        "upkeep_credits": 0, #re[11]
                        "upkeep_energy": re[12],
                        "ore_storage": re[13],
                        "hydrocarbon_storage": re[14],
                        "energy_storage": re[15],
                    }
                    if re[7] > 0:
                        building["produce_ore"] = True
                    if re[8] > 0:
                        building["produce_hydrocarbon"] = True
                    if re[9] > 0:
                        building["produce_energy"] = True
                    if re[13] > 0:
                        building["storage_ore"] = True
                    if re[14] > 0:
                        building["storage_hydrocarbon"] = True
                    if re[15] > 0:
                        building["storage_energy"] = True
                    ck = 'category' + str(category)
                    if not ck in gcontext['category']:
                        gcontext['category'][ck] = {}
                    gcontext['category'][ck][re[0]] = building.copy()
        elif cat == "research": # display help on researches
            with connection.cursor() as cursor:
                cursor.execute("SELECT researchid, category, total_cost, level, levels" +
                    " FROM sp_list_researches(%s) WHERE level > 0 OR (researchable AND planet_elements_requirements_met)" +
                    " ORDER BY category, researchid", [gcontext['exile_user'].id])
                res = cursor.fetchall()
                gcontext['category'] = {}
                for re in res:
                    category = re[1]
                    research = {
                        "id": re[0],
                        "name": getResearchLabel(re[0]),
                        "description": getResearchDescription(re[0]),
                    }
                    if re[3] < re[4]:
                        research["cost_credits"] = re[2]
                    else:
                        research["cost_credits"] = ""
                    ck = 'category' + str(category)
                    if not ck in gcontext['category']:
                        gcontext['category'][ck] = {}
                    gcontext['category'][ck][re[0]] = research.copy()
        elif cat == "ships": # display help on ships
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, category, cost_ore, cost_hydrocarbon, crew," +
                    " signature, capacity, handling, speed, weapon_turrets, weapon_dmg_em + weapon_dmg_explosive + weapon_dmg_kinetic + weapon_dmg_thermal AS weapon_power, " +
                    " weapon_tracking_speed, hull, shield, recycler_output, long_distance_capacity, droppods, cost_energy, upkeep, required_vortex_strength, leadership" +
                    " FROM sp_list_available_ships(%s) WHERE new_shipid IS NULL", [gcontext['exile_user'].id])
                res = cursor.fetchall()
                gcontext['category'] = {}
                for re in res:
                    category = re[1]
                    ShipId = re[0]
                    ship = {
                        "id": ShipId,
                        "category": re[1],
                        "name": getShipLabel(re[0]),
                        "description": getShipDescription(re[0]),
                        "ore": re[2],
                        "hydrocarbon": re[3],
                        "crew": re[4],
                        "energy": re[17],
                        "ship_signature": re[5],
                        "ship_cargo": re[6],
                        "ship_handling": re[7],
                        "ship_speed": re[8],
                        "ship_upkeep": re[18],
                        "ship_hull": re[12],
                        "ship_required_vortex_strength": re[19],
                        "ship_leadership": re[20],
                    }
                    if re[10] > 0:
                        ship["ship_turrets"] = re[9]
                        ship["ship_power"] = re[10]
                        ship["ship_tracking_speed"] = re[11]
                        ship["attack"] = True
                    if re[13] > 0:
                        ship["ship_shield"] = re[13]
                        ship["shield"] = True
                    if re[14] > 0:
                        ship["ship_recycler_output"] = re[14]
                        ship["recycler_output"] = True
                    if re[15] > 0:
                        ship["ship_long_distance_capacity"] = re[15]
                        ship["long_distance_capacity"] = True
                    if re[16] > 0:
                        ship["ship_droppods"] = re[16]
                        ship["droppods"] = True
                    ship["building"] = {}
                    for i in retrieveShipsReqCache():
                        if i[0] == ShipId:
                            ship["building"][i[1]] = getBuildingLabel(i[1])
                            ship["buildingsrequired"] = True
                    ck = 'category' + str(category)
                    if not ck in gcontext['category']:
                        gcontext['category'][ck] = {}
                    gcontext['category'][ck][re[0]] = ship.copy()
        elif cat == "tags":
            with connection.cursor() as cursor:
                cursor.execute("SELECT code, image FROM precise_bbcode_smileytag");
                res = cursor.fetchall()
                gcontext['smileys'] = {}
                for re in res:
                    smiley = {
                        'code': re[0],
                        'image': re[1],
                    }
                    gcontext['smileys'][re[0]] = smiley.copy()
        gcontext['tabnav'] = {'cat': cat}
    gcontext = request.session.get('gcontext',{})
    context = gcontext
    gcontext['selectedmenu'] = 'help'
    gcontext['menu'] = menu(request)
    cat = request.GET.get("cat", "general").strip()
    if cat != "buildings" and cat != "research" and cat != "ships" and cat != "tags":
        cat = "general"
    display_help(cat)
    t = loader.get_template('exile/help.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def options(request):
    def display_general():
        with connection.cursor() as cursor:
            cursor.execute("SELECT avatar_url, regdate, users.description, 0," +
                " alliance_id, a.tag, a.name, r.label" +
                " FROM users" +
                " LEFT JOIN alliances AS a ON (users.alliance_id = a.id)" +
                " LEFT JOIN alliances_ranks AS r ON (users.alliance_id = r.allianceid AND users.alliance_rank = r.id) " +
                " WHERE users.id = %s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            gcontext["general"] = {}
            gcontext["regdate"] = re[1]
            gcontext["description"] = re[2]
            gcontext["ip"] = request.META['REMOTE_ADDR']
            if not re[0]:
                gcontext["general"]["noavatar"] = True
            else:
                gcontext["avatar_url"] = re[0]
                gcontext["general"]["avatar"] = True
            if re[4]:
                gcontext["alliancename"] = re[6]
                gcontext["alliancetag"] = re[5]
                gcontext["rank_label"] = re[7]
                gcontext["general"]["alliance"] = True
            else:
                gcontext["general"]["noalliance"] = True
    def display_options():
        with connection.cursor() as cursor:
            cursor.execute("SELECT int4(date_part('epoch', deletion_date-now())), timers_enabled, display_alliance_planet_name, email, score_visibility, skin FROM users WHERE id=%s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            gcontext["options"] = {}
            if not re[0]:
                gcontext["options"]["delete_account"] = True
            else:
                gcontext["remainingtime"] = re[0]
                gcontext["options"]["account_deleting"] = True
            if re[1]:
                gcontext["options"]["timers_enabled"] = True
            if re[2]:
                gcontext["options"]["display_alliance_planet_name"] = True
            gcontext["options"]["score_visibility_" + str(re[4])] = True
            gcontext["options"]["skin_" + str(re[5])] = True
            gcontext["email"] = re[3]
    def display_holidays():
        # check if holidays will be activated soon
        with connection.cursor() as cursor:
            cursor.execute("SELECT int4(date_part('epoch', start_time-now())) FROM users_holidays WHERE userid=%s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            if re:
                remainingtime = re[0]
            else:
                remainingtime = 0
            gcontext["holidays"] = {}
            if remainingtime > 0:
                gcontext["remaining_time"] = remainingtime
                gcontext["holidays"]['start_in'] = True
                gcontext['showSubmit'] = False
            else:
                # holidays can be activated only if never took any holidays or it was at least 7 days ago
                cursor.execute("SELECT int4(date_part('epoch', now()-last_holidays)) FROM users WHERE id=%s", [gcontext['exile_user'].id])
                re = cursor.fetchone()
                if re[0] and re[0] < gcontext["holidays_breaktime"]:
                    gcontext["remaining_time"] = gcontext["holidays_breaktime"]-re[0]
                    gcontext["holidays"]['cant_enable'] = True
                    gcontext['showSubmit'] = False
                else:
                    gcontext["holidays"]['can_enable'] = True
                    gcontext["submit"]["holidays"] = True
    def display_reports():
        with connection.cursor() as cursor:
            cursor.execute("SELECT type*100+subtype FROM users_reports WHERE userid=%s", [gcontext['exile_user'].id])
            res = cursor.fetchall()
            gcontext["reports"] = {'fake': True}
            for re in res:
                gcontext["reports"]["c"+str(re[0])] = True
    def display_mail():
        with connection.cursor() as cursor:
            cursor.execute("SELECT autosignature FROM users WHERE id=%s", [gcontext['exile_user'].id])
            re = cursor.fetchone()
            if re:
                gcontext["autosignature"] = re[0]
            else:
                gcontext["autosignature"] = ""
            gcontext["mail"] = True
    def display_signature():
        gcontext["signature"] = True
        gcontext['showSubmit'] = False
    def displayPage():
        gcontext['addAllowedImageDomain'] = "*"
        gcontext["cat"] = optionCat
        gcontext["name"] = gcontext['exile_user'].login
        gcontext["universe"] = config.universe
        if optionCat == 2:
            display_options()
        elif optionCat == 3:
            display_holidays()
        elif optionCat == 4:
            display_reports()
        elif optionCat == 5:
            display_mail()
        elif optionCat == 6:
            display_signature()
        else:
            display_general()
        if gcontext['changes_status']:
            gcontext['changes'] = True
        gcontext['nav'] = {
            'cat1':{'fake':True},
            'cat2':{'fake':True},
            'cat3':{},
            'cat4':{'fake':True},
            'cat5':{'fake':True},
            'cat6':{'fake':True},
        }
        gcontext['nav']["cat"+str(optionCat)]["selected"] = True
        if config.allowedHolidays:
            gcontext['nav']["cat3"]['fake'] = True
        if gcontext['showSubmit']:
            gcontext["submit"] = {'fake':True}
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'options'
    if request.GET.get("frame","") == "1":
        with connection.cursor() as cursor:
            cursor.execute("UPDATE users SET inframe=true WHERE id=%s", [gcontext['exile_user'].id])
            return
    gcontext['holidays_breaktime'] = 7*24*60*60 # time before being able to set the holidays again
    gcontext['changes_status'] = ""
    gcontext['showSubmit'] = True
    gcontext["submit"] = {}
    avatar = request.POST.get("avatar","").strip()
    #email = request.POST.get("email").strip()
    description = strip_tags(request.POST.get("description","").strip())
    #password = Trim(request.POST.get("password"))
    #confirm_password = Trim(request.POST.get("confirm_password"))
    timers_enabled = bool(request.POST.get("timers_enabled",""))
    display_alliance_planet_name = bool(request.POST.get("display_alliance_planet_name",""))
    try:
        score_visibility = int(request.POST.get("score_visibility", "0"))
    except (KeyError, Exception):
        score_visibility = 0
    if score_visibility < 0 or score_visibility > 2:
        score_visibility = 0
    try:
        skin = int(request.POST.get("skin", "0"))
    except (KeyError, Exception):
        skin = 0
    deletingaccount = request.POST.get("deleting","")
    deleteaccount = request.POST.get("delete","")
    autosignature = request.POST.get("autosignature","")
    try:
        optionCat = int(request.GET.get("cat", "1"))
    except (KeyError, Exception):
        optionCat = 1
    if optionCat < 1 or optionCat > 6:
        optionCat = 1
    DoRedirect = False
    if not config.allowedHolidays and optionCat == 3:
        optionCat = 1 # only display holidays formular if it is allowed
    #if not oPlayerInfo("payed") and optionCat = 5 then optionCat = 1 ' mail formular is only available to registered/payed accounts
    #if IsPlayerAccount() and optionCat = 6 then optionCat = 1 ' under development
    if request.POST.get("submit",""):
        gcontext['changes_status'] = "done"
        query = ""
        if optionCat == 1:
            try:
                if avatar:
                    validate = URLValidator(schemes=('http', 'https', 'ftp', 'ftps', 'rtsp', 'rtmp'))
                    validate(avatar)
                # save updated information
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE users SET avatar_url=%s, description=%s WHERE id=%s", [avatar, description, gcontext['exile_user'].id])
            except ValidationError:
                #avatar is invalid
                gcontext['changes_status'] = "check_avatar"
        elif optionCat == 2:
    #           dim forwardedfor: forwardedfor = Request.ServerVariables("HTTP_X_FORWARDED_FOR")
    #           dim ipaddress: ipaddress = Request.ServerVariables("REMOTE_ADDR")
    #           dim useragent: useragent = Request.ServerVariables("HTTP_USER_AGENT")
            with connection.cursor() as cursor:
                if skin == 0:
                    skin = "'s_default'"
                else:
                    skin = "'s_transparent'"
                query += ", skin=" + str(skin)
                if deletingaccount and not deleteaccount:
                    query += ", deletion_date=null"
                if not deletingaccount and deleteaccount:
                    query += ", deletion_date=now() + INTERVAL '2 days'"
                query += " WHERE id=" + str(gcontext['exile_user'].id)
                cursor.execute("UPDATE users SET timers_enabled=%s ,display_alliance_planet_name=%s ,score_visibility=%s" + query, [timers_enabled, display_alliance_planet_name, score_visibility])
        elif optionCat == 3:
            if request.POST.get("holidays",""):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COALESCE(int4(date_part('epoch', now()-last_holidays)), 10000000) AS holidays_cooldown, (SELECT 1 FROM users_holidays WHERE userid=users.id) FROM users WHERE id=%s", [gcontext['exile_user'].id])
                    re = cursor.fetchone()
                    if re[0] > gcontext['holidays_breaktime'] and not re[1]:
                        cursor.execute("INSERT INTO users_holidays(userid, start_time, min_end_time, end_time) VALUES(%s,now()+INTERVAL '24 hours', now()+INTERVAL '72 hours', now()+INTERVAL '22 days')", [gcontext['exile_user'].id])
                        return HttpResponseRedirect(reverse('exile:options')+"?cat=3")
        elif optionCat == 4:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM users_reports WHERE userid=%s", [gcontext['exile_user'].id])
                for x in request.POST.getlist("r",[]):
                    try:
                        typ = int(int(x) / 100)
                    except (KeyError, Exception):
                        continue
                    subtyp = int(x) % 100
                    cursor.execute("INSERT INTO users_reports(userid, type, subtype) VALUES(%s, %s, %s)", [gcontext['exile_user'].id, typ, subtyp])
        elif optionCat == 5:
            if autosignature:
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE users SET autosignature=%s WHERE id=%s", [autosignature, gcontext['exile_user'].id])
        DoRedirect = True
    if DoRedirect:
        return HttpResponseRedirect(reverse('exile:options')+'?cat='+str(optionCat))
    else:
        displayPage()
    context = gcontext
    gcontext['menu'] = menu(request)
    t = loader.get_template('exile/options.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

def FormatBattle(request,battleid, creator, pointofview, ispubliclink):
    gcontext = request.session.get('gcontext',{})
    # Retrieve/assign battle info
    with connection.cursor() as cursor:
        cursor.execute("SELECT time, planetid, name, galaxy, sector, planet, rounds," +
            " EXISTS(SELECT 1 FROM battles_ships WHERE battleid=%(battleid)s AND owner_id=%(creator)s AND won LIMIT 1), MD5(key||%(creator)s)," +
            " EXISTS(SELECT 1 FROM battles_ships WHERE battleid=%(battleid)s AND owner_id=%(creator)s AND damages > 0 LIMIT 1) AS see_details" +
            " FROM battles INNER JOIN nav_planet ON (planetid=nav_planet.id) WHERE battles.id=%(battleid)s", {'battleid': battleid, 'creator': creator})
        re = cursor.fetchone()
        if not re:
            return
        gcontext["battleid"] = battleid
        gcontext["userid"] = creator
        gcontext["key"] = re[8]
        gcontext["time"] = re[0]
        gcontext["battleplanetid"] = re[1]
        gcontext["battleplanet"] = re[2]
        gcontext["battleg"] = re[3]
        gcontext["battles"] = re[4]
        gcontext["battlep"] = re[5]
        gcontext["rounds"] = re[6]
        if not ispubliclink:
            # link for the freely viewable report of this battle
            gcontext["publiclink"] = True
        rounds = re[6]
        hasWon = re[7]
        showEnemyDetails = re[9] or hasWon or rounds > 1
        cursor.execute("SELECT fleet_id, shipid, destroyed_shipid, sum(count)" +
                " FROM battles_fleets" +
                "   INNER JOIN battles_fleets_ships_kills ON (battles_fleets.id=fleetid)" +
                " WHERE battleid=%s" +
                " GROUP BY fleet_id, shipid, destroyed_shipid" +
                " ORDER BY sum(count) DESC", [battleid])
        res = cursor.fetchall()
        if not res:
            killsArray = []
            killsCount = -1
        else:
            killsArray = res.copy()
            killsCount = len(killsArray)
        cursor.execute("SELECT owner_name, fleet_name, shipid, shipcategory, shiplabel, count, lost, killed, won, relation1," +
            " owner_id , relation2, fleet_id, attacked, mod_shield, mod_handling, mod_tracking_speed, mod_damage, alliancetag" +
            " FROM sp_get_battle_result(%s, %s, %s)", [battleid, creator, pointofview])
        res = cursor.fetchall()
        category = -1
        lastCategory = -1
        player_ships = 0
        player_lost = 0
        player_killed = 0
        fleet_ships = 0
        fleet_lost = 0
        fleet_killed = 0
        cat_ships = 0
        cat_lost = 0
        cat_killed = 0
        cpt = 0
        gcontext['opponent'] = {}
        for re in res:
            # on crée un opponent si inconnu
            if not re[10] in gcontext['opponent'].keys():
                gcontext['opponent'][re[10]] = {
                    'opponent': re[0],
                    'fleet' : {},
                    'ships': 0,
                    'lost': 0,
                    'killed': 0,
                    'after': 0,
                    'self': False,
                    'ally': False,
                    'friend': False,
                    'enemy': False,
                    'alliance': False,
                    'alliancetag': '',
                    'won': False,
                    'attack': False,
                    'defend': False,
                    'public': False,
                }
            # on cumule des stats sur l'opponent
            gcontext['opponent'][re[10]]['ships'] += re[5]
            gcontext['opponent'][re[10]]['lost'] += re[6]
            gcontext['opponent'][re[10]]['killed'] += re[7]
            gcontext['opponent'][re[10]]['after'] += (re[5]-re[6])
            # on crée une flotte si inconnue
            if not re[12] in gcontext['opponent'][re[10]]['fleet'].keys():
                gcontext['opponent'][re[10]]['fleet'][re[12]] = {
                    'category': {},
                    'fleet': re[1],
                    'ships': 0,
                    'lost': 0,
                    'killed': 0,
                    'after': 0,
                    'self': False,
                    'ally': False,
                    'friend': False,
                    'enemy': False,
                    'mod_shield': re[14],
                    'mod_handling': re[15],
                    'mod_tracking_speed': re[16],
                    'mod_damage': re[17],
                }
            # on cumule des stats sur la flotte
            gcontext['opponent'][re[10]]['fleet'][re[12]]['ships'] += re[5]
            gcontext['opponent'][re[10]]['fleet'][re[12]]['lost'] += re[6]
            gcontext['opponent'][re[10]]['fleet'][re[12]]['killed'] += re[7]
            gcontext['opponent'][re[10]]['fleet'][re[12]]['after'] += (re[5]-re[6])
            # on cache les modificateurs de la flotte si conditions
            if not showEnemyDetails and re[9] < config.rFriend:
                gcontext['opponent'][re[10]]['fleet'][re[12]]["mod_shield"] = "?"
                gcontext['opponent'][re[10]]['fleet'][re[12]]["mod_handling"] = "?"
                gcontext['opponent'][re[10]]['fleet'][re[12]]["mod_tracking_speed"] = "?"
                gcontext['opponent'][re[10]]['fleet'][re[12]]["mod_damage"] = "?"
            # on crée une category de vaisseau dans la flotte si inconnue
            if not re[3] in gcontext['opponent'][re[10]]['fleet'][re[12]]['category'].keys():
                gcontext['opponent'][re[10]]['fleet'][re[12]]['category'][re[3]] = {}
            # on y ajoute les vaisseaux
            gcontext['opponent'][re[10]]['fleet'][re[12]]['category'][re[3]][cpt] = {
                'name': True,
                'label': re[4],
                'ships': re[5],
                'lost': re[6],
                'killed': {}, # re[7], # cumul categorique
                'after': (re[5]-re[6]),
                'killed_zero': False,
                'killed_total': False,
            }
            killed = 0
            total = 0
            for i in killsArray:
                if re[12] == i[0] and re[2] == i[1]:
                    gcontext['opponent'][re[10]]['fleet'][re[12]]['category'][re[3]][cpt]['killed'][str(i[0])+':'+str(i[2])] = {
                        "killed_name": getShipLabel(i[2]),
                        "killed_count": i[3],
                    }
                    total += i[3]
                    killed += 1 # count how many different ships were destroyed:
            if killed == 0:
                gcontext['opponent'][re[10]]['fleet'][re[12]]['category'][re[3]][cpt]["killed_zero"] = True
            if killed > 1:
                gcontext['opponent'][re[10]]['fleet'][re[12]]['category'][re[3]][cpt]["killed_total"] = total
            if re[11] == config.rSelf:
                gcontext['opponent'][re[10]]["self"] = True
                gcontext['opponent'][re[10]]['fleet'][re[12]]["self"] = True
            elif re[11] == config.rAlliance:
                gcontext['opponent'][re[10]]["ally"] = True
                gcontext['opponent'][re[10]]['fleet'][re[12]]["ally"] = True
            elif re[11] == config.rFriend:
                gcontext['opponent'][re[10]]["friend"] = True
                gcontext['opponent'][re[10]]['fleet'][re[12]]["friend"] = True
            else:
                gcontext['opponent'][re[10]]["enemy"] = True
                gcontext['opponent'][re[10]]['fleet'][re[12]]["enemy"] = True
            if re[18]:
                gcontext['opponent'][re[10]]['alliance'] = True
                gcontext['opponent'][re[10]]['alliancetag'] = re[18]
            if re[8]:
                gcontext['opponent'][re[10]]['won'] = True
            if re[13]:
                gcontext['opponent'][re[10]]['attack'] = True
            else:
                gcontext['opponent'][re[10]]['defend'] = True
            cpt += 1

def battleview(request):
    global config
    gcontext = request.session.get('gcontext',{})
    battlekey = request.GET.get("key", "").strip()
    if not battlekey:
        return HttpResponseRedirect(reverse('exile:reports'))
    try:
        creator = int(request.GET.get("by", 0))
    except (KeyError, Exception):
        creator = 0
    if not creator:
        return HttpResponseRedirect(reverse('exile:reports'))
    try:
        fromview = int(request.GET.get("v", 0))
    except (KeyError, Exception):
        fromview = 0
    if not fromview:
        return HttpResponseRedirect(reverse('exile:reports'))
    try:
        id = int(request.GET.get("id", 0))
    except (KeyError, Exception):
        id = 0
    if not id:
        return HttpResponseRedirect(reverse('exile:reports'))
    # check if associated key is correct, and redirect if not
    with connection.cursor() as cursor:
        cursor.execute(" SELECT 1 FROM battles WHERE id=%s AND %s=MD5(key||%s) ", [id, battlekey, creator])
        res = cursor.fetchone()
        if not res:
            return HttpResponseRedirect(reverse('exile:reports'))
        FormatBattle(request,id, creator, fromview, True)
    context = gcontext
    t = loader.get_template('exile/battle.html')
    context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)

@construct
@logged
def battle(request):
    global config
    gcontext = request.session.get('gcontext',{})
    gcontext['selectedmenu'] = 'battles'
    try:
        id = int(request.GET.get("id", 0))
    except (KeyError, Exception):
        id = 0
    if id == 0:
        return HttpResponseRedirect(reverse('exile:reports'))
    creator = gcontext['exile_user'].id
    try:
        fromview = int(request.GET.get("v", gcontext['exile_user'].id))
    except (KeyError, Exception):
        fromview = gcontext['exile_user'].id
    display_battle = True
    # check that we took part in the battle to display it
    with connection.cursor() as cursor:
        cursor.execute("SELECT battleid FROM battles_ships WHERE battleid=%s AND owner_id=%s LIMIT 1", [id, gcontext['exile_user'].id])
        res = cursor.fetchone()
        display_battle = res
        if not display_battle and gcontext['exile_user'].alliance_id:
            if hasRight(request,"can_see_reports"):
                # check if it is a report from alliance reports
                cursor.execute("SELECT owner_id FROM battles_ships WHERE battleid=%s AND (SELECT alliance_id FROM users WHERE id=owner_id)=%s LIMIT 1", [id, gcontext['exile_user'].alliance_id])
                res = cursor.fetchone()
                display_battle = res
                if res:
                    creator = res[0] #fromview
        if display_battle:
            FormatBattle(request,id, creator, fromview, False)
        else:
            return HttpResponseRedirect(reverse('exile:reports'))
        context = gcontext
        gcontext['menu'] = menu(request)
        t = loader.get_template('exile/battle.html')
        context['content'] = t.render(gcontext, request)
    return render(request, 'exile/layout.html', context)
