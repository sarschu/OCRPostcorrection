#!/usr/bin/env python
# encoding: utf-8
'''
Created on May 31, 2013

@author: sarah
usage: run_norm.py <ini> <inputfile> <outputfile> (<csv_doc> <evalDir>)
'''
#if you want to use the preclassifier, normalizer takes a keyword argument pc=True
#you need a csv file for the evaluation
#you need to specifiy the language

import configparser
import codecs
import logging
import os
from prepro.rewrite import Rewrite
from modules.flooding import Flooding
import normalisation
import sys
sys.path.append(os.getcwd())
import util
from data import Text
from normalizer import Normalizer

#from normalizer_preclass import NormalizerPre


#creates the logging file with the three levels DEBUG, INFO, WARNING
config = configparser.ConfigParser()
logger = logging.getLogger('norm')
logger.setLevel(logging.DEBUG)
if len(sys.argv)==6:
        os.system("mkdir "+sys.argv[5])
	hdlr = logging.FileHandler(util.log_in_eval_case(sys.argv[5]))
else:
	hdlr = logging.FileHandler(util.logfile+"_"+sys.argv[2].split("/")[-1])
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)

logger.info(" Starting with the normalization pipeline")
# We may want to work on a corpus of texts, or just on one text.
# A text is e.g. 1 tweet or 1 SMS message.
# If we work on multiple texts, we make a Text instance for each one.
# When instantiating a text, we provide the original text as a unicode string
# (making sure that encoding has been handled), and the text type:
# Or in the case of many texts:
# We also instantiate a Normalizer object, which will do the normalization.

#all expected parameters


config.read(unicode(sys.argv[1]))
try:
    language = config.get("Language", "ln")
    SMT_token =config.get("SMT", "Token")
    SMT_unigram=config.get("SMT", "Unigram")
    SMT_bigram=config.get("SMT", "Bigram")
    SMT_decision=config.get("SMT","Decision")
    MOSES_PATH=config.get("MOSES-PATH", "Moses")
    MOSES_SERVER=config.get("MOSES-PATH", "Mosesserver")
    CRF_PATH=config.get("CRF-PATH", "CRF")
    SETTING=config.get("SETTING", "train_set")
    LM_PATH=config.get("LM","lm")
    modules_string = config.get("Modules","mod")
    modules = modules_string.split()
    filtering = config.get("Filter","filter")
    if filtering != "none":
	    LM_MODEL=config.get("Filter","filter_lm")
    else:
        LM_MODEL="no model"
    dev = config.get("Development","dev")
    

except configparser.NoOptionError:
	raise

#for quantitative analysis
    
#for qualitative and quantitative analysis   
csv_dict={} 

#n = Normalizer(language="nl",pc=True) # In case of Dutch
try:
	if len(sys.argv)==6:

	    os.system("cp "+sys.argv[1]+" "+sys.argv[5])
	    n = Normalizer(filtering,LM_MODEL,language,SMT_token, SMT_unigram, SMT_bigram, SMT_decision, MOSES_PATH, MOSES_SERVER,CRF_PATH, LM_PATH, SETTING, modules,dev,eval_dir=sys.argv[5]) 

	    csv_dict = normalisation.get_linedict_from_csv(sys.argv[4],"utf8")

	    n.e._open_log_for_each_module()
	else:
	    n = Normalizer(filtering,language,LM_MODEL,SMT_token, SMT_unigram, SMT_bigram, SMT_decision, MOSES_PATH, MOSES_SERVER,CRF_PATH, LM_PATH, SETTING, modules,dev)# In case of Dutch
	# n = Normalizer(language="en") # In case of English
	input_file = sys.argv[2]
	output_file=sys.argv[3]
	#rewrite object
	r = Rewrite(n)


	testfile = codecs.open(input_file,"r","utf-8")
	my_sms_collection=[]
	testlines = testfile.readlines()
	for line in testlines:
	    my_sms_collection.append(line)
	print my_sms_collection



	list_of_sms = [Text(sms,n,r) for sms in my_sms_collection]
	print list_of_sms
	outfile = codecs.open(output_file,"w","utf-8")
	f = Flooding(n)
	
for sms in list_of_sms:

    counter += 1
 
    print "Processing text %d of %d" % (counter, amount)

    if sms.text_prepro.strip() !="":
        print "preprocessed version"
        f_out.write(f.flooding_correct(sms.text_prepro) + u"\n")
    if sms.text_prepro.strip()=="":
        deleted+=1
        print "LINE DELETE:"


print "There have been %d lines deleted" % (deleted)

f_out.close()
#n.kill_server_mode(pids)
logger.info(" Done! Enjoy your prepocessed text!")
if __name__ == '__main__':
    pass
