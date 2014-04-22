#!/usr/bin/env python
from function_template import *
import requests
import json


class function(function_template):
    def __init__(self):
        function_template.__init__(self)
        self.commands = ["translate", "trans"]
        self.function_string = "Translate a string. Syntax: '!translate <lang> <message...>'\nExample Languages: 'es' = Spanish, 'es-US' = US Spanish, etc. List: http://www.i18nguy.com/unicode/language-identifiers.html"

    def main(self, bot, msg_data, func_type):
        message = msg_data["message"]
        lang = message[1]
        error = ''
        nonTranslated = ''
        if len(message) > 1:
            nonTranslated = "".join(msg_data["message"][2:])
        else:
            error = 'Syntax: !translate <lang> <message...>'
        if not(error):
            r = requests.get("http://api.mymemory.translated.net/get?langpair=" + lang + "|en&de=overcastian@mailinator.com&q=" + nonTranslated)
            translated = ''
            if r.status_code != requests.codes.ok:
                error = 'Request Exception - Code: ' + str(r.status_code)
            else:
                jsonObj = json.loads(r.text)
                translated = jsonObj["responseData"]["translatedText"]
                bot._irc.sendMSG("\"" + str(translated) + "\"", msg_data["target"])


        if error: bot._irc.sendMSG(error, msg_data["target"])
        return True
