#!/usr/bin/env python
from function_template import *


class function(function_template):
    def __init__(self):
        function_template.__init__(self)
        self.commands = ["player"]
        self.functionString = "Show the stats for a player."

    def main(self, bot, msgData, funcType):
        message = msgData["message"]
        player = "";
        if len(message) > 1:
            player = message[1]
        else:
            bot._irc.sendMSG("No player specified", msgData["target"])
            return True

        error = ''
        try: data = urllib.urlopen('http://oc.tc/' + str(player))
        except urllib2.HTTPError, e:
            error = 'HTTP Error: ' + str(e.code)
        except urllib2.URLError, e:
            error = 'URL Error: ' + str(e.reason)
        except httplib.HTTPException, e:
            error = 'HTTP Exception'
        else:
            if (data.getcode() == int('404')):
                error = '404 - User not found'
            elif (data.getcode() == int('200')):
                soup = BeautifulSoup(data)
                if soup.find("h4", text=["Account Suspended"]):
                    error = 'User Account Suspended'
                else:
                    kills = soup.find("small", text=["kills"]).findParent('h2').contents[0].strip('\n')

                    last_seen_data = soup.find("span", text=re.compile(".*%s.*" % str(player), re.IGNORECASE)).findParent('h1')
                    last_seen_server = last_seen_data.find(href="/play").contents[1].contents[0]

                    last_seen = string.join(last_seen_data.contents[3].contents[0].split())
                    if last_seen == "Online:":
                        last_seen = last_seen + " " + last_seen_server
                    
                    deaths = soup.find("small", text=["deaths"]).findParent('h2').contents[0].strip('\n')
                    friends = soup.find("small", text=["friends"]).findParent('h2').contents[0].strip('\n')
                    kd_ratio = soup.find("small", text=["kd ratio"]).findParent('h2').contents[0].strip('\n')
                    kk_ratio = soup.find("small", text=["kk ratio"]).findParent('h2').contents[0].strip('\n')
                    joins = soup.find("small", text=["server joins"]).findParent('h2').contents[0].strip('\n')
                    
                    bot._irc.sendMSG("%s - %s" % (str(player), last_seen), msgData["target"])
                    bot._irc.sendMSG("Kills:%s, Deaths:%s, KD Ratio:%s, KK Ratio:%s" % (kills, deaths, kd_ratio, kk_ratio), msgData["target"])
                    bot._irc.sendMSG("Friends:%s, Joins:%s" % (friends, joins), msgData["target"])

        if error: bot._irc.sendMSG(error, msgData["target"])
        return True
