#!/usr/bin/env python
# encoding: utf-8

import hunspell
import logging
spellcheck_log = logging.getLogger("norm.module.spellcheck")

class Hunspell(object):
    '''
    This class contains functions that check a word with the hunspell spell checker.
    In case it is recognized as incorrectly spelled, alternative spelling options are suggested
    '''

    def __init__(self,normalizer):
        """
        **parameters**, **types**::
          :param normalizer: an object of the class Normalizer
          :type word: Normalizer object

        A hunspell object is initialized.
        """
        self.normalizer = normalizer
        super(Hunspell,self).__init__()
        #if self.language =="en":
        #    self.hobj = hunspell.HunSpell('/usr/share/myspell/en_US.dic', '/usr/share/myspell/en_US.aff')
        #elif self.language =="nl":
        #    self.hobj = hunspell.HunSpell('/usr/share/myspell/nl_NL.dic', '/usr/share/myspell/nl_NL.aff')
        #elif self.language =="de":
        #    self.hobj = hunspell.HunSpell('/usr/share/myspell/de_DE.dic', '/usr/share/myspell/de_DE.aff')
    def find_suggestions(self,word):
        '''
        use the hunspell spell checker for correct suggestions. take the first suggestion (levenshtein distance smallest).    
        
        **parameters**, **types**,**return**,**return types**::
            :param word: a token
            :type sentence: unicode string 
            :return: hunspell corrected suggestion
            :rtype: unicode string
        '''

        suggestion = self.normalizer.hobj.suggest(word.encode('utf8'))
        

        if suggestion !=[]:
            suggestion = suggestion[0]
        else:
            suggestion=""
        try:
            suggestion = suggestion.encode("utf8")
        except:
            suggestion = ""
        return suggestion

    def generate_alternatives(self,sentence,corr_list):
        '''
        Generate suggestion

        **parameters**, **types**,**return**,**return types**::
            :param sentence: flooding corrected original message
            :type sentence: unicode string 
            :param corr_list: list containing all indices of the tokens that have to be normalized (hard filtering just some, otherwise all)
            :type corr_list: list of integers
            :return: original tokens aligned with the suggestion of the form [[ori,[sug]],[ori2,[sug2]]]
            :rtype: list of lists

        '''
        spellcheck_log.info("start spell checker")
        original = sentence.split()
        words = sentence.split()
        results =[]
        for i in range(0,len(words)):
            #ignore the replacement characters
            options=""
            if self.normalizer.hobj.spell(words[i].encode("utf8")) ==False and words[i] not in [u"•",u"±",u"∞",u"™"]:
                options = self.find_suggestions(unicode(words[i]))

            if options != "" and options !=[]  and i in corr_list:
                results.append([original[i],[unicode(options).strip()]])
            else:

                results.append([original[i],[original[i]]])
                
         
        spellcheck_log.debug(results)
        spellcheck_log.info("finished spell checker")
        return results
            
