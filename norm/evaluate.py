#!/usr/bin/env python
# encoding: utf-8
import sys
import os
import util
import types
from modules.original import Original
from modules.new_NE import New_NE
from prepro.rewrite import Rewrite 
from modules.flooding import Flooding
import codecs
import itertools
import re
import difflib

class Evaluate(object):
    """
    This class contains functions to evaluate the 
    performance of modules and the overall sytem
    The evaluation is based on the gold standard annotations read it from the csv files
    
    """

    def __init__(self,normalizer,eval_dir):
        """
        **parameters**, **types**::
            :param normalizer: an object used to pass certain variables
            :type normalizer: Normalizer object
            :param eval_dir: Path to directory to which all evaluation files are written
            :type eval_dir: string
        """
        super(Evaluate, self).__init__()
        self.normalizer = normalizer
        self.eval_dir = eval_dir
        self.m_log_list={}
        self.m_log_recall_precision={}
        self.m_wer_values={}
        self.m_cer_list={}
        self.token_log={}
        self.correction_list=[]
        self.pre_class_list={}
        self.tokens_found=0
        self.precision=0.0
        self.recall=0.0
        self.suggestions_overall=0
        self.not_found=0
        self.m_wer_list={}
        self.m_wer_list2={}
        self.D=0.0
        self.I=0.0
        self.S=0.0
        self.N=0.0
        self.N_tgt=0.0

    def realign_goldstandard(self,t):
        """
        recompile the evaluation dict which contains the tok, ori and tgt version.
            
        Evaluate flooding correction and preprocessing
            
        **parameters**, **types**::
             :param t: contains ori and prepro text
             :type t: Text object
            
        """

        tok_clean=[]
        tgt_clean=[]
        ori_clean=[]
        act_count=0

        
        self.N_tgt= float(len(self.normalizer.csv_sent))
       

        #original and tgt are aligned, this list is later used to calculate the overall numbers
        self.ori_tgt_map=[]

        self.ori_tgt_map =util.align(t,self.normalizer.csv_sent)
           
        return t   
            
    def evaluate(self,output_system,csv_sent,m,dep,aim):
        
        """
            Evalutation for each module
            
            
            **parameters**, **types**::
                :param output_system: the output of every module ori-> sug
                :type output_system: list of lists
                :param csv_sent: the gold standard dict
                :type csv_sent: dictionary
                :param output_system: module name
                :type output_system: string or identifier of object
                :param ori_sug_map: dictionary to be filled further with ori/sug pairs
                :type ori_sug_map: dictionary
                :param dep: indicates the csv_dicts list to be used, departure
                :type dep: string (ori, tok)
                :param aim: indicates the csv_dicts list to be used, aim
                :type aim: string (tok,tgt)
            
        """
        pred =''
        ori=''
        for i in output_system:
            pred += i[1][0]+' '
            ori+=i[0]+' '
        
        aligned_pred_tgt=util.align(csv_sent.strip(),pred.strip())
        aligned_ori_tgt=util.align(csv_sent.strip(),ori.strip())

        
        i=0                                                          
        orii=0                                                       
        while i< len(aligned_pred_tgt) and orii<len(aligned_ori_tgt):
            print "problem 1 eval"
            t1=aligned_pred_tgt[i][0].strip()                                
            t2=aligned_ori_tgt[orii][0].strip()                              
            a=aligned_pred_tgt[i][1][0]                              
            o=aligned_ori_tgt[orii][1][0]                            
            if t1==t2:                                               
                t = t1                                         
            elif len(t1.split()) < len(t2.split()):                  
                                                                     
                while t1!=t2 and len(t1.split())<len(t2.split()) and i< len(aligned_pred_tgt)-1 and orii<len(aligned_ori_tgt)-1:    
                    print "problem 2 eval"
                    i+=1                                             
                    t1+=' '+aligned_pred_tgt[i][0]                   
                    a+=' '+aligned_pred_tgt[i][1][0]                 
                if len(t1.split())> len(t2.split()):                 
                    while t1!=t2 and len(t1.split())>len(t2.split()) and i< len(aligned_pred_tgt)-1 and orii<len(aligned_ori_tgt)-1:
                        print "problem 3 eval"
                        orii+=1                                      
                        t2+=' '+aligned_ori_tgt[orii][0]             
                        o+=' '+aligned_ori_tgt[orii][1][0]           
                t= t1                                             
                a = a                                             
                o= o                                              
            #cases like ori_tgt =["Wer                                                
            elif len(t2.split()) < len(t1.split()):
                                  
                while t1!=t2 and len(t2.split())<len(t1.split()) and i< len(aligned_pred_tgt)-1 and orii<len(aligned_ori_tgt)-1:
                    print "problem 4 eval"     
                    orii+=1                                          
                    t2+=' '+aligned_ori_tgt[orii][0]                 
                    o+=' '+aligned_ori_tgt[orii][1][0]               
                if len(t2.split())> len(t1.split()):                 
                    while t1!=t2 and len(t2.split())>len(t1.split())and  i< len(aligned_pred_tgt)-1 and orii<len(aligned_ori_tgt)-1:
                        print "problem 5 eval"
                        i+=1                                         
                        t1+=' '+aligned_pred_tgt[i][0]               
                        a+=' '+aligned_pred_tgt[i][1][0]             
                t= t1                                             
                o= o                                              
                a= a 
            else:
                t = t1
            self._log_sugg_per_module(a,o,t, m)
            i+=1                                                     
            orii+=1  
        




    def _open_log_for_each_module(self):
        """
            
            Open log lists for all modules
                        
           """
        for m in self.normalizer.modules:
            self.m_wer_list2[m]={"I":0,"D":0,"S":0,"N":0}
            self.m_wer_values[m]=[]
            self.token_log[m]={"corrected":[],"not_found":[],"over_corrected":[]}
            self.m_log_recall_precision[m]={"corrected":0,"not_corrected":0,"nothing_to_correct":0,"tokens_overall":0,"num_sugg":0,"over_correction":0,"pre":0.0,"rec":0.0}
            self.m_log_list[m] =codecs.open(self.eval_dir+"/module_log_"+str(m),"a","utf8")
        self.m_log_list["decision"]=codecs.open(self.eval_dir+"/module_log_decision","a","utf8")
        self.m_wer_list2["decision"]={"I":0,"D":0,"S":0,"N":0}
        self.m_wer_values["decision"]=[]
        self.token_log["decision"]={"corrected":[],"not_found":[],"over_corrected":[]}
        self.m_log_recall_precision["decision"]={"corrected":0,"not_corrected":0,"nothing_to_correct":0,"tokens_overall":0,"num_sugg":0,"over_correction":0,"pre":0.0,"rec":0.0}
        if self.normalizer.filtering in ["hard","soft"]:
            self.token_log["preclass"]={"corrected":[],"not_found":[],"over_corrected":[]}
            self.m_log_recall_precision["preclass"]={"corrected":0,"not_corrected":0,"nothing_to_correct":0,"tokens_overall":0,"num_sugg":0,"over_correction":0,"pre":0.0,"rec":0.0}
            self.m_log_list["preclass"] =codecs.open(self.eval_dir+"/module_log_"+str("preclassification"),"a","utf8")
            self.m_wer_list2["preclass"]={"I":0,"D":0,"S":0,"N":0}
        #self.token_log["prepro_module"]={"corrected":[],"not_found":[],"over_corrected":[]}
        #self.m_wer_list2["prepro_module"]={"I":0,"D":0,"S":0,"N":0}
        #self.m_wer_values["prepro_module"]=[]
        #self.m_log_recall_precision["prepro_module"]={"corrected":0,"not_corrected":0,"nothing_to_correct":0,"tokens_overall":0,"num_sugg":0,"over_correction":0,"pre":0.0,"rec":0.0}
        #self.m_log_list["prepro_module"] =codecs.open(self.eval_dir+"/module_log_"+str("preclassification"),"a","utf8")
        #self.token_log["flooding"]={"corrected":[],"not_found":[],"over_corrected":[]}
        #self.m_wer_list2["flooding"]={"I":0,"D":0,"S":0,"N":0}
        #self.m_wer_values["flooding"]=[]
        #self.m_log_recall_precision["flooding"]={"corrected":0,"not_corrected":0,"nothing_to_correct":0,"tokens_overall":0,"num_sugg":0,"over_correction":0,"pre":0.0,"rec":0.0}
        #self.m_log_list["flooding"] =codecs.open(self.eval_dir+"/module_log_"+str("preclassification"),"a","utf8")
            
            
    def write_out_match_num_modules(self):
        """
            
            calculate precision and recall and write overcorr, corr and not corr tokens out to module log files
                        
           """

        print self.m_log_recall_precision
        for el in self.m_log_recall_precision:
            if isinstance(el,Original):
                for mod in self.m_log_recall_precision:
                    self.m_log_recall_precision[mod]["nothing_to_correct"] = self.m_log_recall_precision[el]["nothing_to_correct"]

            break
        for m in self.m_log_recall_precision:
            self.m_log_list[m] =codecs.open(self.eval_dir+"/module_log_"+str(m),"a","utf8")

            if m =="preclass":
                pre = float(self.m_log_recall_precision[m]["corrected"]+self.m_log_recall_precision[m]["nothing_to_correct"])/float(self.m_log_recall_precision[m]["num_sugg"])
                rec= float(self.m_log_recall_precision[m]["corrected"]+self.m_log_recall_precision[m]["nothing_to_correct"])/float(self.m_log_recall_precision[m]["tokens_overall"])
                self.m_log_list[m].write("\n\n\n")
            else:
                print m    
                pre = (float(self.m_log_recall_precision[m]["corrected"]+self.m_log_recall_precision[m]["nothing_to_correct"]-self.m_log_recall_precision[m]["over_correction"]))/float(self.m_log_recall_precision[m]["num_sugg"])
                rec= (float(self.m_log_recall_precision[m]["corrected"]+self.m_log_recall_precision[m]["nothing_to_correct"]-self.m_log_recall_precision[m]["over_correction"]))/float(self.m_wer_list2[m]["N"])
            
            self.m_log_recall_precision[m]["pre"]=pre
            self.m_log_recall_precision[m]["rec"]=rec
            
            self.m_log_list[m].write("\n\n\n")
            
            self.m_log_list[m].write("The following tokens could be corrected: \n")
            [self.m_log_list[m].write(y+"\n") for y in self.token_log[m]["corrected"]]
            self.m_log_list[m].write("The following tokens have been over corrected: \n")
            [self.m_log_list[m].write(y+"\n") for y in self.token_log[m]["over_corrected"]]
            self.m_log_list[m].write("The following tokens could NOT be corrected: \n")
            [self.m_log_list[m].write(y+"\n") for y in self.token_log[m]["not_found"]]
            self.m_log_list[m].write("Corrected: "+ str(self.m_log_recall_precision[m]["corrected"]) +"\n")
            self.m_log_list[m].write("Not_corrected: "+ str(self.m_log_recall_precision[m]["not_corrected"]) +"\n")
            self.m_log_list[m].write("The module over corrected: "+ str(self.m_log_recall_precision[m]["over_correction"]))
            self.m_log_list[m].write("Nothing_to_change: "+ str(self.m_log_recall_precision[m]["nothing_to_correct"]) +"\n")
            self.m_log_list[m].write("Tokens overall: "+ str(self.m_wer_list2[m]["N"]) +"\n")
            self.m_log_list[m].write("Precision: "+ str(pre) +"\n")
            self.m_log_list[m].write("Recall: "+ str(rec) +"\n")
            if m !="preclass":
                self.m_log_list[m].write("Number tokens in reference: "+str(self.m_wer_list2[m]["N"])+"\n")
            self.m_log_list[m].write("num sugg all: "+ str(self.m_log_recall_precision[m]["num_sugg"]) +"\n")

            self.m_log_list[m].close()
        overallperf = open(self.eval_dir+"/overall_numbers","w")
        overallperf.write("From "+str(self.m_wer_list2[m]["N"])+" tokens \n there has been found "+str(self.tokens_found)+"\n "+str( self.suggestions_overall)+" suggestions have been generated.\n "+str(self.not_found)+" tokens have not been corrected.")
        self.precision= float(self.tokens_found)/float(self.suggestions_overall)
        self.recall= float(self.tokens_found)/(self.m_wer_list2[m]["N"])
        overallperf.write("This results in recall: "+str(self.recall)+" \n")
        overallperf.write("This results in precision: "+str(self.precision)+" \n")

        overallperf.close()

        #open lists that can hold cer and wer values for each sentence        
    def open_cer_log(self):
        """
            
            Open cer log lists for all modules.
                        
           """
    
        for m in self.normalizer.modules:
            self.m_wer_list[m]={"deletion":0,"insertion":0,"replace":0,"n":0}
            self.m_cer_list[m] ={"deletion":0,"insertion":0,"replace":0,"n":0}
        #self.m_wer_list["before_prepro"]={"deletion":0,"insertion":0,"replace":0,"n":0}
        #self.m_wer_list["floodingmodule"]={"deletion":0,"insertion":0,"replace":0,"n":0} 
        #self.m_wer_list["beforeflood"] = {"deletion":0,"insertion":0,"replace":0,"n":0}
        self.m_wer_list["decision"] = {"deletion":0,"insertion":0,"replace":0,"n":0}
        #self.m_cer_list["before_prepro"]={"deletion":0,"insertion":0,"replace":0,"n":0}
        #self.m_cer_list["floodingmodule"]={"deletion":0,"insertion":0,"replace":0,"n":0}    
        #self.m_cer_list["beforeflood"] = {"deletion":0,"insertion":0,"replace":0,"n":0}
        self.m_cer_list["decision"] = {"deletion":0,"insertion":0,"replace":0,"n":0}
    
    def _close_log_for_each_module(self):
        """
            
            Close log files for all modules.
                        
           """
        #close all the log files
        for m in self.m_log_list:
            self.m_log_list[m].close()

    #calculate CER and WER with dynamic alignment and save one value per sentence
    def _append_cer(self,csv,hyp,mod,aim):
        """
            
            calculate CER/WER dynamic.
            
            **parameters**, **types**::
                :param csv: gold standard dict
                :type csv: dictionary
                :param hyp: hypothesis sentence
                :type hyp: unicode string or list
                :param mod: the module to evaluate
                :type: string or object name
                :param aim: the gold standard to be used tok or tgt
                :type: string            
           """
        
        #evaluate flooding and prepro and so on
        if type(hyp) is not types.UnicodeType:
            pred =''
            for i in hyp:
                pred += i[1][0]+' '
            hyp = pred.strip()
             
        ref = csv.strip()
        hyp = hyp.replace("<NEWLINE>","").replace(u"<com>","").strip()
        dele,ins,rep= util.calculate_cer(ref.lower(),hyp.lower())
        self.m_cer_list[mod]["deletion"]+=dele
        self.m_cer_list[mod]["replace"]+=rep
        self.m_cer_list[mod]["insertion"]+=ins
        self.m_cer_list[mod]["n"]+=len(ref)
        dele,ins,rep= util.calculate_cer(ref.lower().split(),hyp.lower().split())
        self.m_wer_list[mod]["deletion"]+=dele
        self.m_wer_list[mod]["replace"]+=rep
        self.m_wer_list[mod]["insertion"]+=ins
        self.m_wer_list[mod]["n"]+=len(ref.split())
        #evaluate the modules with list of list output
        #else:
        #    print mod
        #    sys.exit()  
        #    if hyp != []:

        #        cers=0.0
        #        wers=0.0
        #        maxi=0
              
        #    target=csv.split()
            
            #eval ne    
            
            #make the gold standard reference            
        #    ref = csv
            
            #this allows to calculate the "best" sentence in case you have more alternatives
        #    for b in itertools.product(*[a[1] for a in hyp]):
        #    
        #        maxi+=1
        #        if maxi > 100:
        #            break

                
                #calculate with dynamic alignment
         #       c = float(util.calculate_cer(ref.lower()," ".join(x for x in b).lower()))
         #       w = util.calculate_wer(ref.lower()," ".join(x for x in b).lower())
         #       #in case more than one alternative of a module, that the best
         #       if c > cers:
         #           cers =c
         #       if w > wers:
         #           wers = w

        

                
         #   self.m_cer_list[mod].append(cers)
         #   self.m_wer_list[mod].append(wers)
        print "append cer done"
        
        #average CER and WER using dynamic alignment and WER based on the manual alignment, log it
    def write_cer_to_file(self,logger):
        """
            
            Write CER/WER dynamic and WER gold to file.
            
            **parameters**, **types**::
                :param logger: log file, used to log the WER counts to the log file
                :type logger: logging object
                    
           """
        cer_log_file= codecs.open(self.eval_dir+"/cer_log","w","utf8")
        print self.m_cer_list
        print self.m_wer_list2
        logger.debug(self.m_wer_list2)
        logger.debug(self.m_cer_list)

        cer_log_file.write("Character error rate per module\n\n\n")
        for elem in self.m_cer_list:
            

            
            cer_log_file.write(str(elem))
            cer_log_file.write("\n")
            cer_log_file.write(str(float(self.m_cer_list[elem]["insertion"]+self.m_cer_list[elem]["deletion"]+self.m_cer_list[elem]["replace"])/float(self.m_cer_list[elem]["n"]))+"\n\n\n")
    
        cer_log_file.write("Word error rate per module\n\n\n")

        for elem in self.m_wer_list:
            
            cer_log_file.write(str(elem))
            cer_log_file.write("\n")
            cer_log_file.write(str(float(self.m_wer_list[elem]["insertion"]+self.m_wer_list[elem]["deletion"]+self.m_wer_list[elem]["replace"])/float(self.m_wer_list[elem]["n"]))+"\n\n\n")
            
            
        cer_log_file.write("Word error rate per module 2\n\n\n")
        
        self.calculate_goldstandard_wer(cer_log_file)
        

        cer_log_file.close()

    def calculate_goldstandard_wer(self,cer_log_file):
    
        """
            
           Calculate WER from gold standard alignement operations.
            
        """
    
        for el in self.m_wer_list2:
            if isinstance(el,Original):
                for mod in self.m_wer_list2:
                    ins = self.m_wer_list2[el]["N"] - self.m_wer_list2[mod]["N"]
                    self.m_wer_list2[mod]["N"] = self.m_wer_list2[el]["N"]
                    self.m_wer_list2[mod]["I"] += ins
                break
        for e in self.m_wer_list2:
            
            wer_av = float((self.m_wer_list2[e]["D"]+self.m_wer_list2[e]["S"]+self.m_wer_list2[e]["I"] ))/float(self.m_wer_list2[e]["N"])
            
            cer_log_file.write("\n\n"+str(e))
            cer_log_file.write("\n")
            cer_log_file.write(str(wer_av)+"\n\n\n")
            for w in self.m_wer_values[e]:
                cer_log_file.write(str(w)+",")
                
            return wer_av       


            
    def evaluate_overall(self,ori_sug_map):
        """
            
            Evalute the overall performance of the system
            
            **parameters**, **types**::
                :param ori_sug_map: list conaining the original token and the suggestions for it 
                :type ori_sug_map: list
                    
           """
        for num,el in enumerate(self.ori_tgt_map):
            
            if el[0] in ori_sug_map:
                if el[1][0] in ori_sug_map[el[0]]:
                    self.tokens_found+=len(el[1][0].split())
                else:
                    self.not_found+=len(el[1][0].split())
            else:
                self.not_found+=len(el[1][0].split())
        for el in ori_sug_map:
            for sug in ori_sug_map[el]:
                self.suggestions_overall+=len(sug.split())
            
            
    def _log_sugg_per_module(self,al,ori,tgt,mod):
        """
        
        Evalute the overall performance of the system
        Evaluation direction: from target to reference
        Ex: tgt: ik heb ref: kheb 1 deletion, 1 substitution
        
        **parameters**, **types**::
            :param ori_sug_map: list conaining the original token and the suggestions for it 
            :type ori_sug_map: list
                    
       """

        #log no tokens in tgt
        self.m_wer_list2[mod]["N"]+=len(tgt.split())

        
        self.N+=len(tgt.split())
        #in case original is same as tgt 
        if ori == tgt:
            #if tgt also in sugg, nothing had do to be corr
            if tgt == al:
                self.m_log_recall_precision[mod]["nothing_to_correct"]+=len(al.split())
            #overcorrection    
            elif tgt != al:
                self.m_log_recall_precision[mod]["over_correction"]+=len(al.split())
                self.token_log[mod]["over_corrected"].append(ori)
                
                if len(al.split())<len(tgt.split()):
                    self.m_wer_list2[mod]["D"] +=len(tgt.split())-len(al.split())
                    self.D+=len(tgt.split())-len(al.split())
                    self.m_wer_list2[mod]["S"] +=len(al.split()) - len(set(tgt.split()) & set(al.split()))
                    self.S+=len(al.split()) - len(set(tgt.split()) & set(al.split()))
                elif len(al.split())==len(tgt.split()):
                    self.m_wer_list2[mod]["S"] +=len(al.split()) - len(set(tgt.split()) & set(al.split()))
                    self.S+=len(al.split()) - len(set(tgt.split()) & set(al.split()))
                elif len(al.split())>len(tgt.split()):
                    self.m_wer_list2[mod]["I"]+=len(al.split())-len(tgt.split())
                    self.I+=len(al.split())-len(tgt.split())
                    self.m_wer_list2[mod]["S"] +=(len(al.split()) - len(set(tgt.split()) & set(al.split())))-(len(al.split())-len(tgt.split()))
                    self.S+=(len(al.split()) - len(set(tgt.split()) & set(al.split())))-(len(al.split())-len(tgt.split()))
        #ori was wrong but right sugg there: corr
        elif tgt == al:
            self.m_log_recall_precision[mod]["corrected"]+=len(al.split())
            self.token_log[mod]["corrected"].append(ori)
        #ori was wrong and also not corrected    
        else:
            if len(al.split())<len(tgt.split()):
                self.m_wer_list2[mod]["D"] +=len(tgt.split())-len(al.split())
                self.D=+len(tgt.split())-len(al.split())
                self.m_wer_list2[mod]["S"] +=len(al.split()) - len(set(tgt.split()) & set(al.split()))
                self.S+= len(al.split()) - len(set(tgt.split()) & set(al.split()))
            elif len(al.split())==len(tgt.split()):
                self.m_wer_list2[mod]["S"] +=len(al.split()) - len(set(tgt.split()) & set(al.split()))
                self.S+=  len(al.split()) - len(set(tgt.split()) & set(al.split()))  
            elif len(al.split())>len(tgt.split()):
                self.m_wer_list2[mod]["I"]+=len(al.split())-len(tgt.split())
                self.I+=len(al.split())-len(tgt.split())
                self.m_wer_list2[mod]["S"] +=(len(al.split()) - len(set(tgt.split()) & set(al.split())))-(len(al.split())-len(tgt.split()))
                self.S+=(len(al.split()) - len(set(tgt.split()) & set(al.split())))-(len(al.split())-len(tgt.split()))
            self.m_log_recall_precision[mod]["not_corrected"]+=len(ori.split())
            self.token_log[mod]["not_found"].append(ori)
        self.m_log_recall_precision[mod]["tokens_overall"]+=len(ori.split())

        self.m_log_recall_precision[mod]["num_sugg"]+=len(al.split())

        #when we reach end of sentence, empty the variables
        #if lastItem:

        #    self.I += float(self.N_tgt-self.N)
         #   #this here is not solved yet, is for an average cer normalized by av sentence length
          #  avg_sent_length = 20.014051522 # Set manually
           # self.m_wer_values[mod].append(float(float(self.D+self.S+self.I)/avg_sent_length))
            #self.D=0.0
        #    self.S=0.0
         #   self.I=0.0
          #  self.N=0.0
          
