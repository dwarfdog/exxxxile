# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = True` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from nexus.models import *


class AiPlanets(models.Model):
    planetid = models.IntegerField(primary_key=True)
    nextupdate = models.DateTimeField()
    enemysignature = models.IntegerField()
    signaturesent = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'ai_planets'


class AiRoguePlanets(models.Model):
    planetid = models.IntegerField(primary_key=True)
    nextupdate = models.DateTimeField()
    is_production = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'ai_rogue_planets'


class AiRogueTargets(models.Model):
    planetid = models.IntegerField(primary_key=True)
    status = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'ai_rogue_targets'


class AiWatchedPlanets(models.Model):
    planetid = models.IntegerField()
    watched_since = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'ai_watched_planets'


class Alliances(models.Model):
    created = models.DateTimeField()
    name = models.CharField(max_length=32)
    description = models.TextField()
    tag = models.CharField(max_length=4)
    logo_url = models.CharField(max_length=255)
    website_url = models.CharField(max_length=255)
    announce = models.TextField()
    max_members = models.IntegerField()
    tax = models.SmallIntegerField()
    credits = models.BigIntegerField()
    score = models.IntegerField()
    previous_score = models.IntegerField()
    score_combat = models.IntegerField()
    defcon = models.SmallIntegerField()
    chatid = models.ForeignKey('Chat', models.DO_NOTHING, db_column='chatid')
    announce_last_update = models.DateTimeField()
    visible = models.BooleanField()
    last_kick = models.DateTimeField()
    last_dividends = models.DateField()

    class Meta:
        managed = True
        db_table = 'alliances'


class AlliancesInvitations(models.Model):
    allianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid')
    userid = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid', related_name='ai_user_set')
    created = models.DateTimeField()
    recruiterid = models.ForeignKey('Users', models.DO_NOTHING, db_column='recruiterid', blank=True, null=True, related_name='ai_recruter_set')
    declined = models.BooleanField()
    replied = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'alliances_invitations'
        unique_together = (('allianceid', 'userid'),)


class AlliancesNaps(models.Model):
    allianceid1 = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid1', related_name='an_alliance1_set')
    allianceid2 = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid2', related_name='an_alliance2_set')
    created = models.DateTimeField()
    guarantee = models.IntegerField()
    share_locs = models.BooleanField()
    share_radars = models.BooleanField()
    give_diplomacy_percent = models.SmallIntegerField()
    break_on = models.DateTimeField(blank=True, null=True)
    break_interval = models.DurationField()

    class Meta:
        managed = True
        db_table = 'alliances_naps'
        unique_together = (('allianceid1', 'allianceid2'),)


class AlliancesNapsOffers(models.Model):
    allianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid', related_name='ano_alliance_set')
    targetallianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='targetallianceid', related_name='ano_target_alliance_set')
    created = models.DateTimeField()
    recruiterid = models.ForeignKey('Users', models.DO_NOTHING, db_column='recruiterid', blank=True, null=True)
    declined = models.BooleanField()
    replied = models.DateTimeField(blank=True, null=True)
    guarantee = models.IntegerField()
    guarantee_asked = models.IntegerField()
    break_interval = models.DurationField()

    class Meta:
        managed = True
        db_table = 'alliances_naps_offers'
        unique_together = (('allianceid', 'targetallianceid'),)


class AlliancesRanks(models.Model):
    allianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid')
    rankid = models.SmallIntegerField()
    label = models.CharField(max_length=32)
    leader = models.BooleanField()
    can_invite_player = models.BooleanField()
    can_kick_player = models.BooleanField()
    can_create_nap = models.BooleanField()
    can_break_nap = models.BooleanField()
    can_ask_money = models.BooleanField()
    can_see_reports = models.BooleanField()
    can_accept_money_requests = models.BooleanField()
    can_change_tax_rate = models.BooleanField()
    can_mail_alliance = models.BooleanField()
    is_default = models.BooleanField()
    members_displayed = models.BooleanField()
    can_manage_description = models.BooleanField()
    can_manage_announce = models.BooleanField()
    enabled = models.BooleanField()
    can_see_members_info = models.BooleanField()
    tax = models.SmallIntegerField()
    can_order_other_fleets = models.BooleanField()
    can_use_alliance_radars = models.BooleanField()

    # A unique constraint could not be introspected.
    class Meta:
        managed = True
        db_table = 'alliances_ranks'
        unique_together = (('allianceid', 'rankid'),)


class AlliancesReports(models.Model):
    id = models.BigAutoField(primary_key=True)
    ownerallianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='ownerallianceid', related_name='ar_owner_alliance_set')
    ownerid = models.ForeignKey('Users', models.DO_NOTHING, db_column='ownerid', related_name='ar_owner_set')
    type = models.SmallIntegerField()
    subtype = models.SmallIntegerField()
    datetime = models.DateTimeField()
    read_date = models.DateTimeField(blank=True, null=True)
    battleid = models.IntegerField(blank=True, null=True)
    fleetid = models.ForeignKey('Fleets', models.DO_NOTHING, db_column='fleetid', blank=True, null=True)
    fleet_name = models.CharField(max_length=18, blank=True, null=True)
    planetid = models.IntegerField(blank=True, null=True)
    researchid = models.ForeignKey('DbResearch', models.DO_NOTHING, db_column='researchid', blank=True, null=True)
    ore = models.IntegerField()
    hydrocarbon = models.IntegerField()
    scientists = models.IntegerField()
    soldiers = models.IntegerField()
    workers = models.IntegerField()
    credits = models.IntegerField()
    allianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid', blank=True, null=True, related_name='ar_alliance_set')
    userid = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid', blank=True, null=True, related_name='ar_user_set')
    invasionid = models.ForeignKey('Invasions', models.DO_NOTHING, db_column='invasionid', blank=True, null=True)
    spyid = models.ForeignKey('Spy', models.DO_NOTHING, db_column='spyid', blank=True, null=True)
    commanderid = models.ForeignKey('Commanders', models.DO_NOTHING, db_column='commanderid', blank=True, null=True)
    buildingid = models.ForeignKey('DbBuildings', models.DO_NOTHING, db_column='buildingid', blank=True, null=True)
    description = models.CharField(max_length=128, blank=True, null=True)
    invited_username = models.CharField(max_length=20, blank=True, null=True)
    planet_name = models.TextField(blank=True, null=True)
    planet_relation = models.SmallIntegerField(blank=True, null=True)
    planet_ownername = models.TextField(blank=True, null=True)
    data = models.TextField()

    class Meta:
        managed = True
        db_table = 'alliances_reports'


class AlliancesTributes(models.Model):
    allianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid', related_name='at_alliance_set')
    target_allianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='target_allianceid', related_name='at_target_alliance_set')
    credits = models.IntegerField()
    next_transfer = models.DateTimeField()
    created = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'alliances_tributes'
        unique_together = (('allianceid', 'target_allianceid'),)


class AlliancesWalletJournal(models.Model):
    datetime = models.DateTimeField()
    allianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid')
    userid = models.IntegerField(blank=True, null=True)
    credits = models.IntegerField()
    description = models.CharField(max_length=256, blank=True, null=True)
    source = models.CharField(max_length=38, blank=True, null=True)
    type = models.SmallIntegerField()
    destination = models.CharField(max_length=38, blank=True, null=True)
    groupid = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'alliances_wallet_journal'


class AlliancesWalletRequests(models.Model):
    allianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid')
    userid = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid')
    credits = models.IntegerField()
    description = models.CharField(max_length=128)
    datetime = models.DateTimeField()
    result = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'alliances_wallet_requests'


class AlliancesWars(models.Model):
    allianceid1 = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid1', related_name='aw_alliance1_set')
    allianceid2 = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid2', related_name='aw_alliance2_set')
    cease_fire_requested = models.IntegerField(blank=True, null=True)
    cease_fire_expire = models.DateTimeField(blank=True, null=True)
    created = models.DateTimeField()
    next_bill = models.DateTimeField(blank=True, null=True)
    can_fight = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'alliances_wars'
        unique_together = (('allianceid1', 'allianceid2'),)


class Battles(models.Model):
    time = models.DateTimeField()
    planetid = models.IntegerField()
    rounds = models.SmallIntegerField()
    key = models.CharField(unique=True, max_length=8)

    class Meta:
        managed = True
        db_table = 'battles'


class BattlesBuildings(models.Model):
    battleid = models.IntegerField()
    owner_id = models.IntegerField()
    owner_name = models.CharField(max_length=16)
    planet_name = models.CharField(max_length=18)
    buildingid = models.IntegerField()
    before = models.IntegerField()
    after = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'battles_buildings'


class BattlesFleets(models.Model):
    id = models.BigAutoField(primary_key=True)
    battleid = models.ForeignKey(Battles, models.DO_NOTHING, db_column='battleid')
    owner_id = models.IntegerField(blank=True, null=True)
    owner_name = models.CharField(max_length=16)
    fleet_id = models.IntegerField(blank=True, null=True)
    fleet_name = models.CharField(max_length=18)
    attackonsight = models.BooleanField()
    won = models.BooleanField()
    mod_shield = models.SmallIntegerField()
    mod_handling = models.SmallIntegerField()
    mod_tracking_speed = models.SmallIntegerField()
    mod_damage = models.SmallIntegerField()
    alliancetag = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'battles_fleets'


class BattlesFleetsShips(models.Model):
    fleetid = models.ForeignKey(BattlesFleets, models.DO_NOTHING, db_column='fleetid')
    shipid = models.ForeignKey('DbShips', models.DO_NOTHING, db_column='shipid')
    before = models.IntegerField()
    after = models.IntegerField()
    killed = models.IntegerField()
    damages = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'battles_fleets_ships'


class BattlesFleetsShipsKills(models.Model):
    fleetid = models.ForeignKey(BattlesFleets, models.DO_NOTHING, db_column='fleetid')
    shipid = models.ForeignKey('DbShips', models.DO_NOTHING, db_column='shipid',related_name='bfsk_ship_set')
    destroyed_shipid = models.ForeignKey('DbShips', models.DO_NOTHING, db_column='destroyed_shipid',related_name='bfsk_destroyed_ship_set')
    count = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'battles_fleets_ships_kills'


class BattlesRelations(models.Model):
    battleid = models.ForeignKey(Battles, models.DO_NOTHING, db_column='battleid')
    user1 = models.IntegerField()
    user2 = models.IntegerField()
    relation = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'battles_relations'
        unique_together = (('battleid', 'user1', 'user2'),)


class BattlesShips(models.Model):
    battleid = models.ForeignKey(Battles, models.DO_NOTHING, db_column='battleid')
    owner_id = models.IntegerField()
    owner_name = models.CharField(max_length=16)
    fleet_name = models.CharField(max_length=18)
    shipid = models.ForeignKey('DbShips', models.DO_NOTHING, db_column='shipid')
    before = models.IntegerField()
    after = models.IntegerField()
    killed = models.IntegerField()
    won = models.BooleanField()
    damages = models.IntegerField()
    fleet_id = models.IntegerField()
    attacked = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'battles_ships'


class Chat(models.Model):
    name = models.CharField(max_length=24, blank=True, null=True)
    password = models.CharField(max_length=16)
    topic = models.CharField(max_length=128)
    public = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'chat'


class ChatChannels(models.Model):
    name = models.CharField(max_length=12, blank=True, null=True)
    password = models.CharField(max_length=16)
    topic = models.CharField(max_length=128)
    public = models.BooleanField()
    allianceid = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'chat_channels'


class ChatLines(models.Model):
    id = models.BigAutoField(primary_key=True)
    chatid = models.ForeignKey(Chat, models.DO_NOTHING, db_column='chatid')
    datetime = models.DateTimeField()
    message = models.CharField(max_length=512)
    action = models.SmallIntegerField(blank=True, null=True)
    login = models.CharField(max_length=16)
    allianceid = models.IntegerField(blank=True, null=True)
    userid = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'chat_lines'


class ChatOnlineusers(models.Model):
    chatid = models.ForeignKey(Chat, models.DO_NOTHING, db_column='chatid')
    userid = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid')
    lastactivity = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'chat_onlineusers'
        unique_together = (('chatid', 'userid'),)


class ChatUsers(models.Model):
    channelid = models.ForeignKey(ChatChannels, models.DO_NOTHING, db_column='channelid')
    userid = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid')
    joined = models.DateTimeField()
    lastactivity = models.DateTimeField()
    rights = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'chat_users'
        unique_together = (('channelid', 'userid'),)


class Commanders(models.Model):
    ownerid = models.ForeignKey('Users', models.DO_NOTHING, db_column='ownerid')
    recruited = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=32)
    points = models.SmallIntegerField()
    mod_production_ore = models.FloatField()
    mod_production_hydrocarbon = models.FloatField()
    mod_production_energy = models.FloatField()
    mod_production_workers = models.FloatField()
    mod_fleet_damage = models.FloatField()
    mod_fleet_speed = models.FloatField()
    mod_fleet_shield = models.FloatField()
    mod_fleet_handling = models.FloatField()
    mod_fleet_tracking_speed = models.FloatField()
    mod_fleet_signature = models.FloatField()
    mod_construction_speed_buildings = models.FloatField()
    mod_construction_speed_ships = models.FloatField()
    mod_recycling = models.FloatField()
    can_be_fired = models.BooleanField()
    salary = models.IntegerField()
    delete_on_reset = models.BooleanField()
    added = models.DateTimeField()
    salary_increases = models.SmallIntegerField()
    salary_last_increase = models.DateTimeField()
    mod_research_effectiveness = models.FloatField()
    mod_fleet_hull = models.IntegerField()
    last_training = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'commanders'


class Fleets(models.Model):
    ownerid = models.ForeignKey('Users', models.DO_NOTHING, db_column='ownerid')
    uid = models.IntegerField()
    name = models.CharField(max_length=18)
    commanderid = models.OneToOneField(Commanders, models.DO_NOTHING, db_column='commanderid', blank=True, null=True)
    planetid = models.ForeignKey('NavPlanet', models.DO_NOTHING, db_column='planetid', blank=True, null=True,related_name='fleet_planet_set')
    dest_planetid = models.ForeignKey('NavPlanet', models.DO_NOTHING, db_column='dest_planetid', blank=True, null=True,related_name='fleet_dest_planet_set')
    action = models.SmallIntegerField()
    action_start_time = models.DateTimeField(blank=True, null=True)
    action_end_time = models.DateTimeField(blank=True, null=True)
    attackonsight = models.BooleanField()
    engaged = models.BooleanField()
    cargo_capacity = models.IntegerField()
    cargo_ore = models.IntegerField()
    cargo_hydrocarbon = models.IntegerField()
    cargo_workers = models.IntegerField()
    cargo_scientists = models.IntegerField()
    cargo_soldiers = models.IntegerField()
    size = models.IntegerField()
    speed = models.IntegerField()
    signature = models.IntegerField()
    military_signature = models.IntegerField()
    real_signature = models.IntegerField()
    recycler_output = models.IntegerField()
    idle_since = models.DateTimeField(blank=True, null=True)
    droppods = models.IntegerField()
    long_distance_capacity = models.IntegerField()
    firepower = models.BigIntegerField()
    score = models.BigIntegerField()
    next_waypointid = models.ForeignKey('RoutesWaypoints', models.DO_NOTHING, db_column='next_waypointid', blank=True, null=True)
    mod_speed = models.SmallIntegerField()
    mod_shield = models.SmallIntegerField()
    mod_handling = models.SmallIntegerField()
    mod_tracking_speed = models.SmallIntegerField()
    mod_damage = models.SmallIntegerField()
    mod_recycling = models.FloatField()
    mod_signature = models.FloatField()
    upkeep = models.IntegerField()
    recycler_percent = models.FloatField()
    categoryid = models.SmallIntegerField()
    required_vortex_strength = models.IntegerField()
    leadership = models.BigIntegerField()
    shared = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'fleets'


class FleetsItems(models.Model):
    fleetid = models.IntegerField(primary_key=True)
    resourceid = models.IntegerField()
    quantity = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'fleets_items'
        unique_together = (('fleetid', 'resourceid'),)


class FleetsShips(models.Model):
    fleetid = models.ForeignKey(Fleets, models.DO_NOTHING, db_column='fleetid')
    shipid = models.IntegerField()
    quantity = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'fleets_ships'
        unique_together = (('fleetid', 'shipid'),)


class Invasions(models.Model):
    time = models.DateTimeField()
    planet_id = models.IntegerField()
    planet_name = models.CharField(max_length=32)
    attacker_name = models.CharField(max_length=16)
    defender_name = models.CharField(max_length=16)
    attacker_succeeded = models.BooleanField()
    soldiers_total = models.IntegerField()
    soldiers_lost = models.IntegerField()
    def_scientists_total = models.IntegerField()
    def_scientists_lost = models.IntegerField()
    def_soldiers_total = models.IntegerField()
    def_soldiers_lost = models.IntegerField()
    def_workers_total = models.IntegerField()
    def_workers_lost = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'invasions'


class LogAdminActions(models.Model):
    datetime = models.DateTimeField()
    adminuserid = models.IntegerField()
    userid = models.IntegerField()
    action = models.SmallIntegerField()
    reason = models.CharField(max_length=128, blank=True, null=True)
    reason_public = models.CharField(max_length=128, blank=True, null=True)
    admin_notes = models.TextField()

    class Meta:
        managed = True
        db_table = 'log_admin_actions'


class LogHttpErrors(models.Model):
    datetime = models.DateTimeField()
    user = models.CharField(max_length=32, blank=True, null=True)
    http_error_code = models.TextField(blank=True, null=True)
    err_asp_code = models.TextField(blank=True, null=True)
    err_number = models.TextField(blank=True, null=True)
    err_source = models.TextField(blank=True, null=True)
    err_category = models.TextField(blank=True, null=True)
    err_file = models.TextField(blank=True, null=True)
    err_line = models.TextField(blank=True, null=True)
    err_column = models.TextField(blank=True, null=True)
    err_description = models.TextField(blank=True, null=True)
    err_aspdescription = models.TextField(blank=True, null=True)
    details = models.CharField(max_length=128)
    url = models.CharField(max_length=128)

    class Meta:
        managed = True
        db_table = 'log_http_errors'


class LogJobs(models.Model):
    task = models.CharField(primary_key=True, max_length=128, unique=True)
    lastupdate = models.DateTimeField()
    state = models.CharField(max_length=128)
    processid = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'log_jobs'


class LogMultiAccountWarnings(models.Model):
    ucid = models.ForeignKey('UsersConnections', models.DO_NOTHING, db_column='ucid', related_name='lmaw_userco1_set')
    withid = models.ForeignKey('UsersConnections', models.DO_NOTHING, db_column='withid', related_name='lmaw_userco2_set')

    class Meta:
        managed = True
        db_table = 'log_multi_account_warnings'


class LogMultiSimultaneousWarnings(models.Model):
    datetime = models.DateTimeField()
    userid1 = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid1', related_name='lmsw_user1_set')
    userid2 = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid2', related_name='lmsw_user2_set')

    class Meta:
        managed = True
        db_table = 'log_multi_simultaneous_warnings'
        unique_together = (('datetime', 'userid1', 'userid2'),)


class LogNotices(models.Model):
    datetime = models.DateTimeField()
    username = models.CharField(max_length=32, blank=True, null=True)
    title = models.CharField(max_length=128)
    details = models.CharField(max_length=128)
    url = models.CharField(max_length=128)
    repeats = models.IntegerField()
    level = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'log_notices'


class LogPages(models.Model):
    id = models.BigAutoField(primary_key=True)
    datetime = models.DateTimeField()
    userid = models.IntegerField()
    webpage = models.CharField(max_length=256)
    elapsed = models.FloatField()

    class Meta:
        managed = True
        db_table = 'log_pages'


class LogReferers(models.Model):
    referer = models.TextField()
    page = models.TextField(blank=True, null=True)
    pages = models.TextField()  # This field type is a guess.

    class Meta:
        managed = True
        db_table = 'log_referers'


class LogReferersUsers(models.Model):
    refererid = models.ForeignKey(LogReferers, models.DO_NOTHING, db_column='refererid')
    datetime = models.DateTimeField()
    userid = models.IntegerField()
    page = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'log_referers_users'


class LogSysErrors(models.Model):
    procedure = models.TextField()
    added = models.DateTimeField()
    error = models.TextField()

    class Meta:
        managed = True
        db_table = 'log_sys_errors'


class MarketHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    datetime = models.DateTimeField()
    ore_sold = models.IntegerField(blank=True, null=True)
    hydrocarbon_sold = models.IntegerField()
    credits = models.IntegerField()
    username = models.CharField(max_length=16, blank=True, null=True)
    workers_sold = models.IntegerField()
    scientists_sold = models.IntegerField()
    soldiers_sold = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'market_history'


class MarketPurchases(models.Model):
    planetid = models.ForeignKey('NavPlanet', models.DO_NOTHING, db_column='planetid')
    ore = models.IntegerField()
    hydrocarbon = models.IntegerField()
    credits = models.IntegerField()
    delivery_time = models.DateTimeField()
    ore_price = models.SmallIntegerField()
    hydrocarbon_price = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'market_purchases'


class MarketSales(models.Model):
    planetid = models.ForeignKey('NavPlanet', models.DO_NOTHING, db_column='planetid')
    ore = models.IntegerField()
    hydrocarbon = models.IntegerField()
    credits = models.IntegerField()
    sale_time = models.DateTimeField()
    ore_price = models.SmallIntegerField()
    hydrocarbon_price = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'market_sales'


class Messages(models.Model):
    datetime = models.DateTimeField()
    read_date = models.DateTimeField(blank=True, null=True)
    ownerid = models.ForeignKey('Users', models.DO_NOTHING, db_column='ownerid', blank=True, null=True, related_name='message_owner_set')
    owner = models.CharField(max_length=20)
    senderid = models.ForeignKey('Users', models.DO_NOTHING, db_column='senderid', blank=True, null=True, related_name='message_sender_set')
    sender = models.CharField(max_length=20)
    subject = models.CharField(max_length=80)
    body = models.TextField()
    credits = models.IntegerField()
    deleted = models.BooleanField()
    bbcode = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'messages'


class MessagesAddresseeHistory(models.Model):
    ownerid = models.ForeignKey('Users', models.DO_NOTHING, db_column='ownerid', related_name='mah_owner_set')
    addresseeid = models.ForeignKey('Users', models.DO_NOTHING, db_column='addresseeid', related_name='mah_addressee_set')
    created = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'messages_addressee_history'


class MessagesIgnoreList(models.Model):
    userid = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid', related_name='mil_user_set')
    ignored_userid = models.ForeignKey('Users', models.DO_NOTHING, db_column='ignored_userid', related_name='mil_ignored_user_set')
    added = models.DateTimeField()
    blocked = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'messages_ignore_list'
        unique_together = (('userid', 'ignored_userid'),)


class MessagesMoneyTransfers(models.Model):
    datetime = models.DateTimeField()
    senderid = models.IntegerField(blank=True, null=True)
    sendername = models.CharField(max_length=20)
    toid = models.IntegerField(blank=True, null=True)
    toname = models.CharField(max_length=16, blank=True, null=True)
    credits = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'messages_money_transfers'


class NavGalaxies(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    colonies = models.IntegerField()
    visible = models.BooleanField()
    allow_new_players = models.BooleanField()
    created = models.DateTimeField()
    reserved_for_gameover = models.BooleanField()
    planets = models.IntegerField()
    protected_until = models.DateTimeField(blank=True, null=True)
    has_merchants = models.BooleanField()
    traded_ore = models.BigIntegerField()
    traded_hydrocarbon = models.BigIntegerField()
    price_ore = models.FloatField()
    price_hydrocarbon = models.FloatField()

    class Meta:
        managed = True
        db_table = 'nav_galaxies'


class NavPlanet(models.Model):
    ownerid = models.ForeignKey('Users', models.DO_NOTHING, db_column='ownerid', blank=True, null=True)
    commanderid = models.ForeignKey(Commanders, models.DO_NOTHING, db_column='commanderid', blank=True, null=True)
    name = models.CharField(max_length=32)
    galaxy = models.ForeignKey(NavGalaxies, models.DO_NOTHING, db_column='galaxy')
    sector = models.SmallIntegerField()
    planet = models.SmallIntegerField()
    warp_to = models.IntegerField(blank=True, null=True)
    planet_floor = models.SmallIntegerField()
    planet_space = models.SmallIntegerField()
    planet_pct_ore = models.SmallIntegerField()
    planet_pct_hydrocarbon = models.SmallIntegerField()
    pct_ore = models.SmallIntegerField()
    pct_hydrocarbon = models.SmallIntegerField()
    floor = models.SmallIntegerField()
    space = models.SmallIntegerField()
    floor_occupied = models.SmallIntegerField()
    space_occupied = models.SmallIntegerField()
    score = models.BigIntegerField()
    ore = models.IntegerField()
    ore_capacity = models.IntegerField()
    ore_production = models.IntegerField()
    ore_production_raw = models.IntegerField()
    hydrocarbon = models.IntegerField()
    hydrocarbon_capacity = models.IntegerField()
    hydrocarbon_production = models.IntegerField()
    hydrocarbon_production_raw = models.IntegerField()
    workers = models.IntegerField()
    workers_capacity = models.IntegerField()
    workers_busy = models.IntegerField()
    scientists = models.IntegerField()
    scientists_capacity = models.IntegerField()
    soldiers = models.IntegerField()
    soldiers_capacity = models.IntegerField()
    energy_consumption = models.IntegerField()
    energy_production = models.IntegerField()
    production_lastupdate = models.DateTimeField(blank=True, null=True)
    production_frozen = models.BooleanField()
    radar_strength = models.SmallIntegerField()
    radar_jamming = models.SmallIntegerField()
    spawn_ore = models.IntegerField()
    spawn_hydrocarbon = models.IntegerField()
    orbit_ore = models.IntegerField()
    orbit_hydrocarbon = models.IntegerField()
    mod_production_ore = models.SmallIntegerField()
    mod_production_hydrocarbon = models.SmallIntegerField()
    mod_production_energy = models.SmallIntegerField()
    mod_production_workers = models.SmallIntegerField()
    mod_construction_speed_buildings = models.SmallIntegerField()
    mod_construction_speed_ships = models.SmallIntegerField()
    training_scientists = models.IntegerField()
    training_soldiers = models.IntegerField()
    mood = models.SmallIntegerField()
    buildings_dilapidation = models.IntegerField()
    previous_buildings_dilapidation = models.IntegerField()
    workers_for_maintenance = models.IntegerField()
    soldiers_for_security = models.IntegerField()
    next_battle = models.DateTimeField(blank=True, null=True)
    colonization_datetime = models.DateTimeField(blank=True, null=True)
    last_catastrophe = models.DateTimeField()
    next_training_datetime = models.DateTimeField()
    recruit_workers = models.BooleanField()
    sandworm_activity = models.SmallIntegerField()
    seismic_activity = models.SmallIntegerField()
    production_percent = models.FloatField()
    blocus_strength = models.SmallIntegerField(blank=True, null=True)
    credits_production = models.IntegerField()
    credits_random_production = models.IntegerField()
    mod_research_effectiveness = models.SmallIntegerField()
    energy_receive_antennas = models.SmallIntegerField()
    energy_send_antennas = models.SmallIntegerField()
    energy_receive_links = models.SmallIntegerField()
    energy_send_links = models.SmallIntegerField()
    energy = models.IntegerField()
    energy_capacity = models.IntegerField()
    next_planet_update = models.DateTimeField(blank=True, null=True)
    upkeep = models.IntegerField()
    shipyard_next_continue = models.DateTimeField(blank=True, null=True)
    shipyard_suspended = models.BooleanField()
    market_buy_ore_price = models.SmallIntegerField(blank=True, null=True)
    market_buy_hydrocarbon_price = models.SmallIntegerField(blank=True, null=True)
    credits_total = models.IntegerField()
    credits_next_update = models.DateTimeField()
    credits_updates = models.SmallIntegerField()
    planet_vortex_strength = models.IntegerField()
    vortex_strength = models.IntegerField()
    production_prestige = models.IntegerField()
    planet_stock_ore = models.IntegerField()
    planet_stock_hydrocarbon = models.IntegerField()
    planet_need_ore = models.IntegerField()
    planet_need_hydrocarbon = models.IntegerField()
    buy_ore = models.IntegerField()
    buy_hydrocarbon = models.IntegerField()
    invasion_defense = models.IntegerField()
    min_security_level = models.IntegerField()
    parked_ships_capacity = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'nav_planet'
        unique_together = (('galaxy', 'sector', 'planet'),)


class PlanetBuildings(models.Model):
    planetid = models.ForeignKey(NavPlanet, models.DO_NOTHING, db_column='planetid')
    buildingid = models.ForeignKey('DbBuildings', models.DO_NOTHING, db_column='buildingid')
    quantity = models.SmallIntegerField()
    destroy_datetime = models.DateTimeField(blank=True, null=True)
    disabled = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'planet_buildings'
        unique_together = (('planetid', 'buildingid'),)


class PlanetBuildingsPending(models.Model):
    planetid = models.ForeignKey(NavPlanet, models.DO_NOTHING, db_column='planetid')
    buildingid = models.ForeignKey('DbBuildings', models.DO_NOTHING, db_column='buildingid')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    loop = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'planet_buildings_pending'
        unique_together = (('planetid', 'buildingid'),)


class PlanetEnergyTransfer(models.Model):
    planetid = models.IntegerField(primary_key=True)
    target_planetid = models.IntegerField()
    energy = models.IntegerField()
    effective_energy = models.IntegerField()
    enabled = models.BooleanField()
    activation_datetime = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'planet_energy_transfer'
        unique_together = (('planetid', 'target_planetid'),)


class PlanetOwners(models.Model):
    datetime = models.DateTimeField()
    planetid = models.IntegerField()
    ownerid = models.IntegerField(blank=True, null=True)
    newownerid = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'planet_owners'


class PlanetShips(models.Model):
    planetid = models.ForeignKey(NavPlanet, models.DO_NOTHING, db_column='planetid')
    shipid = models.ForeignKey('DbShips', models.DO_NOTHING, db_column='shipid')
    quantity = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'planet_ships'
        unique_together = (('planetid', 'shipid'),)


class PlanetShipsPending(models.Model):
    planetid = models.ForeignKey(NavPlanet, models.DO_NOTHING, db_column='planetid')
    shipid = models.ForeignKey('DbShips', models.DO_NOTHING, db_column='shipid')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    quantity = models.IntegerField()
    recycle = models.BooleanField()
    take_resources = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'planet_ships_pending'


class PlanetTrainingPending(models.Model):
    planetid = models.ForeignKey(NavPlanet, models.DO_NOTHING, db_column='planetid')
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    scientists = models.IntegerField()
    soldiers = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'planet_training_pending'


class Reports(models.Model):
    ownerid = models.ForeignKey('Users', models.DO_NOTHING, db_column='ownerid', related_name='report_owner_set')
    type = models.SmallIntegerField()
    subtype = models.SmallIntegerField()
    datetime = models.DateTimeField()
    read_date = models.DateTimeField(blank=True, null=True)
    battleid = models.IntegerField(blank=True, null=True)
    fleetid = models.ForeignKey(Fleets, models.DO_NOTHING, db_column='fleetid', blank=True, null=True)
    fleet_name = models.CharField(max_length=18, blank=True, null=True)
    planetid = models.IntegerField(blank=True, null=True)
    researchid = models.ForeignKey('DbResearch', models.DO_NOTHING, db_column='researchid', blank=True, null=True)
    ore = models.IntegerField()
    hydrocarbon = models.IntegerField()
    scientists = models.IntegerField()
    soldiers = models.IntegerField()
    workers = models.IntegerField()
    credits = models.IntegerField()
    allianceid = models.ForeignKey(Alliances, models.DO_NOTHING, db_column='allianceid', blank=True, null=True)
    userid = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid', blank=True, null=True, related_name='report_user_set')
    invasionid = models.ForeignKey(Invasions, models.DO_NOTHING, db_column='invasionid', blank=True, null=True)
    spyid = models.ForeignKey('Spy', models.DO_NOTHING, db_column='spyid', blank=True, null=True)
    commanderid = models.ForeignKey(Commanders, models.DO_NOTHING, db_column='commanderid', blank=True, null=True)
    buildingid = models.ForeignKey('DbBuildings', models.DO_NOTHING, db_column='buildingid', blank=True, null=True)
    description = models.CharField(max_length=128, blank=True, null=True)
    upkeep_planets = models.IntegerField(blank=True, null=True)
    upkeep_scientists = models.IntegerField(blank=True, null=True)
    upkeep_ships = models.IntegerField(blank=True, null=True)
    upkeep_ships_in_position = models.IntegerField(blank=True, null=True)
    upkeep_ships_parked = models.IntegerField(blank=True, null=True)
    upkeep_soldiers = models.IntegerField(blank=True, null=True)
    upkeep_commanders = models.IntegerField(blank=True, null=True)
    planet_name = models.TextField(blank=True, null=True)
    planet_relation = models.SmallIntegerField(blank=True, null=True)
    planet_ownername = models.TextField(blank=True, null=True)
    data = models.TextField()

    class Meta:
        managed = True
        db_table = 'reports'


class Researches(models.Model):
    userid = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid')
    researchid = models.ForeignKey('DbResearch', models.DO_NOTHING, db_column='researchid')
    level = models.SmallIntegerField()
    expires = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'researches'
        unique_together = (('userid', 'researchid'),)


class ResearchesPending(models.Model):
    userid = models.OneToOneField('Users', models.DO_NOTHING, db_column='userid')
    researchid = models.ForeignKey('DbResearch', models.DO_NOTHING, db_column='researchid')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    looping = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'researches_pending'


class Routes(models.Model):
    ownerid = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=32)
    repeat = models.BooleanField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    last_used = models.DateTimeField()

    # A unique constraint could not be introspected.
    class Meta:
        managed = True
        db_table = 'routes'


class RoutesWaypoints(models.Model):
    id = models.BigAutoField(primary_key=True)
    next_waypointid = models.BigIntegerField(blank=True, null=True)
    routeid = models.ForeignKey(Routes, models.DO_NOTHING, db_column='routeid')
    action = models.SmallIntegerField()
    waittime = models.SmallIntegerField()
    planetid = models.IntegerField(blank=True, null=True)
    ore = models.IntegerField(blank=True, null=True)
    hydrocarbon = models.IntegerField(blank=True, null=True)
    scientists = models.IntegerField(blank=True, null=True)
    soldiers = models.IntegerField(blank=True, null=True)
    workers = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'routes_waypoints'


class Sessions(models.Model):
    userid = models.OneToOneField('Users', models.DO_NOTHING, db_column='userid')
    lastactivity = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'sessions'


class SessionsNotifications(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.IntegerField()
    type = models.CharField(max_length=16)
    data = models.TextField()
    added = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'sessions_notifications'


class Spy(models.Model):
    userid = models.ForeignKey('Users', models.DO_NOTHING, db_column='userid')
    date = models.DateTimeField()
    credits = models.IntegerField(blank=True, null=True)
    type = models.SmallIntegerField()
    key = models.CharField(unique=True, max_length=8, blank=True, null=True)
    spotted = models.BooleanField()
    level = models.SmallIntegerField()
    target_id = models.IntegerField(blank=True, null=True)
    target_name = models.CharField(max_length=16, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'spy'


class SpyBuilding(models.Model):
    spy = models.ForeignKey(Spy, models.DO_NOTHING)
    planet_id = models.IntegerField()
    building_id = models.IntegerField()
    endtime = models.DateTimeField(blank=True, null=True)
    quantity = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'spy_building'
        unique_together = (('spy', 'planet_id', 'building_id'),)


class SpyFleet(models.Model):
    spy = models.ForeignKey(Spy, models.DO_NOTHING)
    fleet_name = models.CharField(max_length=18)
    galaxy = models.SmallIntegerField()
    sector = models.SmallIntegerField()
    planet = models.SmallIntegerField()
    size = models.IntegerField(blank=True, null=True)
    signature = models.IntegerField(blank=True, null=True)
    dest_galaxy = models.SmallIntegerField(blank=True, null=True)
    dest_sector = models.SmallIntegerField(blank=True, null=True)
    dest_planet = models.SmallIntegerField(blank=True, null=True)
    fleet_id = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'spy_fleet'
        unique_together = (('spy', 'fleet_id'),)


class SpyPlanet(models.Model):
    spy = models.ForeignKey(Spy, models.DO_NOTHING)
    planet_id = models.IntegerField()
    planet_name = models.CharField(max_length=32, blank=True, null=True)
    floor = models.SmallIntegerField()
    space = models.SmallIntegerField()
    ground = models.IntegerField(blank=True, null=True)
    ore = models.IntegerField(blank=True, null=True)
    hydrocarbon = models.IntegerField(blank=True, null=True)
    workers = models.IntegerField(blank=True, null=True)
    ore_capacity = models.IntegerField(blank=True, null=True)
    hydrocarbon_capacity = models.IntegerField(blank=True, null=True)
    workers_capacity = models.IntegerField(blank=True, null=True)
    ore_production = models.IntegerField(blank=True, null=True)
    hydrocarbon_production = models.IntegerField(blank=True, null=True)
    scientists = models.IntegerField(blank=True, null=True)
    scientists_capacity = models.IntegerField(blank=True, null=True)
    soldiers = models.IntegerField(blank=True, null=True)
    soldiers_capacity = models.IntegerField(blank=True, null=True)
    radar_strength = models.SmallIntegerField(blank=True, null=True)
    radar_jamming = models.SmallIntegerField(blank=True, null=True)
    orbit_ore = models.IntegerField(blank=True, null=True)
    orbit_hydrocarbon = models.IntegerField(blank=True, null=True)
    floor_occupied = models.SmallIntegerField(blank=True, null=True)
    space_occupied = models.SmallIntegerField(blank=True, null=True)
    owner_name = models.CharField(max_length=16, blank=True, null=True)
    energy_consumption = models.IntegerField(blank=True, null=True)
    energy_production = models.IntegerField(blank=True, null=True)
    pct_ore = models.SmallIntegerField(blank=True, null=True)
    pct_hydrocarbon = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'spy_planet'
        unique_together = (('spy', 'planet_id'),)


class SpyResearch(models.Model):
    spy = models.ForeignKey(Spy, models.DO_NOTHING)
    research_id = models.IntegerField()
    research_level = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'spy_research'
        unique_together = (('spy', 'research_id'),)


class SysDailyUpdates(models.Model):
    procedure = models.CharField(primary_key=True, max_length=64, unique=True)
    enabled = models.BooleanField()
    last_runtime = models.DateTimeField()
    run_every = models.DurationField()
    last_result = models.TextField(blank=True, null=True)
    last_executiontimes = models.TextField()  # This field type is a guess.

    class Meta:
        managed = True
        db_table = 'sys_daily_updates'


class SysEvents(models.Model):
    procedure = models.CharField(primary_key=True, max_length=64, unique=True)
    enabled = models.BooleanField()
    last_runtime = models.DateTimeField()
    run_every = models.DurationField()
    last_result = models.TextField(blank=True, null=True)
    last_executiontimes = models.TextField()  # This field type is a guess.

    class Meta:
        managed = True
        db_table = 'sys_events'


class SysProcesses(models.Model):
    procedure = models.CharField(primary_key=True, max_length=64, unique=True)
    enabled = models.BooleanField()
    last_runtime = models.DateTimeField()
    run_every = models.DurationField()
    last_result = models.TextField(blank=True, null=True)
    last_executiontimes = models.TextField()  # This field type is a guess.

    class Meta:
        managed = True
        db_table = 'sys_processes'


class Users(models.Model):
    id = models.IntegerField(primary_key=True)
    privilege = models.IntegerField()
    login = models.CharField(max_length=16, blank=True, null=True)
    password = models.CharField(max_length=32, blank=True, null=True)
    lastlogin = models.DateTimeField(blank=True, null=True)
    regdate = models.DateTimeField()
    email = models.CharField(max_length=128, blank=True, null=True)
    credits = models.IntegerField()
    credits_bankruptcy = models.SmallIntegerField(blank=True, null=True)
    lcid = models.SmallIntegerField()
    description = models.TextField()
    notes = models.TextField(blank=True, null=True)
    avatar_url = models.CharField(max_length=255)
    lastplanetid = models.ForeignKey(NavPlanet, models.DO_NOTHING, db_column='lastplanetid', blank=True, null=True)
    deletion_date = models.DateTimeField(blank=True, null=True)
    score = models.IntegerField()
    score_prestige = models.BigIntegerField()
    score_buildings = models.BigIntegerField()
    score_research = models.BigIntegerField()
    score_ships = models.BigIntegerField()
    alliance = models.ForeignKey(Alliances, models.DO_NOTHING, blank=True, null=True)
    alliance_rank = models.ForeignKey(AlliancesRanks, models.DO_NOTHING, db_column='alliance_rank', blank=True, null=True)
    alliance_joined = models.DateTimeField(blank=True, null=True)
    alliance_left = models.DateTimeField(blank=True, null=True)
    alliance_taxes_paid = models.BigIntegerField()
    alliance_credits_given = models.BigIntegerField()
    alliance_credits_taken = models.BigIntegerField()
    alliance_score_combat = models.IntegerField()
    newpassword = models.CharField(max_length=32, blank=True, null=True)
    lastactivity = models.DateTimeField(blank=True, null=True)
    planets = models.IntegerField()
    noplanets_since = models.DateTimeField(blank=True, null=True)
    last_catastrophe = models.DateTimeField()
    last_holidays = models.DateTimeField(blank=True, null=True)
    previous_score = models.IntegerField()
    timers_enabled = models.BooleanField()
    ban_datetime = models.DateTimeField(blank=True, null=True)
    ban_expire = models.DateTimeField(blank=True, null=True)
    ban_reason = models.CharField(max_length=128, blank=True, null=True)
    ban_reason_public = models.CharField(max_length=128, blank=True, null=True)
    ban_adminuserid = models.IntegerField(blank=True, null=True)
    scientists = models.IntegerField()
    soldiers = models.IntegerField()
    dev_lasterror = models.IntegerField(blank=True, null=True)
    dev_lastnotice = models.IntegerField(blank=True, null=True)
    protection_enabled = models.BooleanField()
    protection_colonies_to_unprotect = models.SmallIntegerField()
    protection_datetime = models.DateTimeField()
    max_colonizable_planets = models.IntegerField()
    remaining_colonizations = models.IntegerField()
    upkeep_last_cost = models.IntegerField()
    upkeep_commanders = models.FloatField()
    upkeep_planets = models.FloatField()
    upkeep_scientists = models.FloatField()
    upkeep_soldiers = models.FloatField()
    upkeep_ships = models.FloatField()
    upkeep_ships_in_position = models.FloatField()
    upkeep_ships_parked = models.FloatField()
    wallet_display = models.TextField(blank=True, null=True)  # This field type is a guess.
    resets = models.SmallIntegerField()
    mod_production_ore = models.FloatField()
    mod_production_hydrocarbon = models.FloatField()
    mod_production_energy = models.FloatField()
    mod_production_workers = models.FloatField()
    mod_construction_speed_buildings = models.FloatField()
    mod_construction_speed_ships = models.FloatField()
    mod_fleet_damage = models.FloatField()
    mod_fleet_speed = models.FloatField()
    mod_fleet_shield = models.FloatField()
    mod_fleet_handling = models.FloatField()
    mod_fleet_tracking_speed = models.FloatField()
    mod_fleet_energy_capacity = models.FloatField()
    mod_fleet_energy_usage = models.FloatField()
    mod_fleet_signature = models.FloatField()
    mod_merchant_buy_price = models.FloatField()
    mod_merchant_sell_price = models.FloatField()
    mod_merchant_speed = models.FloatField()
    mod_upkeep_commanders_cost = models.FloatField()
    mod_upkeep_planets_cost = models.FloatField()
    mod_upkeep_scientists_cost = models.FloatField()
    mod_upkeep_soldiers_cost = models.FloatField()
    mod_upkeep_ships_cost = models.FloatField()
    mod_research_cost = models.FloatField()
    mod_research_time = models.FloatField()
    mod_recycling = models.FloatField()
    mod_commanders = models.FloatField()
    mod_planets = models.FloatField()
    commanders_loyalty = models.SmallIntegerField()
    orientation = models.SmallIntegerField()
    admin_notes = models.TextField()
    paid_until = models.DateTimeField(blank=True, null=True)
    autosignature = models.CharField(max_length=512, blank=True, null=True)
    game_started = models.DateTimeField()
    mod_research_effectiveness = models.FloatField()
    mod_energy_transfer_effectiveness = models.FloatField()
    requests = models.BigIntegerField(blank=True, null=True)
    score_next_update = models.DateTimeField()
    display_alliance_planet_name = models.BooleanField()
    score_visibility = models.SmallIntegerField()
    prestige_points = models.IntegerField()
    mod_prestige_from_buildings = models.FloatField()
    displays_ads = models.BigIntegerField()
    displays_pages = models.BigIntegerField()
    ad_bonus_code = models.IntegerField(blank=True, null=True)
    regaddress = models.GenericIPAddressField()
    inframe = models.BooleanField(blank=True, null=True)
    modf_bounty = models.FloatField()
    skin = models.TextField(blank=True, null=True)
    tutorial_first_ship_built = models.BooleanField()
    tutorial_first_colonisation_ship_built = models.BooleanField()
    leave_alliance_datetime = models.DateTimeField(blank=True, null=True)
    production_prestige = models.IntegerField()
    score_visibility_last_change = models.DateTimeField()
    credits_produced = models.BigIntegerField()
    mod_prestige_from_ships = models.FloatField()
    mod_planet_need_ore = models.FloatField()
    mod_planet_need_hydrocarbon = models.FloatField()
    mod_fleets = models.FloatField()
    security_level = models.IntegerField()
    prestige_points_refund = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'users'


class UsersAllianceHistory(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='userid')
    joined = models.DateTimeField()
    left = models.DateTimeField()
    taxes_paid = models.BigIntegerField()
    credits_given = models.BigIntegerField()
    credits_taken = models.BigIntegerField()
    alliance_tag = models.CharField(max_length=4)
    alliance_name = models.CharField(max_length=32)

    class Meta:
        managed = True
        db_table = 'users_alliance_history'


class UsersBounty(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='userid')
    bounty = models.BigIntegerField()
    reward_time = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'users_bounty'


class UsersChannels(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='userid')
    channelid = models.ForeignKey(ChatChannels, models.DO_NOTHING, db_column='channelid')
    password = models.CharField(max_length=16)
    added = models.DateTimeField()
    lastactivity = models.DateTimeField()
    rights = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'users_channels'
        unique_together = (('userid', 'channelid'),)


class UsersChats(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='userid')
    chatid = models.ForeignKey(Chat, models.DO_NOTHING, db_column='chatid')
    password = models.CharField(max_length=16)
    added = models.DateTimeField()
    lastactivity = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'users_chats'
        unique_together = (('userid', 'chatid'),)


class UsersConnections(models.Model):
    id = models.BigAutoField(primary_key=True)
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='userid', blank=True, null=True)
    datetime = models.DateTimeField()
    forwarded_address = models.CharField(max_length=64, blank=True, null=True)
    browser = models.CharField(max_length=128)
    address = models.BigIntegerField()
    browserid = models.BigIntegerField()
    disconnected = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'users_connections'


class UsersExpenses(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='userid')
    datetime = models.DateTimeField()
    credits = models.IntegerField()
    credits_delta = models.IntegerField()
    buildingid = models.IntegerField(blank=True, null=True)
    shipid = models.IntegerField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    fleetid = models.IntegerField(blank=True, null=True)
    planetid = models.IntegerField(blank=True, null=True)
    ore = models.IntegerField(blank=True, null=True)
    hydrocarbon = models.IntegerField(blank=True, null=True)
    to_alliance = models.IntegerField(blank=True, null=True)
    to_user = models.IntegerField(blank=True, null=True)
    leave_alliance = models.IntegerField(blank=True, null=True)
    spyid = models.IntegerField(blank=True, null=True)
    scientists = models.IntegerField(blank=True, null=True)
    soldiers = models.IntegerField(blank=True, null=True)
    researchid = models.IntegerField(blank=True, null=True)
    login = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'users_expenses'


class UsersFavoriteLocations(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='userid')
    galaxy = models.SmallIntegerField()
    sector = models.SmallIntegerField(blank=True, null=True)
    added = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'users_favorite_locations'


class UsersFleetsCategories(models.Model):
    userid = models.IntegerField(primary_key=True)
    category = models.SmallIntegerField()
    label = models.CharField(max_length=32)

    class Meta:
        managed = True
        db_table = 'users_fleets_categories'
        unique_together = (('userid', 'category'),)


class UsersHolidays(models.Model):
    userid = models.OneToOneField(Users, models.DO_NOTHING, db_column='userid')
    start_time = models.DateTimeField()
    min_end_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    activated = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'users_holidays'


class UsersNewemails(models.Model):
    userid = models.OneToOneField(Users, models.DO_NOTHING, db_column='userid')
    email = models.CharField(max_length=128)
    key = models.CharField(max_length=8)
    expiration = models.DateTimeField()

    class Meta:
        managed = True
        db_table = 'users_newemails'


class UsersOptionsHistory(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='userid')
    datetime = models.DateTimeField()
    action = models.SmallIntegerField()
    info = models.TextField()
    browser = models.TextField()
    address = models.BigIntegerField(blank=True, null=True)
    forwarded_address = models.TextField(blank=True, null=True)
    browserid = models.BigIntegerField()

    class Meta:
        managed = True
        db_table = 'users_options_history'


class UsersRegistrationAddress(models.Model):
    userid = models.IntegerField()
    address = models.TextField()

    class Meta:
        managed = True
        db_table = 'users_registration_address'


class UsersReports(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='userid')
    type = models.SmallIntegerField()
    subtype = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'users_reports'
        unique_together = (('userid', 'type', 'subtype'),)


class UsersShipsKills(models.Model):
    userid = models.ForeignKey(Users, models.DO_NOTHING, db_column='userid')
    shipid = models.ForeignKey('DbShips', models.DO_NOTHING, db_column='shipid')
    killed = models.IntegerField()
    lost = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'users_ships_kills'
        unique_together = (('userid', 'shipid'),)

class BannedDomains(models.Model):
    domain = models.CharField(primary_key=True, max_length=64, unique=True)

    class Meta:
        managed = True
        db_table = 'banned_domains'


class BannedLogins(models.Model):
    login = models.TextField(primary_key=True)

    class Meta:
        managed = True
        db_table = 'banned_logins'


class ChatBannedWords(models.Model):
    regexp = models.TextField()
    replace_by = models.TextField()

    class Meta:
        managed = True
        db_table = 'chat_banned_words'


class DbBuildings(models.Model):
    category = models.SmallIntegerField()
    name = models.CharField(max_length=32)
    label = models.CharField(max_length=64)
    description = models.TextField()
    cost_ore = models.IntegerField()
    cost_hydrocarbon = models.IntegerField()
    cost_credits = models.IntegerField()
    workers = models.IntegerField()
    energy_consumption = models.IntegerField()
    energy_production = models.IntegerField()
    floor = models.SmallIntegerField()
    space = models.SmallIntegerField()
    production_ore = models.IntegerField()
    production_hydrocarbon = models.IntegerField()
    storage_ore = models.IntegerField()
    storage_hydrocarbon = models.IntegerField()
    storage_workers = models.IntegerField()
    construction_maximum = models.SmallIntegerField()
    construction_time = models.IntegerField()
    destroyable = models.BooleanField()
    mod_production_ore = models.FloatField()
    mod_production_hydrocarbon = models.FloatField()
    mod_production_energy = models.FloatField()
    mod_production_workers = models.FloatField()
    mod_construction_speed_buildings = models.FloatField()
    mod_construction_speed_ships = models.FloatField()
    storage_scientists = models.IntegerField()
    storage_soldiers = models.IntegerField()
    radar_strength = models.SmallIntegerField()
    radar_jamming = models.SmallIntegerField()
    is_planet_element = models.BooleanField()
    can_be_disabled = models.BooleanField()
    training_scientists = models.IntegerField()
    training_soldiers = models.IntegerField()
    maintenance_factor = models.SmallIntegerField()
    security_factor = models.SmallIntegerField()
    sandworm_activity = models.SmallIntegerField()
    seismic_activity = models.SmallIntegerField()
    production_credits = models.IntegerField()
    production_credits_random = models.IntegerField()
    mod_research_effectiveness = models.FloatField()
    energy_receive_antennas = models.SmallIntegerField()
    energy_send_antennas = models.SmallIntegerField()
    construction_time_exp_per_building = models.FloatField()
    storage_energy = models.IntegerField()
    buildable = models.BooleanField()
    lifetime = models.IntegerField()
    active_when_destroying = models.BooleanField()
    upkeep = models.IntegerField()
    cost_energy = models.IntegerField()
    use_planet_production_pct = models.BooleanField()
    production_exp_per_building = models.FloatField(blank=True, null=True)
    consumption_exp_per_building = models.FloatField(blank=True, null=True)
    vortex_strength = models.IntegerField()
    production_prestige = models.IntegerField()
    cost_prestige = models.IntegerField()
    mod_planet_need_ore = models.FloatField()
    mod_planet_need_hydrocarbon = models.FloatField()
    bonus_planet_need_ore = models.IntegerField()
    bonus_planet_need_hydrocarbon = models.IntegerField()
    visible = models.BooleanField()
    invasion_defense = models.IntegerField()
    parked_ships_capacity = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'db_buildings'


class DbBuildingsCategories(models.Model):
    id = models.SmallIntegerField(primary_key=True)
    name = models.CharField(max_length=32)

    class Meta:
        managed = True
        db_table = 'db_buildings_categories'


class DbBuildingsReqBuilding(models.Model):
    buildingid = models.ForeignKey(DbBuildings, models.DO_NOTHING, db_column='buildingid', related_name='dbrb_building_set')
    required_buildingid = models.ForeignKey(DbBuildings, models.DO_NOTHING, db_column='required_buildingid', related_name='dbrb_required_building_set')

    class Meta:
        managed = True
        db_table = 'db_buildings_req_building'
        unique_together = (('buildingid', 'required_buildingid'),)


class DbBuildingsReqResearch(models.Model):
    buildingid = models.ForeignKey(DbBuildings, models.DO_NOTHING, db_column='buildingid')
    required_researchid = models.ForeignKey('DbResearch', models.DO_NOTHING, db_column='required_researchid')
    required_researchlevel = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'db_buildings_req_research'
        unique_together = (('buildingid', 'required_researchid'),)


class DbFirstnames(models.Model):
    name = models.CharField(max_length=16)

    class Meta:
        managed = True
        db_table = 'db_firstnames'


class DbItems(models.Model):
    category = models.SmallIntegerField()
    name = models.CharField(max_length=32)
    label = models.CharField(max_length=64)
    description = models.TextField()
    virtual = models.BooleanField()
    movable = models.BooleanField()
    volume = models.FloatField()

    class Meta:
        managed = True
        db_table = 'db_items'


class DbLcid(models.Model):
    lcid = models.IntegerField(primary_key=True)
    name = models.TextField()
    label = models.TextField()

    class Meta:
        managed = True
        db_table = 'db_lcid'


class DbMessages(models.Model):
    lcid = models.SmallIntegerField()
    subject = models.TextField()
    body = models.TextField()
    sender = models.TextField()

    class Meta:
        managed = True
        db_table = 'db_messages'


class DbNames(models.Model):
    name = models.CharField(max_length=16)

    class Meta:
        managed = True
        db_table = 'db_names'


class DbOrientations(models.Model):
    name = models.TextField()
    selectable = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'db_orientations'


class DbResearch(models.Model):
    category = models.SmallIntegerField()
    name = models.CharField(max_length=32)
    label = models.CharField(max_length=64)
    description = models.TextField()
    rank = models.IntegerField()
    levels = models.SmallIntegerField()
    defaultlevel = models.SmallIntegerField()
    cost_credits = models.IntegerField()
    mod_production_ore = models.FloatField()
    mod_production_hydrocarbon = models.FloatField()
    mod_production_energy = models.FloatField()
    mod_production_workers = models.FloatField()
    mod_construction_speed_buildings = models.FloatField()
    mod_construction_speed_ships = models.FloatField()
    mod_fleet_damage = models.FloatField()
    mod_fleet_speed = models.FloatField()
    mod_fleet_shield = models.FloatField()
    mod_fleet_handling = models.FloatField()
    mod_fleet_tracking_speed = models.FloatField()
    mod_fleet_energy_capacity = models.FloatField()
    mod_fleet_energy_usage = models.FloatField()
    mod_fleet_signature = models.FloatField()
    mod_merchant_buy_price = models.FloatField()
    mod_merchant_sell_price = models.FloatField()
    mod_merchant_speed = models.FloatField()
    mod_upkeep_commanders_cost = models.FloatField()
    mod_upkeep_planets_cost = models.FloatField()
    mod_upkeep_scientists_cost = models.FloatField()
    mod_upkeep_soldiers_cost = models.FloatField()
    mod_upkeep_ships_cost = models.FloatField()
    mod_research_cost = models.FloatField()
    mod_research_time = models.FloatField()
    mod_recycling = models.FloatField()
    mod_commanders = models.FloatField()
    mod_planets = models.FloatField()
    mod_research_effectiveness = models.FloatField()
    mod_energy_transfer_effectiveness = models.FloatField()
    mod_prestige_from_ships = models.FloatField()
    modf_bounty = models.FloatField()
    mod_prestige_from_buildings = models.FloatField()
    mod_planet_need_ore = models.FloatField()
    mod_planet_need_hydrocarbon = models.FloatField()
    mod_fleet_jump_speed = models.FloatField()
    expiration = models.DurationField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'db_research'


class DbResearchReqBuilding(models.Model):
    researchid = models.ForeignKey(DbResearch, models.DO_NOTHING, db_column='researchid')
    required_buildingid = models.ForeignKey(DbBuildings, models.DO_NOTHING, db_column='required_buildingid')
    required_buildingcount = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'db_research_req_building'
        unique_together = (('researchid', 'required_buildingid'),)


class DbResearchReqResearch(models.Model):
    researchid = models.ForeignKey(DbResearch, models.DO_NOTHING, db_column='researchid', related_name='drrr_research_set')
    required_researchid = models.ForeignKey(DbResearch, models.DO_NOTHING, db_column='required_researchid', related_name='drrr_required_research_set')
    required_researchlevel = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'db_research_req_research'
        unique_together = (('researchid', 'required_researchid'),)


class DbSecurityLevels(models.Model):
    id = models.IntegerField(primary_key=True)
    max_planets = models.IntegerField()
    max_commanders = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'db_security_levels'


class DbShipModules(models.Model):
    category = models.SmallIntegerField()
    label = models.TextField()
    description = models.TextField()
    cost_ore = models.IntegerField()
    cost_hydrocarbon = models.IntegerField()
    cost_credits = models.IntegerField()
    workers = models.IntegerField()
    crew = models.SmallIntegerField()
    capacity = models.IntegerField()
    construction_time = models.IntegerField()
    maximum = models.SmallIntegerField()
    hull = models.IntegerField()
    shield = models.IntegerField()
    weapon_power = models.SmallIntegerField()
    weapon_ammo = models.SmallIntegerField()
    weapon_tracking_speed = models.SmallIntegerField()
    weapon_turrets = models.SmallIntegerField()
    signature = models.SmallIntegerField()
    speed = models.IntegerField()
    handling = models.IntegerField()
    recycler_output = models.IntegerField()
    droppods = models.SmallIntegerField()
    long_distance_capacity = models.SmallIntegerField()
    mod_speed = models.SmallIntegerField()
    mod_shield = models.SmallIntegerField()
    mod_handling = models.SmallIntegerField()
    mod_tracking_speed = models.SmallIntegerField()
    mod_damage = models.SmallIntegerField()
    mod_signature = models.SmallIntegerField()
    mod_recycling = models.SmallIntegerField()
    cpu = models.SmallIntegerField()
    power = models.SmallIntegerField()
    usage_cpu = models.SmallIntegerField()
    usage_power = models.SmallIntegerField()
    usage_slot_low = models.SmallIntegerField()
    usage_slot_middle = models.SmallIntegerField()
    usage_slot_high = models.SmallIntegerField()
    weight = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'db_ship_modules'


class DbShipStructures(models.Model):
    category = models.SmallIntegerField()
    label = models.TextField()
    description = models.TextField()
    cost_ore = models.IntegerField()
    cost_hydrocarbon = models.IntegerField()
    cost_credits = models.IntegerField()
    workers = models.IntegerField()
    crew = models.IntegerField()
    capacity = models.IntegerField()
    construction_time = models.IntegerField()
    hull = models.IntegerField()
    signature = models.SmallIntegerField()
    handling = models.IntegerField()
    buildingid = models.IntegerField(blank=True, null=True)
    cpu = models.SmallIntegerField()
    power = models.SmallIntegerField()
    slot_low = models.SmallIntegerField()
    slot_middle = models.SmallIntegerField()
    slot_high = models.SmallIntegerField()
    weight = models.IntegerField(db_column='Weight')  # Field name made lowercase.

    class Meta:
        managed = True
        db_table = 'db_ship_structures'


class DbShips(models.Model):
    category = models.SmallIntegerField(blank=True, null=True)
    name = models.CharField(max_length=32)
    label = models.CharField(max_length=64)
    description = models.TextField()
    cost_ore = models.IntegerField()
    cost_hydrocarbon = models.IntegerField()
    cost_credits = models.IntegerField()
    workers = models.IntegerField()
    crew = models.SmallIntegerField()
    capacity = models.IntegerField()
    construction_time = models.IntegerField()
    maximum = models.SmallIntegerField()
    hull = models.IntegerField()
    shield = models.IntegerField()
    weapon_power = models.SmallIntegerField()
    weapon_ammo = models.SmallIntegerField()
    weapon_tracking_speed = models.SmallIntegerField()
    weapon_turrets = models.SmallIntegerField()
    signature = models.SmallIntegerField()
    speed = models.IntegerField()
    handling = models.SmallIntegerField()
    buildingid = models.ForeignKey(DbBuildings, models.DO_NOTHING, db_column='buildingid', blank=True, null=True)
    recycler_output = models.IntegerField()
    droppods = models.SmallIntegerField()
    long_distance_capacity = models.SmallIntegerField()
    buildable = models.BooleanField()
    required_shipid = models.IntegerField(blank=True, null=True)
    new_shipid = models.IntegerField(blank=True, null=True)
    mod_speed = models.FloatField()
    mod_shield = models.FloatField()
    mod_handling = models.FloatField()
    mod_tracking_speed = models.FloatField()
    mod_damage = models.FloatField()
    mod_signature = models.FloatField()
    mod_recycling = models.FloatField()
    protection = models.IntegerField()
    upkeep = models.IntegerField()
    cost_energy = models.IntegerField()
    weapon_dmg_em = models.SmallIntegerField()
    weapon_dmg_explosive = models.SmallIntegerField()
    weapon_dmg_kinetic = models.SmallIntegerField()
    weapon_dmg_thermal = models.SmallIntegerField()
    resist_em = models.SmallIntegerField()
    resist_explosive = models.SmallIntegerField()
    resist_kinetic = models.SmallIntegerField()
    resist_thermal = models.SmallIntegerField()
    tech = models.SmallIntegerField()
    prestige_reward = models.IntegerField()
    credits_reward = models.IntegerField()
    cost_prestige = models.IntegerField()
    built_per_batch = models.IntegerField()
    bounty = models.IntegerField()
    required_vortex_strength = models.IntegerField()
    leadership = models.IntegerField()
    can_be_parked = models.BooleanField()
    required_jump_capacity = models.IntegerField()

    class Meta:
        managed = True
        db_table = 'db_ships'


class DbShipsReqBuilding(models.Model):
    shipid = models.ForeignKey(DbShips, models.DO_NOTHING, db_column='shipid')
    required_buildingid = models.ForeignKey(DbBuildings, models.DO_NOTHING, db_column='required_buildingid')

    class Meta:
        managed = True
        db_table = 'db_ships_req_building'
        unique_together = (('shipid', 'required_buildingid'),)


class DbShipsReqResearch(models.Model):
    shipid = models.ForeignKey(DbShips, models.DO_NOTHING, db_column='shipid')
    required_researchid = models.ForeignKey(DbResearch, models.DO_NOTHING, db_column='required_researchid')
    required_researchlevel = models.SmallIntegerField()

    class Meta:
        managed = True
        db_table = 'db_ships_req_research'
        unique_together = (('shipid', 'required_researchid'),)


class DbSuccesses(models.Model):
    name = models.TextField()

    class Meta:
        managed = True
        db_table = 'db_successes'


class GscLevels(models.Model):
    id = models.AutoField(primary_key=True)

    class Meta:
        managed = True
        db_table = 'gsc_levels'