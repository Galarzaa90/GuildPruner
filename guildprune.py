import urllib.request
from operator import itemgetter, attrgetter, methodcaller
import time
from calendar import timegm
import re
from datetime import datetime,timedelta,date
import pickle

ERROR_DOESNTEXIST = 1
ERROR_NETWORK = 2

def saveData(file,data):
    with open(file,"wb") as f:
        pickle.dump(data,f,protocol=pickle.HIGHEST_PROTOCOL)

def loadData(file):
    try:
        with open(file,"rb") as f:
            return pickle.load(f)
    except ValueError:
        return None
    except FileNotFoundError:
        return None

def monthToNumber(string):
    m = {'jan': 1,'feb': 2,'mar': 3,'apr':4,'may':5,'jun':6,'jul':7,
        'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
    s = string.strip()[:3].lower()
    try:
        out = m[s]
        return out
    except:
        raise ValueError('Not a month')

def getGuildPlayers(guildname,tries=5):
    content = ""
    url = "https://secure.tibia.com/community/?subtopic=guilds&page=view&GuildName="+urllib.parse.quote(guildname)
    #Number of retries exhausted
    if(tries == 0):
        print("Error: Couldn't fetch guild after 5 tries")
        return ERROR_NETWORK
    #Fetch website
    try:
        page = urllib.request.urlopen(url)
        content = page.read().decode('ISO-8859-1')
    except Exception:
        return getGuildPlayers(guildname,tries-1)
    #Trimming content to reduce load
    try:
        startIndex = content.index('<div class="BoxContent"')
        endIndex = content.index('<div id="ThemeboxesColumn" >')
        content = content[startIndex:endIndex]
    except ValueError:
        #Website fetch was incomplete
        return getGuildPlayers(guildname,tries-1)

    if '<div class="Text" >Error</div>' in content:
        return ERROR_DOESNTEXIST
    
    #Regex pattern to fetch information
    regex_members = r'<TR BGCOLOR=#[\dABCDEF]+><TD>(.+?)</TD>\s</td><TD><A HREF="https://secure.tibia.com/community/\?subtopic=characters&name=(.+?)">.+?</A> *\(*(.*?)\)*</TD>\s<TD>(.+?)</TD>\s<TD>(.+?)</TD>\s<TD>(.+?)</TD>'
    pattern = re.compile(regex_members,re.MULTILINE+re.S)

    m = re.findall(pattern,content)
    member_list = []
    #Check if list is empty
    if m:
        #Building dictionary list from members
        for (rank, name, title, vocation, level, joined) in m:
            rank = '' if (rank == '&#160;') else rank
            name = urllib.parse.unquote_plus(name)
            joined = joined.replace('&#160;','/')
            joined = datetime.strptime(joined,"%b/%d/%Y")
            member_list.append({'rank' : rank, 'name' : name, 'title' : title,
            'vocation' : vocation, 'level' : int(level), 'joined' : joined})
    return member_list

def getPlayer(name,tries = 5):
    url = "https://secure.tibia.com/community/?subtopic=characters&name="+urllib.parse.quote(name)
    content = ""
    char = dict()
    if(tries == 0):
        print("Couldn't fetch player after 5 tries")
        return ERROR_NETWORK
    #Fetch website
    try:
        page = urllib.request.urlopen(url)
        content = page.read().decode('ISO-8859-1')
    except Exception:
        return getPlayer(name,tries-1)

    #Trimming content to reduce load
    try:
        startIndex = content.index('<div class="BoxContent"')
        endIndex = content.index("<B>Search Character</B>")
        content = content[startIndex:endIndex]
    except ValueError:
        #Website fetch was incomplete, due to a network error
            return getPlayer(name,tries)
    #Check if player exists
    if "Name:</td><td>" not in content:
        return ERROR_DOESNTEXIST

    #Premium status
    m = re.search(r'Status:</td><td>([^<]+)',content)
    if m:
        char['status'] = m.group(1).strip()

    #Last login
    m = re.search(r'Last login:</td><td>([^<]+)',content)
    if m:
        char['lastlogin'] = m.group(1).strip().replace('&#160;',' ')

    return char

def getLocalTime(tibiaTime):
    """Gets a time object from a time string from tibia.com"""
    #Getting local time and GMT
    t = time.localtime()
    u = time.gmtime(time.mktime(t))
    #UTC Offset
    local_utc_offset = ((timegm(t) - timegm(u))/60/60)

    #Convert time string to time object
    #Removing timezone cause CEST and CET are not supported
    t = datetime.strptime(tibiaTime[:-4].strip(), "%b %d %Y, %H:%M:%S")
    #Extracting timezone
    tz = tibiaTime[-4:].strip()

    #Getting the offset
    if(tz == "CET"):
        utc_offset = 1
    elif(tz == "CEST"):
        utc_offset = 2
    else:
        return None
    #Add/substract hours to get the real time
    return t + timedelta(hours=(local_utc_offset - utc_offset))

guildname = "Redd Alliance"
memberlist = loadData(guildname+".data")
if memberlist is None:
    print("no data found, gathering")
    memberlist = getGuildPlayers(guildname)
    for member in memberlist:
        player = getPlayer(member['name'])
        if(type(player) is dict):
            member['status'] = player['status']
            member['lastlogin'] = getLocalTime(player['lastlogin'])
    saveData(guildname+".data",memberlist)
else:
    print("data previously saved")
print("before sort")
for member in memberlist:
    print("{name} - {level}".format(**member))
print("***************************After sort****************************")
memberlist = sorted(memberlist,key=itemgetter("joined"))
for member in memberlist:
    print("{name} - {level}".format(**member))
print("done")

