#!/usr/bin/env python
from function_template import *
import requests
import json

import logging
log = logging.getLogger('bot')

class function(function_template):
    syntax = 'Syntax: !translate <lang> <message...>'
    langList = "www.i18nguy.com/unicode/language-identifiers.html"
    def __init__(self):
        function_template.__init__(self)
        self.commands = ["translate", "trans"]
        self.function_string = "Translate a string. Syntax: '!translate <lang> <message...>'\nExample Languages: 'es' = Spanish, 'es-US' = US Spanish, etc. List: " + langList

    def main(self, bot, msg_data, func_type):
        message = msg_data["message"]
        error = ''
        if len(message) > 0:
            lang = message[1]
            if lang == 'en':
                error = 'Please use a language other than "en"'
            nonTranslated = ''
            if len(message) > 1:
                nonTranslated = " ".join(msg_data["message"][2:])
                if not(error):
                    r = requests.get("http://api.mymemory.translated.net/get?langpair=" + lang + "|en&de=overcastian@mailinator.com&q=" + nonTranslated)
                    translated = ''
                    if r.status_code != requests.codes.ok:
                        error = 'Request Exception - Code: ' + str(r.status_code)
                    else:
                        jsonObj = json.loads(r.text)
                        translated = jsonObj["responseData"]["translatedText"]
                        status = jsonObj["responseStatus"]
                        if status != 200:
                            if "PLEASE SELECT TWO DISTINCT LANGUAGES" in translated:
                                error = 'Please use a non english language'
                            if "NO QUERY SPECIFIED" in translated:
                                error = syntax
                            if "INVALID SOURCE LANGUAGE" in translated:
                                error = "\"" + lang + "\" is not a valid language. List: " + langList
                            if not(error):
                                error = "Unknown error when translating. See console"
                                log.info('"' + translated + '" for "' + nonTranslated + '" with lang: ' + lang)

                        if not(error):
                            bot._irc.sendMSG("\"" + str(translated) + "\"", msg_data["target"])
            else:
                error = syntax
        else:
            error = syntax
        if error: bot._irc.sendMSG(error, msg_data["target"])
        return True
