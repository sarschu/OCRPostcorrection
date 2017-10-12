#!/usr/bin/env python
# encoding: utf-8
import subprocess
import operator
import util
import codecs
import logging
from Levenshtein import distance
import os
import datetime


lm_log = logging.getLogger("norm.module.lm")
class LM(object):
    '''
    This class contains functions with which for every word a word is suggested that appears in the input text and is close to the current word (Levenshtein)
    '''


    def __init__(self,normalizer):
        """
        **parameters**, **types**::
            :param normalizer: an object of the class Normalizer
            :type word: Normalizer object

        """
        self.normalizer = normalizer
        self.specific_vocab=[]
        self.lm_path=''
        print self.normalizer.language
        print "bef"
        if self.normalizer.language=="en":
            self.table = codecs.open(util.STATIC_DIR+"/Levenshtein/lex.e2f.en","r","utf8").readlines()
        elif  self.normalizer.language=="fr":
            print "french"
            self.table = codecs.open(util.STATIC_DIR+"/Levenshtein/lex.e2f.fr","r","utf8").readlines()
        else:
            self.table = codecs.open(util.STATIC_DIR+"/Levenshtein/lex.e2f.de","r","utf8").readlines()
        self.prob_dict_sub={}
        self.prob_dict_ins={}
        self.prob_dict_del={}
        print "after"
        for line in self.table:
            ls=line.strip().split()
            if ls[0]=="NULL":
                self.prob_dict_ins[ls[1]]=float(ls[2])
            elif ls[1]=="NULL":
                self.prob_dict_del[ls[0]]=float(ls[2])
            else:
                self.prob_dict_sub[ls[0]+ls[1]]=float(ls[2])
        print "table read"
        super(LM,self).__init__()
        


    def make_lm(self,text):
        os.system("export PYTHONIOENCODING=utf-8")
        print "b3f"
        os.environ["LC_ALL"] = "en_US.UTF-8"
        print "in the function"
        
        t= datetime.datetime.now()
        timestamp = t.strftime('%m_%d_%Y_%H_%M_%S')
        tmpfile = codecs.open(timestamp,'w','utf8')
        tmpfile.write(text)
        tmpfile.close()
        #echo = subprocess.Popen(['echo',text],stdout=subprocess.PIPE,shell=False)
        #print "after echo"
        #echo2 = echo.communicate()[0]
        #print 'ttttt'
        #e=unicode(echo2)
        input = codecs.open(timestamp,'r','utf8')
        print  ' '.join([self.normalizer.KENLM_PATH+'/lmplz','-o','1'])
        #tstfile= codecs.open("testf","w","utf8")
        self.lmpath=util.get_random_lm_path()
        lmfile = codecs.open(self.lmpath,'w',"utf8")
        proc = subprocess.Popen([self.normalizer.KENLM_PATH+'/lmplz','-o','1'],stdin = input, stdout= lmfile, stderr= subprocess.PIPE,shell=False)
        
        out,err = proc.communicate()
        input.close()
        os.remove(timestamp)
        #proc = subprocess.Popen([self.normalizer.KENLM_PATH+'/lmplz','-o','1'],stdin = subprocess.PIPE, stdout= lmfile, stderr= subprocess.PIPE,shell=False)
        #out,err = proc.communicate(text.encode("utf-8"))
        lmfile.flush()
        print "reading from file"
        print self.lmpath
        lmf=codecs.open(self.lmpath,"r","utf8")
        lmft=codecs.open(self.lmpath,"r","utf8").read()
        if lmft.strip() != '':
        
            out = lmf.readlines()
            lmf.close()
            numbers=[]

            for i,element in enumerate(out):
                try:
                   numb= float(element.split("\t")[0])
                   if numb not in numbers:
                       numbers.append(numb)
                   
                except ValueError:
                   pass
            almostmax = sorted(numbers)[1]
            max= sorted(numbers)[0]
         
            finalout=["\data\\"+'\n',"ngram 1=3259\n","ngram 2=1\n","\n","\\1-grams:"+'\n','-4.1670585\t<unk>\n']
            for element in out[5:]:
                print element
                print str(max)
                print str(almostmax)
                if not str(max) in element and not str(almostmax) in element and len(element.split("\t"))>1 and len(element.split("\t")[1])> 3:
                    print "appending"
                    finalout.append(element)
        
            #finalout.insert(len(finalout)-2,"\n\\2-grams:\n-1.000\t"+finalout[9].split('\t')[1].strip()+' '+finalout[9].split('\t')[1].strip()+"\n")
            finalout[1] ='ngram 1='+str(len(finalout)-5)+'\n'
            finalout.append("\n")
            finalout.append("\\2-grams:\n")
            finalout.append("-1.000\t"+finalout[9].split("\t")[1].strip()+" "+finalout[9].split("\t")[1].strip()+"\n")
            finalout.append("\n")
            finalout.append("\end\\")

            print finalout[1]
            finalout = ''.join(finalout)
            lmmod= codecs.open(self.lmpath,"w","utf8")
            lmmod.write(finalout)
            lmmod.close()
            print "utf8check"
            out = unicode(finalout)
            print "this worked"

            lm = finalout.split('\n')
            dict={}

            for line in lm:
                ls = line.split("\t")
                if len(ls)==2:
                    dict[ls[1].strip()] = float(ls[0])


            sorted_list = sorted(dict.items(),key=operator.itemgetter(1))



            position=-1
            for i in range(len(sorted_list)):
                self.specific_vocab.append(sorted_list[i][0])
               
            print self.specific_vocab
            #lmpath=self.write_lm(lm, onetimecount)
            return self.lmpath
        else:
            self.specific_vocab="nospecific"
            return "../log/tmp_lms/fallback.lm"
        
        
    def write_lm(self, lm,onetimecount):
        self.lmpath=util.get_random_lm_path()
        print self.lmpath
        lmfile = codecs.open(self.lmpath,'w',"utf8")
        for line in lm:
            ls=line.split('\t')
            if len(ls)!=2:
                lmfile.write(line.strip()+'\n')
            else:
                if ls[1].strip() != onetimecount:
                    lmfile.write(line.strip()+'\n')
        lmfile.close()
        return self.lmpath

    def calc_closest_word(self,word,prob_dict_sub,prob_dict_ins,prob_dict_del):
    
        if self.specific_vocab != "nospecific":
            levenshtein_dist=1000.
            sug =""
            for potsug in self.specific_vocab:
                dist = self.levenshtein(unicode(potsug), unicode(word),prob_dict_sub,prob_dict_del,prob_dict_ins)
                if dist !=0 and dist < levenshtein_dist:
                    levenshtein_dist = dist
                    
                    sug=potsug
        else:
            sug = word

        return sug
 

                
    def levenshtein(self,s1, s2,prob_dict_sub,prob_dict_del,prob_dict_ins):
        if len(s1) < len(s2):
            return self.levenshtein(s2, s1,prob_dict_sub,prob_dict_del,prob_dict_ins)

        # len(s1) >= len(s2)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                if c1+c2 in prob_dict_ins:
                    insertions = previous_row[j] + 1-(prob_dict_ins[c1+c2])
                else:
                    insertions = previous_row[j] + 1
                #insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
                if c1+c2 in prob_dict_del:
                    deletions = current_row[j] + 1-(prob_dict_del[c1+c2])
                else:
                    deletions = current_row[j] + 1
                #deletions = current_row[j] + 1       # than s2
              
                if c1+c2 in prob_dict_sub:
                    substitutions = previous_row[j] + 1-(prob_dict_sub[c1+c2])
                else:
                    substitutions = previous_row[j] + 1

                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]



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
        lm_log.info("start lm checker")
        original = sentence.split()
        words = sentence.split()
        results = []
        
       

                
        for i in range(0,len(words)):

            if  i in corr_list and self.normalizer.hobj.spell(words[i]) ==False:

                sugg=self.calc_closest_word(words[i],self.prob_dict_sub,self.prob_dict_ins,self.prob_dict_del)
                #append all made up compound as an option. To use hunspell include the two lines above
                results.append([unicode(original[i]),[sugg]])

            else:
                results.append([unicode(original[i]),[unicode(original[i])]])
          
        lm_log.debug(results)
        lm_log.info("lm checker finished")
        return results
        
        
