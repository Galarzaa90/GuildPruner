import urllib.request
from operator import itemgetter, attrgetter, methodcaller
import time
from calendar import timegm
import re
from datetime import datetime, timedelta, date
import pickle
import os
import platform

# TODO: Cleanup code
# TODO: Foolproof
# TODO: Better console interface

ERROR_DOESNTEXIST = 1
ERROR_NETWORK = 2


def save_data(file, data):
    with open(file, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_data(file):
    try:
        with open(file, "rb") as f:
            return pickle.load(f)
    except ValueError:
        return None
    except FileNotFoundError:
        return None


def month_to_number(string):
    m = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7,
         'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
    s = string.strip()[:3].lower()
    try:
        out = m[s]
        return out
    except:
        raise ValueError('Not a month')


def get_guild_players(guildname, tries=5):
    content = ""
    url = "https://secure.tibia.com/community/?subtopic=guilds&page=view&GuildName=" + urllib.parse.quote(guildname)
    # Number of retries exhausted
    if tries == 0:
        print("Error: Couldn't fetch guild after 5 tries")
        return ERROR_NETWORK
    # Fetch website
    try:
        page = urllib.request.urlopen(url)
        content = page.read().decode('ISO-8859-1')
    except Exception:
        return get_guild_players(guildname, tries - 1)
    # Trimming content to reduce load
    try:
        start_index = content.index('<div class="BoxContent"')
        end_index = content.index('<div id="ThemeboxesColumn" >')
        content = content[start_index:end_index]
    except ValueError:
        # Website fetch was incomplete
        return get_guild_players(guildname, tries - 1)

    if '<div class="Text" >Error</div>' in content:
        return ERROR_DOESNTEXIST

    # Regex pattern to fetch information
    regex_members = r'<TR BGCOLOR=#[\dABCDEF]+><TD>(.+?)</TD>\s</td><TD><A HREF="https://secure.tibia.com/community/\?subtopic=characters&name=(.+?)">.+?</A> *\(*(.*?)\)*</TD>\s<TD>(.+?)</TD>\s<TD>(.+?)</TD>\s<TD>(.+?)</TD>'
    pattern = re.compile(regex_members, re.MULTILINE + re.S)

    m = re.findall(pattern, content)
    member_list = []
    # Check if list is empty
    if m:
        # Building dictionary list from members
        for (rank, name, title, vocation, level, joined) in m:
            rank = '' if (rank == '&#160;') else rank
            name = urllib.parse.unquote_plus(name)
            joined = joined.replace('&#160;', '/')
            joined = datetime.strptime(joined, "%b/%d/%Y")
            member_list.append({'rank': rank, 'name': name, 'title': title,
                                'vocation': vocation, 'level': int(level), 'joined': joined})
    return member_list


def get_character(name, tries=5):
    url = "https://secure.tibia.com/community/?subtopic=characters&name=" + urllib.parse.quote(name)
    content = ""
    char = dict()
    if tries == 0:
        print("Couldn't fetch {0} after 5 tries".format(name))
        return ERROR_NETWORK
    # Fetch website
    try:
        page = urllib.request.urlopen(url)
        content = page.read().decode('ISO-8859-1')
    except Exception:
        return get_character(name, tries - 1)

    # Trimming content to reduce load
    try:
        start_index = content.index('<div class="BoxContent"')
        end_index = content.index("<B>Search Character</B>")
        content = content[start_index:end_index]
    except ValueError:
        # Website fetch was incomplete, due to a network error
        return get_character(name, tries)
    # Check if player exists
    if "Name:</td><td>" not in content:
        return ERROR_DOESNTEXIST

    # Premium status
    m = re.search(r'Status:</td><td>([^<]+)', content)
    if m:
        char['status'] = m.group(1).strip()

    # Last login
    m = re.search(r'Last Login:</td><td>([^<]+)', content)
    if m:
        char['lastlogin'] = m.group(1).strip().replace('&#160;', ' ')

    return char


def get_local_time(tibiaTime):
    """Gets a time object from a time string from tibia.com"""
    # Getting local time and GMT
    t = time.localtime()
    u = time.gmtime(time.mktime(t))
    # UTC Offset
    local_utc_offset = ((timegm(t) - timegm(u)) / 60 / 60)

    # Convert time string to time object
    # Removing timezone cause CEST and CET are not supported
    t = datetime.strptime(tibiaTime[:-4].strip(), "%b %d %Y, %H:%M:%S")
    # Extracting timezone
    tz = tibiaTime[-4:].strip()

    # Getting the offset
    if tz == "CET":
        utc_offset = 1
    elif tz == "CEST":
        utc_offset = 2
    else:
        return None
    # Add/substract hours to get the real time
    return t + timedelta(hours=(local_utc_offset - utc_offset))


def get_days(time):
    """Returns the difference in days of a timedelta"""
    if not isinstance(time, timedelta):
        return None
    days = time.days
    if days <= 0:
        return "<1 day"
    if days == 1:
        return "1 day"
    return "{0} days".format(days)


def get_vocation_acronym(vocation):
    """Given a vocation name, it returns an abbreviated string """
    abbrev = {'None': 'N', 'Druid': 'D', 'Sorcerer': 'S', 'Paladin': 'P', 'Knight': 'K',
              'Elder Druid': 'ED', 'Master Sorcerer': 'MS', 'Royal Paladin': 'RP', 'Elite Knight': 'EK'}
    try:
        return abbrev[vocation]
    except KeyError:
        return 'N'


def clear_screen():
    if platform.system() == "Linux":
        os.system("clear")
    else:
        os.system("cls")


def fetch_guild_data(name):
    memberlist = get_guild_players(name)
    if type(memberlist) != list:
        return memberlist
    i = 1
    for member in memberlist:
        time.sleep(0.15)
        print("Fetching members: {0}/{1}".format(i, len(memberlist)))
        player = get_character(member['name'])
        if (type(player) is dict):
            member['status'] = player['status']
            member['lastlogin'] = get_local_time(player['lastlogin'])
        else:
            print("error")
        i += 1
    return memberlist


if __name__ == "__main__":
    minLevel = 1000
    freeAccount = 0
    daysInactive = 0
    guildname = input("Enter the name (exact case) of the guild you want to check: ")
    memberlist = load_data(guildname + ".data")
    if memberlist is None:
        print("Gathering guild data...")
        memberlist = fetch_guild_data(guildname)
        save_data(guildname + ".data", memberlist)
    else:
        choice = input(
            "Data for this guild was found, do you want to use this data instead of fetching new data? (y/n): ")
        if choice == "n":
            print("Gathering guild data...")
            memberlist = fetch_guild_data(guildname)
            save_data(guildname + ".data", memberlist)
    choice = ""
    while choice != "exit":
        print("1. List members")
        print("2. Set mininum level")
        print("3. Set account status")
        print("4. Set days without logging")
        print("5. Sort by level")
        print("6. Sort by join date")
        print("7. Sort by days without logging")
        choice = input("Select an option: ")
        clear_screen()
        if choice == "1":
            print()
            print("Name".ljust(25) + "\tLevel\tAccount Status\tTime in guild\tLast login")
            for member in memberlist:
                if (member["level"] <= minLevel and (member["status"] == "Free Account" or freeAccount == 0) and (
                            (datetime.now() - member["lastlogin"]).days > daysInactive)):
                    print("{0}\t{1} {2}\t{3}\t{4}\t{5}".format(member["name"].ljust(25), member["level"],
                                                               get_vocation_acronym(member["vocation"]),
                                                               member["status"],
                                                               get_days(datetime.now() - member["joined"]).ljust(15),
                                                               get_days(datetime.now() - member["lastlogin"])))
        if choice == "2":
            print("If a mininum level is set, characters above this level won't be shown")
            minLevel = int(input("Enter mininum level: "))
        if choice == "3":
            print("Select wether only free accounts will be considered or players with any status")
            choice = input("1) Free account only 2) Any status:")
            if choice == "1":
                freeAccount = 1
        if choice == "4":
            days = input("Enter the number of days without logging in a member needs to be considered: ")
            daysInactive = int(days)
        if choice == "5":
            memberlist = sorted(memberlist, key=itemgetter("level"))
        if choice == "6":
            memberlist = sorted(memberlist, key=itemgetter("joined"))
        if choice == "7":
            memberlist = sorted(memberlist, key=itemgetter("lastlogin"))
