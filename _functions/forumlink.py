#!/usr/bin/env python
from function_template import *
import requests

class function(function_template):
    def __init__(self):
        function_template.__init__(self)
        self.type = ["natural"]
        self.priority = 100
        self.functionString = "Get the title for oc.tc/forum links."
        self.hidden = True


    def main(self, bot, msgData, funcType):
        if (funcType == "natural"):
            message = string.join(msgData["message"])
            linkMatch = re.findall("(oc\.tc/forums/topics/[A-Za-z0-9-]+|oc\.tc/forums/[A-Za-z0-9-]+)", message, re.IGNORECASE)
            if linkMatch:
                for link in linkMatch:
                    r = requests.get("http://" + link)
                    if r.status_code != requests.codes.ok:
                        continue

                    soup = BeautifulSoup(r.text)
                    if soup.find('title'):
                        pageTitle = soup.find('title').get_text().strip()
                        if pageTitle == "Home - Overcast Network Forum":
                            continue
                        bot._irc.sendMSG(pageTitle, msgData["target"])
                
                return True
        
        return False


