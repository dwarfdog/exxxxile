import time, datetime, random, time
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    #def add_arguments(self, parser):
    #    parser.add_argument('poll_ids', nargs='+', type=int)

    def ResolveBattles(self, cursor):
        Rounds = 25
        rounds_time = time.time()
        print("Check for battles",rounds_time)
        # list planets where there are battles
        cursor.execute("SELECT id, COALESCE(sp_get_user(ownerid), ''), galaxy, sector, planet FROM nav_planet WHERE next_battle <= now() LIMIT 1;")
        resg = cursor.fetchall()
        if not resg:
            print("No battles found")
        for re in resg:
            planetid = re[0]
            data = "planet:{owner:'" + str(re[1]) + "',g:" + str(re[2]) + ",s:" + str(re[3]) + ",p:" + str(re[4]) + "}"
            print(data)
            # retrieve opponents relationships
            cursor.execute("SELECT f1.ownerid, f2.ownerid, sp_relation(f1.ownerid, f2.ownerid)" +
                            " FROM (SELECT ownerid, bool_or(attackonsight) AS attackonsight FROM fleets WHERE planetid=%s" +
                            " AND engaged GROUP BY ownerid) as f1," +
                            " (SELECT ownerid, bool_or(attackonsight) AS attackonsight FROM fleets WHERE planetid=%s AND engaged GROUP BY ownerid) as f2" +
                            " WHERE f1.ownerid > f2.ownerid AND (sp_relation(f1.ownerid, f2.ownerid) >= 0" +
                            " OR (sp_relation(f1.ownerid, f2.ownerid) = -1 AND NOT f1.attackonsight AND NOT f2.attackonsight) );", [planetid, planetid])
            oFriends = cursor.fetchall()
            if not oFriends:
                friendsCount = -1
                friendsArray = []
            else:
                friendsArray = oFriends
                friendsCount = len(oFriends)
            #for oFriend in oFriends:
            #    print(oFriend)
            # retrieve fleets near the planet
    #       query = "SELECT fleets.ownerid, fleets.id, db_ships.id, hull, shield, handling, weapon_ammo, weapon_power, weapon_tracking_speed, weapon_turrets, quantity, dest_planetid, 100+fleets.mod_shield, 100+fleets.mod_handling, 100+fleets.mod_tracking_speed, 100+fleets.mod_damage, attackonsight," &_
    #               " weapon_dmg_em, weapon_dmg_explosive, weapon_dmg_kinetic, weapon_dmg_thermal," &_
    #               " resist_em, resist_explosive, resist_kinetic, resist_thermal, tech" &_
    #               " FROM (fleets INNER JOIN fleets_ships ON (fleetid = id))" &_
    #               "   INNER JOIN db_ships ON (fleets_ships.shipid = db_ships.id)" &_
    #               " WHERE fleets.planetid=" & planetid & " AND engaged" &_
    #               " ORDER BY fleets.speed DESC, random();"
    #       set oFleets = createobject("ADODB.Recordset")
    #       oFleets.open query, oConn
    #
    #       fleetsArray = oFleets.GetRows()
    #       fleetsCount = UBound(fleetsArray, 2)
    #
    #       oFleets.Close
    #       set oFleets = Nothing
            # create the battlefield
            battle = {}
            cursor.execute("SELECT fleets.ownerid, fleets.id, db_ships.id, hull, shield, handling, weapon_ammo, weapon_power, weapon_tracking_speed," +
                " weapon_turrets, quantity, dest_planetid, fleets.mod_shield, fleets.mod_handling, fleets.mod_tracking_speed, fleets.mod_damage, attackonsight," +
                " weapon_dmg_em, weapon_dmg_explosive, weapon_dmg_kinetic, weapon_dmg_thermal," +
                " resist_em, resist_explosive, resist_kinetic, resist_thermal, tech" +
                " FROM (fleets INNER JOIN fleets_ships ON (fleetid = id))" +
                "   INNER JOIN db_ships ON (fleets_ships.shipid = db_ships.id)" +
                " WHERE fleets.planetid=%s AND engaged" +
                " ORDER BY fleets.speed DESC, random();", [planetid])
            oFleets = cursor.fetchall()
            shoots = []
            ships = []
            players = {}
            print('building fleets')
            for oFleet in oFleets:
                #print(oFleet)
                if not oFleet[0] in players.keys():
                    friends = []
                    for oFriend in oFriends:
                        if oFleet[0] == oFriend[0]:
                            friends.append(oFriend[1])
                        elif oFleet[0] == oFriend[1]:
                            friends.append(oFriend[0])
                    players[oFleet[0]] = {'friends': friends.copy()}
                for i in range(oFleet[10]):
                    #  owner, id, shipid, hull, shield, handling, res_em, res_expl, res_kin, res_ther, [shot], mod_shield, mod_handling, mod_tracking_speed, mod_damage, tech, i
                    if not [oFleet[11]]:
                        ships.append([oFleet[0], oFleet[1], oFleet[2], oFleet[3], oFleet[4]*oFleet[12]/100, oFleet[5]*oFleet[13]/100, oFleet[21] , oFleet[22], oFleet[23], oFleet[24], [oFleet[9], oFleet[14]*oFleet[8]/100, oFleet[15]*oFleet[17]/100, oFleet[15]*oFleet[18]/100, oFleet[15]*oFleet[19]/100, oFleet[15]*oFleet[20]/100], oFleet[12], oFleet[13], oFleet[14], oFleet[15], oFleet[25], i])
                    else:
                        ships.append([oFleet[0], oFleet[1], oFleet[2], oFleet[3], oFleet[4]*oFleet[12]/100, oFleet[5]*oFleet[13]/100, oFleet[21] , oFleet[22], oFleet[23], oFleet[24], [oFleet[9], oFleet[14]/2*oFleet[8]/100, oFleet[15]*oFleet[17]/100, oFleet[15]*oFleet[18]/100, oFleet[15]*oFleet[19]/100, oFleet[15]*oFleet[20]/100], oFleet[12], oFleet[13], oFleet[14], oFleet[15], oFleet[25], i])
            for d, player in players.items():
                enemies = [k for k, v in players.items() if k != d and not d in v['friends']]
                players[d]['enemies'] = enemies.copy()
            random.shuffle(ships)
            counter = {}
            possible_targets = {}
            reverse_possible_targets = {}
            selected_targets = {}
            possible_targets_stats = {}
            print('building stats')
            for ship in ships:
                cship_key = str(ship[0])+':'+str(ship[1])+':'+str(ship[2])
                if cship_key in counter.keys():
                    continue
                counter[cship_key] = {'killed':{}, 'damages':0, 'before':0, 'after':0, 'mod_shield':0, 'mod_handling':0, 'mod_tracking_speed':0, 'mod_damage':0}
                if not ship[0] in possible_targets.keys():
                    listOfStr = [k for k,x in enumerate(ships) if x[0] in players[ship[0]]['enemies']]
                    random.shuffle(listOfStr)
                    possible_targets[ship[0]] = { i : listOfStr[i] for i in range(0, len(listOfStr) ) }
                    #possible_targets[ship[0]] = [k for k,x in enumerate(ships) if x[0] in players[ship[0]]['enemies']]#list(filter(lambda x: x[0] in players[ship[0]]['enemies'], ships))
                    for k,pt in possible_targets[ship[0]].items():
                        if pt not in reverse_possible_targets.keys():
                            reverse_possible_targets[pt] = {}
                        if ship[0] not in reverse_possible_targets[pt].keys():
                            reverse_possible_targets[pt][ship[0]] = []
                        reverse_possible_targets[pt][ship[0]].append(k)
                shot = ship[10]
                if shot[0]: # ship can shot
                    for target in possible_targets[ship[0]]:
                        target = ships[target]
                        ship_key = str(ship[0])+'|'+str(ship[1])+'|'+str(ship[2])
                        if not ship_key in possible_targets_stats.keys():
                            possible_targets_stats[ship_key] = {}
                        target_key = str(target[0])+'|'+str(target[1])+'|'+str(target[2])
                        if not target_key in possible_targets_stats[ship_key].keys():
                            chance_to_hit = max(shot[1]/target[5],1)
                            tech_diff = ship[15] - target[15]
                            if tech_diff < 0:
                                chance_to_hit *= 0.85**abs(tech_diff);
                            elif tech_diff > 0:
                                chance_to_hit *= 1.10**tech_diff;
                            if chance_to_hit >= 1:
                                chance_to_hit = 1
                            if chance_to_hit < 0:
                                chance_to_hit = 0
                            degats = shot[2]*(100-target[6])/100 + shot[3]*(100-target[7])/100 + shot[4]*(100-target[8])/100 + shot[5]*(100-target[9])/100
                            avg_degats = degats * chance_to_hit
                            possible_targets_stats[ship_key][target_key] = {
                                'degats':degats,
                                'avg_degats':avg_degats,
                                'chance_to_hit':chance_to_hit,
                                #'back_link':[k for k,x in enumerate(ships) if x[0] in players[ship[0]]['enemies'] and target_key == str(x[0])+'|'+str(x[1])+'|'+str(x[2])],#list(filter(lambda x: x[0] in players[ship[0]]['enemies'] and target_key == str(x[0])+'|'+str(x[1])+'|'+str(x[2]), ships))
                            }
                    # TODO
                    # shuffle(possible_targets) then sort them by possible_targets_stats[ship_key][target_key]['avg_degats']
                    # QUESTION: this is an targeting optimization, how can a ship know others ships mods, from ship type ok but from other mods sources ?
                    # Maybe degats base should be = shot[2] + shot[3] + shot[4] + shot[5] to simulate this lack of knowledge
                    # it suppose to compute the real degats too, for algo optimization (like now)
                    #
                    # le ciblage est trop gourmand en temps
                    #
            #for r in range(Rounds):
            #print(possible_targets_stats)
            r = 0
            for ship in ships:
                counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['before'] += 1
                counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['shield'] = ship[4]
                if not counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['mod_shield']:
                    counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['mod_shield'] = ship[11]
                if not counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['mod_handling']:
                    counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['mod_handling'] = ship[12]
                if not counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['mod_tracking_speed']:
                    counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['mod_tracking_speed'] = ship[13]
                if not counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['mod_damage']:
                    counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['mod_damage'] = ship[14]
            print('running fight')
            while True: #time.time()-rounds_time<120: # limit 2min
                #if r%100 == 0:
                print('round',str(r),str(time.time()))
                targets = 0
                #cpt = 0
                for ship in ships:
                    #cpt += 1
                    #if cpt %(len(ships)/100) == 0:
                    #    print('.')
                    if not ship:
                        continue
                    shot = ship[10]
                    if shot[0]: # ship can shot
                        ship_key = str(ship[0])+'|'+str(ship[1])+'|'+str(ship[2])
                        if not len(possible_targets[ship[0]]):
                            continue
                        for singleshot in range(shot[0]):
                            #pship_key = ship_key+'|'+str(ship[16])
                            #target = False
                            #if pship_key in selected_targets.keys():
                            #    #target_index = False
                            #    #prioritary_target_avg_degats = True
                            #    targetk = selected_targets[pship_key]
                            #if not target:
                            #    len_possible_targets = len(possible_targets[ship[0]])
                            #    if not len_possible_targets:
                            #        continue
                            #    #prioritary_target_key = False
                            #    #prioritary_target_avg_degats = 0
                            #    #for k,p_target in possible_targets_stats[ship_key].items():
                            #    #    if p_target['avg_degats'] > prioritary_target_avg_degats and len(p_target['back_link']):
                            #    #        prioritary_target_key = k
                            #    #        prioritary_target_avg_degats = p_target['avg_degats']
                            #    #        len_possible_targets = len(p_target['back_link'])
                            #
                            #    # on tente d'accélérer en targetant le premier de la pile plutot que random
                            #    target_index = ind_tar % len_possible_targets
                            #    #target_index = random.randint(0,len_possible_targets-1)
                            #
                            #    #if prioritary_target_avg_degats:
                            #    #    targetk = possible_targets_stats[ship_key][prioritary_target_key]['back_link'][target_index]
                            #    #    target = ships[targetk]
                            #    #else: # bizarre mais bon au cas ou
                            #    targetk = possible_targets[ship[0]][target_index]
                            targetk = possible_targets[ship[0]][ list(possible_targets[ship[0]].keys())[0] ]
                            #print('targetpos is',targetk)
                            target = ships[targetk]
                            #print(target)
                            #ind_tar += 1
                            targets += 1
                            target_key = str(target[0])+'|'+str(target[1])+'|'+str(target[2])
                            #selected_targets[pship_key] = targetk
                            chance_to_hit = possible_targets_stats[ship_key][target_key]['chance_to_hit']
                            if chance_to_hit < 1 and random.random() > chance_to_hit:
                                continue
                            degats = possible_targets_stats[ship_key][target_key]['degats']
                            counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['damages'] += degats
                            if degats > target[4]:
                                degats -= target[4]
                                target[4] = 0
                                target[3] -= degats
                            else:
                                target[4] -= degats
                                continue
                            #if target[4] > 0:
                            #    shield = target[4]
                            #    deg = degats
                            #    degats -= shield
                            #    target[4] -= deg
                            #if target[4] > 0:
                            #    counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['damages'] += deg
                            #    continue
                            #target[3] -= degats
                            #counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['damages'] += degats
                            if target[3] <= 0:
                                if not target[2] in counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['killed'].keys():
                                    counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['killed'][target[2]] = 0
                                counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['killed'][target[2]] += 1
                                #print('avant destruction')
                                #print(len(possible_targets_stats[ship_key][prioritary_target_key]['back_link']))
                                #print(len(possible_targets[ship[0]]))
                                #print(len([x for x in ships if x]))
                                #print('targetk '+str(targetk)+' destroyed')

                                ships[targetk] = False
                                #print('killed',targetk)
                                for sh,k in reverse_possible_targets[targetk].items():
                                    #print('del in',sh)
                                    for kk in k:
                                        del possible_targets[sh][kk]
                                #del target
                                #del selected_targets[pship_key]
                                #if prioritary_target_avg_degats:
                                #for k1,t in possible_targets_stats.items():
                                #    for k2,p_target in t.items():
                                #        try:
                                #            #print('possible_targets_stats['+str(k1)+']['+str(k2)+']')
                                #            #print(possible_targets_stats[k1][k2]['back_link'])
                                #            del possible_targets_stats[k1][k2]['back_link'][ possible_targets_stats[k1][k2]['back_link'].index(targetk) ]
                                #            #print('del in possible_targets_stats['+str(k1)+']['+str(k2)+'][\'back_link\']')
                                #        except (KeyError,Exception):
                                #            pass
                                #del possible_targets_stats[ship_key][prioritary_target_key]['back_link'][ possible_targets_stats[ship_key][prioritary_target_key]['back_link'].index(targetk) ]
                                #for k,t in enumerate(possible_targets_stats[ship_key][prioritary_target_key]['back_link']):
                                #    if t == targetk:
                                #        del possible_targets_stats[ship_key][prioritary_target_key]['back_link'][k]
                                #        break
                                #for k1,t1 in possible_targets.items():
                                #    indices = [i for i, x in enumerate(t1) if x == targetk]
                                #    for indice in indices:
                                #        try:
                                #            del possible_targets[k1][ indice ]
                                #        except (KeyError,Exception):
                                #            pass
                                #del possible_targets[ship[0]][ possible_targets[ship[0]].index(targetk) ]
                                #for k,t in enumerate(possible_targets[ship[0]]):
                                #    if t == targetk:
                                #        del possible_targets[ship[0]][k]
                                #        break
                                #else:
                                #    del possible_targets[ship[0]][target_index]
                                #print('apres destruction')
                                #print(len(possible_targets_stats[ship_key][prioritary_target_key]['back_link']))
                                #print(len(possible_targets[ship[0]]))
                                #print(len([x for x in ships if x]))
                                #exit()
                #for ship in ships:
                #    if ship[4] > 0:
                #        ship[4] = ship[4] + (counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['shield']-ship[4])/2 # les shields se rechargent de la moitié de leurs pertes si ils n'ont pas été détruits
                if not targets: # battle finished ?!
                    r -= 1
                    break
                r+=1
            r += 1
            for ship in ships:
                if ship: # ship still alive
                    counter[str(ship[0])+':'+str(ship[1])+':'+str(ship[2])]['after'] += 1
            print(counter)
            print("battle near planet " + str(planetid) + " : resolved in " + str(r) + " rounds")
            shipsDestroyed = 0
            cursor.execute("SELECT sp_create_battle(%s, %s)", [planetid, r])
            res = cursor.fetchone()
            if res:
                BattleId = res[0]
                lastOwner = -1
                print("battle near planet " + str(planetid) + " : insert battles_relations")
                # store players relationships
                for i in friendsArray:
                    if i[0] > i[1]:
                        p1 = i[1]
                        p2 = i[0]
                    else:
                        p1 = i[0]
                        p2 = i[1]
                    cursor.execute("INSERT INTO battles_relations VALUES(%s, %s, %s, %s)", [BattleId, p1, p2, i[2]])
                print("battle near planet " + str(planetid) + " : write battle result")
                # write battle result
                lastFleetId = ""
                lastBattleFleetId = ""
                for k,res in counter.items():
                    expl = k.split(':')
                    sum_killed = 0
                    for y,cc in res['killed'].items():
                        sum_killed += cc
                    won = (targets == 0) and res['after'] > 0
                    cursor.execute("INSERT INTO battles_ships(battleid, owner_id, owner_name, fleet_id, fleet_name, shipid, before, after, killed, won, damages, attacked)" +
                                " VALUES(%s, %s, (SELECT login FROM users WHERE id=%s LIMIT 1), %s" +
                                ", (SELECT name FROM fleets WHERE id=%s LIMIT 1), %s, %s, %s, %s" +
                                 ", %s, %s, (SELECT attackonsight FROM fleets WHERE id=%s LIMIT 1))", [BattleId, expl[0], expl[0], expl[1], expl[1], expl[2], res['before'], res['after'], sum_killed, won, int(res['damages']), expl[1]])
                    # new way of saving battle
                    if expl[1] != lastFleetId:
                        # add a fleet in the battle report
                        cursor.execute("SELECT sp_add_battle_fleet(%s, %s, %s, %s, %s, %s, %s, (SELECT attackonsight FROM fleets WHERE id=%s LIMIT 1), %s)", [BattleId, expl[0], expl[1], res['mod_shield'], res['mod_handling'], res['mod_tracking_speed'], res['mod_damage'], expl[1], won])
                        ree = cursor.fetchone()
                        lastFleetId = expl[1]
                        lastBattleFleetId = ree[0]
                    cursor.execute("INSERT INTO battles_fleets_ships(fleetid, shipid, before, after, killed, damages) VALUES(%s, %s, %s, %s, %s, %s)", [lastBattleFleetId, expl[2], res['before'], res['after'], sum_killed, int(res['damages'])])

                    for DestroyedShipId,quantity in res['killed'].items():
                        cursor.execute("INSERT INTO battles_fleets_ships_kills(fleetid, shipid, destroyed_shipid, count) VALUES(%s, %s, %s, %s)", [lastBattleFleetId, expl[2], DestroyedShipId, quantity])
                        # count number of ships killed
                        if quantity > 0:
                            cursor.execute("INSERT INTO users_ships_kills(userid, shipid, killed) VALUES(%s, %s, %s)", [expl[0], DestroyedShipId, quantity])

                    shipsDestroyed = shipsDestroyed + res['before'] - res['after']
                    # count number of ships the owner lost
                    if res['before'] - res['after'] > 0:
                        cursor.execute("SELECT sp_destroy_ships(%s, %s, %s)", [expl[1], expl[2], res['before'] - res['after']])
                        cursor.execute("INSERT INTO users_ships_kills(userid, shipid, lost) VALUES(%s, %s, %s)", [expl[0], expl[2], res['before'] - res['after']])

                    if lastOwner != expl[0]:
                        if won:
                            battlesubtype = 1
    #                   elseif Rounds = 1 then
    #                       battlesubtype = 2
                        else:
                            battlesubtype = 0

                        cursor.execute("SELECT ownerid FROM reports WHERE ownerid=%s AND type=2 AND subtype=%s AND battleid=%s", [expl[0], battlesubtype, BattleId])
                        ree = cursor.fetchone()
                        if not ree:
                            cursor.execute("INSERT INTO reports(ownerid, type, subtype, battleid, planetid, data) VALUES(%s, 2, %s, %s, %s,%s)", [expl[0], battlesubtype, BattleId, planetid, '{'+data+',battleid:'+str(BattleId)+',ownerid:'+str(expl[0])+'}'])
                        lastOwner = expl[0]
            else:
                BattleId = "#"

            print("battle near planet " + str(planetid) + " : " + str(BattleId))

            cursor.execute("UPDATE nav_planet SET next_battle = null WHERE id=" + str(planetid))

            # set fleeing ships out of battle
    #       oConn.Execute "UPDATE fleets SET engaged=false WHERE engaged AND (action=-1 OR action=1) AND planetid=" & planetid, , 128
            cursor.execute("UPDATE fleets SET engaged=false WHERE engaged AND action <> 0 AND planetid=" + str(planetid))

            if shipsDestroyed > 0:
                cursor.execute("SELECT sp_check_battle(" + str(planetid) + ")")
            else:
                query = "UPDATE fleets SET engaged=false, action=4, action_end_time=now()"
                # reset fleet's idle time (idle_since value) if battle had more than 10 round
                if r > 5:
                    query += ", idle_since=now()"
                query += " WHERE engaged AND action=0 AND planetid=" + str(planetid)
                cursor.execute(query)

            print("battle near planet " + str(planetid) + " : " + str(BattleId) + ": finished", time.time())


        print("Check for battles:done", time.time())

    def handle(self, *args, **options):
        while True:
            with connection.cursor() as cursor:
                print('loop '+str(datetime.datetime.now()))
                for i in range(5000):
                    start = datetime.datetime.now()
                    print('start ' + str(start.microsecond))
                    try:
                        self.ResolveBattles(cursor)
                    except (KeyError, Exception):
                        print(KeyError)
                        print(Exception)
                        cursor.execute('select * from users_chats where userid=2 and chatid=3')
                        row = cursor.fetchone()
                        if not row:
                            cursor.execute('insert into users_chats (userid,chatid,password) values (2,3,\'\')')
                        cursor.execute('insert into chat_lines (chatid,message,login,allianceid,userid) values (3,\'ALERT : sp_battle is down ! Les combats sont stoppés.\',\'Watchdog\',null,2)');
                        exit()
                    end = datetime.datetime.now()
                    print('end ' + str(end.microsecond))
                    print()
                    time.sleep(5)
                    #exit()
