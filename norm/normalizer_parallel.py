#!/usr/bin/env python
# encoding: utf-8
import sys
import types
import multiprocessing
from multiprocessing import Pool, Queue
from modules.original import Original
from modules.smt import SMT_Token, SMT_Unigram, SMT_Bigram, SMT_Cascaded, SMT_Token2, SMT_Unigram2
from modules.spellcheck import Hunspell
from modules.readNN import NN
from modules.compound import Compound
from modules.wordsplit import Word_Split
from modules.flooding import Flooding
from modules.abbreviation import Abbreviation
from modules.new_NE import New_NE
from modules.transliterate import Transliterate
from modules.phonemic import Phonemic
from prepro.preclassification import Preclassifier
from modules.empty import Empty
from modules.text_specific_lm import LM
from data import Text
from evaluate import Evaluate
import os
import re
import util
import subprocess
import itertools
import time
import random
import xmlrpclib as x
import codecs
import hunspell
import logging
from Queue import Empty

# from modules import g2p, hunspell, orig, cascade
normalizer_log = logging.getLogger("norm.normalizer")



#wrapper function for the module specific generate_alternative calls
def call_it(queue,instance, name, args=(), kwargs=None):
   
    "indirect caller for instance methods and multiprocessing"
    if kwargs is None:
        kwargs = {}
    queue.put(getattr(instance, name)(*args, **kwargs))
    
class Normalizer(object):
    """Pipeline for text normalization

        Programm flow:
        it gets the preprocessed text
        it flooding corrects
        its sends this corrected version to the
        different modules
        it takes the output per sentence and writes to phrase table
        it starts the moses decoder with this phrase table
        it returns the normalized sentence

    
    
    """

    def __init__(self,filtering,lm_model,language, SMT_token, SMT_token2, SMT_unigram, SMT_unigram2, SMT_bigram, SMT_decision, MOSES_PATH, MOSES_SERVER, CRF_PATH, LM_PATH, SETTING, modules,dev,NNfile,KENLM,eval_dir="no_eval",**kwargs):
        """
        **parameters**, **types**::
            :param filtering: is there any filtering used: soft or hard or none
            :type filtering: string
            :param lm_model: the language model used for filtering
            :type lm_model: string (path to lm model)
            :param language: the language of the text you want to normalize, choose from 'en' and 'nl', default is 'nl'
            :type language: string 
            :param SMT_tokmodel: path to the SMT token model
            :type SMT_tokmodel: string
            :param SMT_tokmodel2: path to the second SMT token model
            :type SMT_tokmodel2: string
            :param SMT_unimodel: path to the SMT unigram model
            :type SMT_unimodel: string
            :param SMT_unimodel2: path to the second SMT unigram model
            :type SMT_unimodel2: string  
            :param SMT_bimodel: path to the SMT bigram model
            :type SMT_bimodel: string
            :param SMT_decision: path to the SMT decision model
            :type SMT_decision: string        
            :param MOSES_PATH: path to Moses executable
            :type MOSES_PATH: string
            :param MOSES_SERVER: path to Mosesserver executable
            :type MOSES_SERVER: string
            :param CRF_PATH: path to crf_test executable
            :type CRF_PATH: string
            :param LM_PATH: path to language model
            :type LM_PATH: string
            :param SETTING: train setting you want to use: for english: bal, ask, twe, unb, you. for dutch: bal, unb, sms, sns, twe
            :type SETTING: string
            :param modules: the modules used for normalization
            :type modules: list of strings
            :param dev: is it a development run in which phrase tables should not be deleted?
            :type dev: boolean
            :type NNfile: string that points to a file where there are results from the NN for each of the lines
            :param eval_dir: keyword argument. Path to directory to which all evaluation files are written
            :type eval_dir: string



        A hunspell object is initialized
        The modules are initialized
        """

        super(Normalizer, self).__init__()
        self.sentcount=0
        if eval_dir != "no_eval":
            self.eval = True
            self.e = Evaluate(self,eval_dir)
        else:
            self.eval = False
        self.dev = dev
        print self.eval

        self.language = language    
        if self.language =="en":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/en_US.dic', '/usr/share/myspell/en_US.aff')
        elif self.language =="nl":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/nl_NL.dic', '/usr/share/myspell/nl_NL.aff')
        elif self.language =="de":
            self.hobj = hunspell.HunSpell('/usr/share/myspell/de_DE.dic', '/usr/share/myspell/de_DE.aff')
        self.filtering = filtering
        if self.filtering in ["hard","soft"]:
            if self.language == "nl":
                lm_file = codecs.open(lm_model+"lm.nl",'r',encoding='utf-8')
            elif self.language =="en":
                lm_file = codecs.open(lm_model+"lm.en",'r',encoding='utf-8')
            elif self.language =="de":
                lm_file = codecs.open(lm_model,'r',encoding='utf-8')
            self.lm = set(lm_file.read().splitlines())
        self.SMT_tokmodel = SMT_token
        self.SMT_tokmodel2 = SMT_token2
        self.SMT_unimodel = SMT_unigram
        self.SMT_unimodel2 = SMT_unigram2
        self.SMT_bimodel = SMT_bigram
        self.SMT_decision = SMT_decision
        self.MOSES_PATH = MOSES_PATH
        self.MOSES_SERVER= MOSES_SERVER
        self.CRF_PATH = CRF_PATH
        self.LM_PATH = LM_PATH
        self.SETTING = SETTING 
        self.ori_tgt_map =[]
        self.NNfile=codecs.open(NNfile,'r','utf8').readlines()
        self.initialize_modules(modules)
        self.modules1 = modules
        #hard filter list
        self.correction_list=[]
        #soft filter list
        self.soft_list=[]
        #accounts for diff number of features in case of soft filtering (1 for hunspell)
        if self.filtering == "soft":
            #NE is added dynamically if called (the two are PRE and hsfeature)
            self.feature_increase = 2
        else:
            self.feature_increase = 1
        self.entire_text = ''
        self.seclm=''
        self.KENLM_PATH=KENLM
        self.res_decision=[]
        self.result_untokenized=[]
        self.pids=[]
        
    def normalize_text(self,t,csv_sent):
        """
        returns the normalized sentences in a list

        the preprocessed text is first flooding corrected
        then the messages are sent into the pipeline and the normalized sentence is returned

         **parameters**, **types**,**return**,**return types**::
            :param t: object from class Text, containing the original and the preprocessed string 
            :type t: Text object
            :param csv_sent: gold standard sentence in case of normalization, otherwise empty
            :type csv_sent: dictionary
            :return: return normalized sentences
            :rtype: list of strings
        """        
        assert isinstance(t, Text)
        self.csv_sent = csv_sent
        #in case you run in evaluation mode

        if self.eval:
            t.text_prepro = self.e.realign_goldstandard(t.text_orig)

        #flood = Flooding(self)
        #flood_cor = flood.flooding_correct(t.text_prepro)
        normalizer_log.info("run normalization")
        norm_sentences=[]
        #if hard filtering is turned on
        self.correction_list=[]

        if self.filtering == "hard":
            p = Preclassifier(self)
            self.correction_list = p.hard_filtering(self,t.text_prepro)

        else:
            for i in range(0,len(t.text_prepro.split())):
                self.correction_list.append(i)
                        
            if self.filtering =="soft":

                self.p = Preclassifier(self)
                l = self.p.hard_filtering(self,t.text_prepro)
                for i in l:
                    self.soft_list.append(t.text_prepro.split()[i]) 
        
        norm_sentences.append(self._normalize_sentence(t.text_prepro,t.text_orig))
    
        #norm_sentences.append(self._normalize_sentence(flood_cor))
        normalizer_log.info("normalizer finished")
            
        return norm_sentences
            
    def init_lm(self,text):
        for mod in self.modules:
            if isinstance(mod,LM):
                self.seclm=mod.make_lm(text)
        
    
    def start_server_mode(self):
        """
        start Moses server mode for all three SMT systems

        the SMT modules use the Moses server mode which is started in the beginning of 
        one run for each of the three modes: Token, Unigram and Bigram. They run on a random 
        port between 30000 and 40000. The pids are stored and the server mode is stopped in case of
        error or sucessful finish. Each Moses server waits for a certain amount of seconds after      start up to ensure it has enough time to run properly in the background.
        The server modes use the .ini files which are located in ../static/Moses/decoder_files. In         the ini files themselves you can see which phrase table or language model is accessed.
         """
        pids=[]
        logfile = util.logfile
        os.system('export LC_ALL="C"')
        print self.modules1
        
        
        if u'SMT_Token' in self.modules1 or u'SMT_Cascaded' in self.modules1:
            normalizer_log.info("start token server mode")
            log = open(logfile,"a")
            port_tok= str(random.randint(40000, 50000))
            print self.MOSES_SERVER+" -f "+self.SMT_tokmodel +" --server-port "+ port_tok +" --server-log "+util.LOG_DIR+"/server/moses_server_token.log"
            p1 = subprocess.Popen(self.MOSES_SERVER+" -f "+self.SMT_tokmodel +" --server-port "+ port_tok +" --server-log "+util.LOG_DIR+"/server/moses_server_token.log",stdout=log,stderr=subprocess.PIPE,shell=True,bufsize=0,env={"LD_LIBRARY_PATH":"/mount/projekte/sfb-732/inf/users/sarah/tools/xmlrpc-c/lib"},universal_newlines=True)
            
            log.close()
            
            pids.append(p1)
            elapsed_time=0
            start_time = time.time()

           
            err=''
            out=''
            for line in iter(p1.stderr.readline, ''):

                if "Listening on port" in line or elapsed_time > 150:
                    print "loaded tok1"
                    break
                elapsed_time = time.time() - start_time
            
            if elapsed_time >= 150:
                print "SMT Token Server Modes doesn't start."
                sys.exit()
            self.s_token = x.ServerProxy("http://localhost:"+port_tok+"/RPC2",allow_none=True)

        if u'SMT_Token2' in self.modules1:
            normalizer_log.info("start token2 server mode")
            log = open(logfile,"a")
            port_tok2= str(random.randint(40000, 50000))
            print self.MOSES_SERVER+" -f "+self.SMT_tokmodel +" --server-port "+ port_tok2 +" --server-log "+util.LOG_DIR+"/server/moses_server_token2.log"
            p2 = subprocess.Popen(self.MOSES_SERVER+" -f "+self.SMT_tokmodel2 +" --server-port "+ port_tok2 +" --server-log "+util.LOG_DIR+"/server/moses_server_token2.log",stdout=log,stderr=subprocess.PIPE,shell=True,env={"LD_LIBRARY_PATH":"/mount/projekte/sfb-732/inf/users/sarah/tools/xmlrpc-c/lib"})
            log.close()
            pids.append(p2)
            start_time = time.time()
            
            elapsed_time=0
            start_time = time.time()
           
            err=''
            out=''
            for line in iter(p2.stderr.readline, ''):

                if "Listening on port" in line or elapsed_time > 150:
                    print "loaded tok2"
                    break
                elapsed_time = time.time() - start_time
            
            if elapsed_time >= 150:
                print "SMT TokenDTA Server Mode doesn't start."
                sys.exit()
            self.s_token2 = x.ServerProxy("http://localhost:"+port_tok2+"/RPC2",allow_none=True)
            

            
        if u'SMT_Unigram' in self.modules1 or u'SMT_Cascaded' in self.modules1:
            normalizer_log.info("start unigram server mode")
            log = open(logfile,"a")
            port_uni= str(random.randint(40000, 50000))
            p3 = subprocess.Popen(self.MOSES_SERVER+" -f "+ self.SMT_unimodel+" --server-port "+ port_uni +" --server-log "+util.LOG_DIR+"/server/moses_server_unigram.log",stdout= log,stderr=subprocess.PIPE,shell=True,env={"LD_LIBRARY_PATH":"/mount/projekte/sfb-732/inf/users/sarah/tools/xmlrpc-c/lib"})
            log.close()
            pids.append(p3)
            elapsed_time=0
            start_time = time.time()
           
            err=''
            out=''
            for line in iter(p3.stderr.readline, ''):

                if "Listening on port" in line or elapsed_time > 150:
                    print "loaded uni1"
                    break
                    
                elapsed_time = time.time() - start_time
            
            if elapsed_time >= 150:
                print "SMT Unigram Server Mode doesn't start."
                sys.exit()
            self.s_unigram = x.ServerProxy("http://localhost:"+port_uni+"/RPC2",allow_none=True)                
            
        if u'SMT_Unigram2' in self.modules1:

            normalizer_log.info("start unigram2 server mode")
            log = open(logfile,"a")
            port_uni2= str(random.randint(40000, 50000))
            p4 = subprocess.Popen(self.MOSES_SERVER+" -f "+ self.SMT_unimodel2+" --server-port "+ port_uni2 +" --server-log "+util.LOG_DIR+"/server/moses_server_unigram2.log",stdout= log,stderr=subprocess.PIPE,shell=True,env={"LD_LIBRARY_PATH":"/mount/projekte/sfb-732/inf/users/sarah/tools/xmlrpc-c/lib"})
            log.close()

            pids.append(p4)
            elapsed_time=0
            start_time = time.time()
           
            err=''
            out=''
            for line in iter(p4.stderr.readline, ''):

                if "Listening on port" in line or elapsed_time > 250:
                    print "loaded uni2"
                    break
                elapsed_time = time.time() - start_time
            
            if elapsed_time >= 150:
                print "SMT Unigram DTA Server Mode doesn't start."
                sys.exit()
            self.s_unigram2 = x.ServerProxy("http://localhost:"+port_uni2+"/RPC2",allow_none=True)     
                       
        if u'SMT_Bigram' in self.modules1:
            normalizer_log.info("start bigram server mode")
            log = open(logfile,"a")
            port_bi=str(random.randint(40000, 50000))
            p5 = subprocess.Popen(self.MOSES_SERVER+" -f "+self.SMT_bimodel +" --server-port "+ port_bi +" --server-log "+util.LOG_DIR+"/server/moses_server_bigram.log",stdout= log,stderr=log,shell=True,env={"LD_LIBRARY_PATH":"/mount/projekte/sfb-732/inf/users/sarah/tools/xmlrpc-c/lib"})
            log.close()
            #p5.communicate()
            pids.append(p5)
            time.sleep(15)
            self.s_bigram = x.ServerProxy("http://localhost:"+port_bi+"/RPC2",allow_none=True)
                        
        self.pids=pids
        return pids
    
    def initialize_modules(self, mods):
        """
        initialize the different module objects

        The module objects are initialized onces for every normalization run. The 
        order of the initialization is important since this order is the same as the 
        weights for the modules in the ini files. 

        For English there are 10 modules:

        Word_Split, Compound, Original, Abbreviation, SMT_Token, SMT_Unigram, SMT_Bigram, SMT_Cascaded, Transliterate, Hunspell

        For Dutch there are 11 modules:

        Word_Split, Compound, Phonemic, Original, Abbreviation, SMT_Token, SMT_Unigram, SMT_Bigram, SMT_Cascaded, Transliterate, Hunspell
        """

          
        self.modules =[]
        #make an object out of strings in input list
        for m in mods:
            cmd = "mod = %s(self)" % m

            exec cmd
            self.modules.append(mod)
        if self.filtering =="soft":
            self.modules.insert(0,New_NE(self))
        if self.eval:
            self.e.open_cer_log()

            
    def _kill_server_mode(self,proc):
        """
        kill Moses server mode with the help of the process id.

        **parameters**, **types**::
            :param proc: the process ideas collected when starting up server modes
            :type proc: list of integers    
        
        forces the kill of all running processes with the respective process id
        """

        for p in proc:
            id1 = p.pid
            os.kill(id1,9)


    def _normalize_sentence(self, sentence,ori_sentence):
        """
        normalize the message, running all modueles and combining their output

        **parameters**, **types**,**return**,**return types**::
            :param sentence: preprocessed and flooding corrected text message
            :type sentence: unicode string
            :param ori_sentence: orginial untokenized text message
            :type Ori_sentence: unicode string
            :return: return normalized sentences
            :rtype: list of strings    

        first all modules generate their suggestion, then these suggestions are collected
        and written out to a phrase table, then the decision module generates one normalized         sentence
        """        
        phrase_dict = {}
        
        self.ori_sug_map={}
   

        
        #here we go async
        
        #generate suggestions per options
        outputs_system=[]
        #pool = Pool(processes=len(self.modules))
        print self.modules
        #outputs_system = [pool.apply_async(call_it,
            #args = (m, 'generate_alternatives', (sentence,self.correction_list,))) for m in self.modules]
            
        queue=[]
        processes=[]
        for m in self.modules:
            queue.append(Queue())
            p=multiprocessing.Process(
                target=call_it,
                args=(queue[-1],m,'generate_alternatives', (sentence,self.correction_list,)),
                name=str(m),
            )
            p.start()
            time.sleep(0.0001)
            processes.append(p)
        #print "joining processes"
        #for i,p in enumerate(processes):
        #    p.join(timeout=60)
            
        print "processes joined"
        outputs_system=[]
        print "getting results"
        for q in queue:
            try:
                outp=q.get(timeout=600)
                outputs_system.append(outp)
            except Empty:
                print "excepted Empty"
                orires=[]
                for w in sentence.split():
                    orires.append([w,[w]])
                outputs_system.append(orires)

        print "got results"
  
        #for m in self.modules:
        #    print 'ADDING ASYNC FOR MODULE ' + str(m) + ' of size ' + str(sys.getsizeof(m))
        #    outputs_system.append(pool.apply_async(call_it,args= (m,'generate_alternatives', (sentence,self.correction_list,))))
            #outputs_system.append(pool.apply_async(call_it2, (20,)))
        #print outputs_system
        #pool.close()
        #pool.join()
        #time.sleep(20)
       
        #print outputs_system
        #map(multiprocessing.pool.ApplyResult.wait, outputs_system)
        #print "outsys after wait"
        #for o in outputs_system:
        #    print o.ready()
        #    print o.successful()
        #    print o._cond
        #    print o._job
        #    print o._cache
        #    print o._callback
        #    print o.get()
        #pool.close()    
        #print outputs_system
        #here we come back sync
        #outputs_system = [r.get() for r in outputs_system]
        
        for i,m in enumerate(self.modules):
            print m
            output_system= outputs_system[i]
            print m
            
            print output_system
            sug=[]        
            [sug.append(x[1][0]) for x in output_system]
            print ' '.join(sug)
            print '\n'
            if self.eval: 
                self.e._append_cer(self.csv_sent,output_system,m,"tgt")
                self.e.evaluate(output_system,self.csv_sent,m,"ori","tgt")
                normalizer_log.debug(m)
                normalizer_log.debug(output_system)

            for num,item in enumerate(output_system):
                ori,alternatives = item

                for alt in alternatives:
                    found_alt=[]
                    for key in phrase_dict:
                        if key.rstrip("1234567890") ==alt.strip():
                            found_alt.append(key)
                    if len(found_alt)>0:
                        alreadyin=""
                        for a in found_alt:
                            if phrase_dict[a]["ori"][0] == ori.strip():
                                alreadyin=a
                                break
                        if alreadyin!='':
                                phrase_dict[alreadyin]["module"].append(m)
                        else:
                            rint=random.randint(1,1000)
                            phrase_dict[alt.strip()+str(rint)]={"module":[],"ori":[ori.strip()]}
                            phrase_dict[alt.strip()+str(rint)]["module"].append(m)
                                
                    else:

                        phrase_dict[alt.strip()]={"module":[],"ori":[ori.strip()]}
                        phrase_dict[alt.strip()]["module"].append(m)

                    #elif ori.strip() not in phrase_dict[alt.strip()]["ori"]:
                     #   phrase_dict[alt.strip()+]["ori"].append(ori.strip())
                    #if m not in phrase_dict[alt.strip()]["module"]:
                    #    phrase_dict[alt.strip()]["module"].append(m)
                       
                    for o in ori.split():

                        if o in self.ori_sug_map:

                            self.ori_sug_map[o].append(alternatives[0])
                        else:
                       

                            self.ori_sug_map[o]=[alternatives[0]]
                            

        phrase_table_path = util.get_random_phrase_table_path(prefix = "phrase_table")
        self._write_phrase_table(phrase_dict, phrase_table_path)
            
        print "phrase table written"
        self.res_decision,normalized_sentence = self._call_moses(sentence, phrase_table_path)
        self.result_untokenized= util.align(ori_sentence,unicode(normalized_sentence, 'utf-8'))
        normalized_sentence= unicode(normalized_sentence, 'utf-8')
        if self.eval:
            print "logging values for decision module"
            print self.res_decision
            self.e._append_cer(self.csv_sent,self.res_decision,"decision","tgt")
            self.e.evaluate(self.res_decision, self.csv_sent, "decision","ori","tgt")
        print "sent  normalized"
        return normalized_sentence.strip()
           
                
        
    def _write_phrase_table(self, phrase_dict, phrase_dict_location):
        """
        write out the phrase table for the run of the decision module

        **parameters**, **types**::
            :param phrase_dict: a dictionary holding all suggestions, with the information of the modules that suggested it and the original token
            :type phrase_dict: dictionary
            :param phrase_dict_location: the path to the phrase table
            :type phrase_dict_location: string
        """
            
        print "writing...."
        fout = codecs.open(phrase_dict_location, "w", "utf8")
        fout.writelines(self._generate_phrase_table(phrase_dict))
        fout.close()
        
    def _generate_phrase_table(self, phrase_dict):
        """
        generate the per line entry of a phrase table

        **parameters**, **types**::
            :param phrase_dict: a dictionary holding all suggestions, with the information of the modules that suggested it and the original token
            :type phrase_dict: dictionary


        iterate over the phrase_dict and compile an etry of the followng format for each 
        suggestion
    
        ori ||| sug ||| 0 1 0 1 0 1 ....

        the 0 and 1 indicate which module returned the suggestion. The order of the modules is 
        given my the initialization of the modules.
        The last 0 or 1 says if hunspell can find the suggestion as a word or not.
        """
        if self.eval:
            self.e.evaluate_overall(self.ori_sug_map)
        
        #add info about filtering to phrase_dict        
        if self.filtering =="soft":
        
            phrase_dict = self.p.soft_filtering(self.soft_list,phrase_dict,self.ori_sug_map)

        for alternative in phrase_dict.iteritems():
            # in case you want to use empty module, you have to comment this out    
            if alternative[1] =="":
                continue
            modules=""
            hs_feature=0
            if util.check_hunspell(self,alternative[0]): 
                hs_feature=1
                        
                
            for i,ori in enumerate(alternative[1]["ori"]):
                #skip the NE char
                if alternative[0].rstrip("1234567890")!=u"ਊ" :
                   
                    for mod in self.modules:
                        if not isinstance(mod,New_NE):#never return the NE char as sugg
                            if mod in alternative[1]["module"]:
                                modules = modules + str(1)+ " "
                        
                            else:
                                modules = modules + str(0)+ " "
                        
                    #compile the filter features if turned on        
                    if self.filtering=="soft":
                        if "NE" in alternative[1]["module"]:
                            modules = modules + str(1)+ " "
                        else: 
                            modules = modules + str(0)+ " "
                        if "PRE" in alternative[1]["module"]:
                            modules = modules + str(1) +" "
                        else: 
                            modules = modules + str(0)+" "
                    modules = modules.strip() +" "+ str(hs_feature)
                    #enables an analysis on how many unique correct answers a module gives (encoded in the phrase table)
                    if self.eval:
                    #    #if alternative is correct
                    #    if True in [True for el in self.ori_tgt_map if alternative[0].rstrip("1234567890") == el[1][0].strip() and el[0].strip() ==alternative[1]["ori"][i].strip()]:

                    #        modules = modules +" "+str("correct")
                        #if alternative is incorrect
                    #    else:
                    #        modules = modules +" "+str("incorrect")
                        yield u"%s ||| %s ||| %s\n" % (alternative[1]["ori"][i], alternative[0].rstrip("1234567890"),modules)
                    else:
                        yield u"%s ||| %s ||| %s\n" % (alternative[1]["ori"][i], alternative[0].rstrip("1234567890"),modules)


    def _call_moses(self, s, phrase_table):
        """
        decide for a combination of suggestions

        **parameters**, **types**,**return**,**return types**::
            :param s: is the original message that has also been forwarded to the modules 
            :type s: unicode string
            :param phrase_table: is the path to the phrase table
            :type phrase_table: string
            :return: return normalized sentences
            :rtype: string    


        Moses is called including the phrase table that has been generated from the suggestions.
        Using a language model and the phrase table with its features, Moses translates the original sentence into the normalized sentence.
        """

        normalizer_log.info("start decision module")
        logfile = util.logfile
        log = open(logfile,"a")
        echo = subprocess.Popen(['echo',s.encode("utf8")],stdout=subprocess.PIPE)
        if "LM" in self.modules1:
            proc = subprocess.Popen([self.MOSES_PATH,'-v','2', '-f', self.SMT_decision, '-ttable-file', '0 0 0 '+str(len(self.modules)+self.feature_increase)+' ' + phrase_table, '-lmodel-file', '8 0 5 ' + self.LM_PATH, '8 0 5 ' + self.seclm],stdin = echo.stdout, stdout= subprocess.PIPE, stderr= subprocess.PIPE,shell=False)
        else:
            proc = subprocess.Popen([self.MOSES_PATH,'-v','2', '-f', self.SMT_decision, '-ttable-file', '0 0 0 '+str(len(self.modules)+self.feature_increase)+' ' + phrase_table, '-lmodel-file', '8 0 5 ' + self.LM_PATH],stdin = echo.stdout, stdout= subprocess.PIPE, stderr= subprocess.PIPE,shell=False)
    
        out,err = proc.communicate()

        align_text = re.findall("Source and Target Units:.*]",err)

        try: alignments= re.findall("\[\[(\d+)\.\.(\d+)\]:(.*?)(?= :: c)",align_text[0])
        except IndexError:
            raise
           
        input_tokens = s.split()

        result_list=[]
       
        
        result_list= util.align(s,unicode(out, 'utf-8'))
            #for el in alignments:
            #    result_list.append([" ".join(input_tokens[int(el[0]):int(el[1])+1]), [unicode(el[2].strip(),"utf8")]])
            #normalizer_log.debug("debug decisionmod")
            #normalizer_log.debug(result_list)
        log.close()
        
        if self.dev == "False":

            os.system("rm "+phrase_table)
        normalizer_log.info("finished decision module")
        
        return result_list,out
    
   
        
        

