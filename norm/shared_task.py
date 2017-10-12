#!/usr/bin/env python
# encoding: utf-8
import sys
import os
import util
import types
#from modules.original import Original
#from modules.new_NE import New_NE
#from prepro.rewrite import Rewrite 
#from modules.flooding import Flooding
import codecs
import itertools
import re
import json
import difflib
import ast
from collections import OrderedDict

#"fr_sample/1.txt":{
#		   "0:3": {"FRAGMENT DE LA":0.8, "FRAGMENT DELA":0.2},
#		   "27:1": {"GESTE DE GIRBERT":0.5, "GESTE DEGIRBERT":0.5},
#		   "55:1": {"avons trouvé":0.9, "a trouvé": 0.1},
#		   "64:1": {"le manuscrit":1}
#	},
# python shared_task.py folderwithenglish_mono folderwithenglish_periodical folderwithfr_mono folderwithfr_periodical task <optional>jsonwithcorrtokens
task=sys.argv[5]
indir = sys.argv[1]
indir2 = sys.argv[2]
indir3 = sys.argv[3]
indir4 = sys.argv[4]
dumbjson={}
corrjson={}
if len(sys.argv) ==7:

    with open(sys.argv[6]) as data_file:    
        corrjson = json.load(data_file)
        
for f in os.listdir(indir):
    
    if "normalization"  in f:

        outname = f.split("log_")[1]
        #print f
        logtext=codecs.open(indir+'/'+f,'r','utf8').read()
        rd=OrderedDict()
        res= re.findall("\n[\d\-: ,]+ DEBUG (.*)\n[\d\-: ,]+ DEBUG SHARED TASK END",logtext)
        i=0
        for result in res:
            elements= ast.literal_eval(result)
            for r in elements:

                
                if task =="1":
                    if r[0] != re.sub(" ([\.\:\?\!\'\,])","\\g<1>",r[1][0]):
                        rd[str(i)+':'+str(len(r[0].split()))]={}
                elif task =="2":

                    print i
                    matches=[key for key in corrjson[indir.split('/')[-1]+'/'+outname] if  key.startswith(str(i)+':')]
                    if matches !=[]:
#                    if str(i)+':'+str(len(r[0].split())) in corrjson[indir.split('/')[-1]+'/'+outname]:
                        rd[str(i)+':'+str(len(r[0].split()))]={re.sub(" ([\.\:\?\!\'])","\\g<1>",r[1][0]):1.0}
                i+=len(r[0])
                i+=1
            #print rd
        print indir.split('/')[-1]
        dumbjson[indir.split('/')[-1]+'/'+outname]=rd
    
for f in os.listdir(indir2):
    
    if "normalization" in f:
        outname = f.split("log_")[1]
        #print f
        logtext=codecs.open(indir2+'/'+f,'r','utf8').read()
        rd=OrderedDict()
        res= re.findall("\n[\d\-: ,]+ DEBUG (.*)\n[\d\-: ,]+ DEBUG SHARED TASK END",logtext)
        i=0
        for result in res:
            elements= ast.literal_eval(result)
            for r in elements:

                if task =="1":
                    if r[0] != re.sub(" ([\.\:\?\!\'\,])","\\g<1>",r[1][0]):
                        rd[str(i)+':'+str(len(r[0].split()))]={}
                elif task =="2":
                    print i
                    matches=[key for key in corrjson[indir2.split('/')[-1]+'/'+outname] if  key.startswith(str(i)+':')]
                    if matches !=[]:
                    #if str(i)+':'+str(len(r[0].split())) in corrjson[indir2.split('/')[-1]+'/'+outname]:
                        rd[str(i)+':'+str(len(r[0].split()))]={re.sub(" ([\.\:\?\!\'])","\\g<1>",r[1][0]):1.0}
                i+=len(r[0])
                i+=1
            #print rd
        print indir2.split('/')[-1]
        dumbjson[indir2.split('/')[-1]+'/'+outname]=rd
            
for f in os.listdir(indir3):
    
    if "normalization" in f:
        outname = f.split("log_")[1]
        #print f
        logtext=codecs.open(indir3+'/'+f,'r','utf8').read()
        rd=OrderedDict()
        res= re.findall("\n[\d\-: ,]+ DEBUG (.*)\n[\d\-: ,]+ DEBUG SHARED TASK END",logtext)
        i=0
        for result in res:
            elements= ast.literal_eval(result)
            for r in elements:

                if task =="1":
                    if r[0] != re.sub(" ([\.\:\?\!\'\,])","\\g<1>",r[1][0]):
                        rd[str(i)+':'+str(len(r[0].split()))]={}
                elif task =="2":
                    print i
                    matches=[key for key in corrjson[indir3.split('/')[-1]+'/'+outname] if  key.startswith(str(i)+':')]
                    if matches !=[]:
                    #if str(i)+':'+str(len(r[0].split())) in corrjson[indir2.split('/')[-1]+'/'+outname]:
                        rd[str(i)+':'+str(len(r[0].split()))]={re.sub(" ([\.\:\?\!\'])","\\g<1>",r[1][0]):1.0}
                i+=len(r[0])
                i+=1
          #  print rd
        print indir3.split('/')[-1]
        dumbjson[indir3.split('/')[-1]+'/'+outname]=rd

for f in os.listdir(indir4):
    
    if "normalization" in f:
        outname = f.split("log_")[1]
        #print f
        logtext=codecs.open(indir4+'/'+f,'r','utf8').read()
        rd=OrderedDict()
        res= re.findall("\n[\d\-: ,]+ DEBUG (.*)\n[\d\-: ,]+ DEBUG SHARED TASK END",logtext)
        i=0
        for result in res:
            elements= ast.literal_eval(result)
            for r in elements:

                if task =="1":
                    if r[0] != re.sub(" ([\.\:\?\!\'\,])","\\g<1>",r[1][0]):
                        rd[str(i)+':'+str(len(r[0].split()))]={}
                elif task =="2":
                    print i
                    matches=[key for key in corrjson[indir4.split('/')[-1]+'/'+outname] if  key.startswith(str(i)+':')]
                    if matches !=[]:
                    #if str(i)+':'+str(len(r[0].split())) in corrjson[indir2.split('/')[-1]+'/'+outname]:
                        rd[str(i)+':'+str(len(r[0].split()))]={re.sub(" ([\.\:\?\!\'])","\\g<1>",r[1][0]):1.0}
                i+=len(r[0])
                i+=1
         #   print rd
        print indir4.split('/')[-1]
        dumbjson[indir4.split('/')[-1]+'/'+outname]=rd
            

    
with codecs.open("/".join(indir.split("/")[:-1])+'/task'+task+'results.json', 'w',"utf8") as f:
      json.dump(dumbjson, f, ensure_ascii=False)


