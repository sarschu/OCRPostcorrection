#!/usr/bin/env python
# encoding: utf-8

from __future__ import division
from nltk import ngrams

import os
import string
import random
import re
import datetime
from os.path import dirname
from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import SimpleScoring, GlobalSequenceAligner
import numpy
import codecs
import sys
import itertools
from Levenshtein import distance
import difflib

ROOT_DIR = os.path.join(dirname(dirname(os.path.abspath(__file__))),"norm")
print ROOT_DIR
LOG_DIR = os.path.join(dirname(dirname(os.path.abspath(__file__))), "log")
STATIC_DIR = os.path.join(dirname(dirname(os.path.abspath(__file__))), "static")
TMP_DIR = "/tmp"

t= datetime.datetime.now()
timestamp = t.strftime('%m_%d_%Y_%H_%M_%S')
logfile = ROOT_DIR+"/../log/runs/normalization_"+timestamp+".log"

def get_random_tmp_path(prefix = "norm"):
    filename = str(prefix) + "_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
    return os.path.join(TMP_DIR, filename)

def get_random_phrase_table_path(prefix="phrase_table"):
    filename = str(prefix) + "_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
    return os.path.join("../log/phrasetables", filename)

def get_random_lm_path(prefix="lm"):
    filename = str(prefix) + "_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
    return os.path.join("../log/tmp_lms", filename)

def get_random_tmp_eval_path(prefix = "phrase_table"):
    filename = str(prefix) + "_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(6))
    return os.path.join(TMP_DIR+"/eval_options", filename)

def log_in_eval_case(ev_path,prefix = "norm"):
    filename = os.path.join(ev_path, prefix+"_"+timestamp+ ".log")
    return filename

def calculate_cer(ref,hyp):
    #!/usr/bin/env python

# Compute word error or character error rates.
# Usage: 
# To compute WER: error-rates.py wer REFERENCE-DOC HYPOTHESIS-DOC
# To compute CER: error-rates.py cer REFERENCE-DOC HYPOTHESIS-DOC
    deletion, insertion, replace = 0,0,0
    s = difflib.SequenceMatcher(None, ref, hyp)
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == "delete":
            deletion += len(ref[i1:i2])
        elif tag == "replace":
            replace +=  len(ref[i1:i2])
        elif tag =="insert":
            insertion += len(hyp[j1:j2])

    
    #[('delete', 0, 0), ('insert', 3, 2), ('replace', 3, 3)]

   
    return deletion,insertion,replace

def calculate_wer(r,h):
    #Grzegorz Chrupala
    r = r.split()
    h = h.split()
    d = numpy.zeros((len(r)+1)*(len(h)+1), dtype=numpy.uint8)
    d = d.reshape((len(r)+1, len(h)+1))
    for i in range(len(r)+1):
        for j in range(len(h)+1):
            if i == 0:
                d[0][j] = j
            elif j == 0:
                d[i][0] = i
    
        # computation
    for i in range(1, len(r)+1):
        for j in range(1, len(h)+1):
            if r[i-1] == h[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                substitution = d[i-1][j-1] + 1
                insertion    = d[i][j-1] + 1
                deletion     = d[i-1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)
    
    return (float(d[len(r)][len(h)]) / float(len(r)))
    
def check_hunspell(n,word):
	"""
	check word for spelling

	**parameters**, **types**,**return**,**return types**::
		:param word: a word
		:type word: unicode string
		:return: return True or False dependent on word being in dict or not
		:rtype: boolean	
	"""
        language = n.language
        word_split = word.split()
        is_word=False
        for word in word_split:
             
            is_word = n.hobj.spell(word.encode("utf8"))
            if is_word == False: 
                break
           
        return is_word
        

def align(ori,tgt):
    if len(ori.split())<2:
        results = [[ori,[tgt]]]
    else:
        tgtr=tgt.strip().replace("-",u"‡")
        orir=ori.strip().replace("-",u"‡")


    
        seq1 = string.strip(orir)
        seq2 = string.strip(tgtr)

        results = water(seq1, seq2)
        resultori= [x[0] for x in results]
 
    return results
 #comment in for webappl
        #this is a mechanism to correct wrong NeedleWunschAlignments
        #if len(ori.split()) == len(resultori):
        #    for i,w in enumerate(ori.split()):
        #        if w != resultori[i]:
        #            results[i][0]=w
        #else:
        #    lasti=0
        #    for i,w in enumerate(resultori):
        #        if w != ori.split()[i]:
        #            results[i][0]=ori.split()[i]
        #            lasti=i
        #    results[lasti][0]+=' '.join(ori.split()[lasti+1:])


    #return results
    

def get_linedict_from_parallel(inpath_ori, inpath_tgt):
    ### Read files
    print inpath_ori
    print inpath_tgt
    oritext= codecs.open(inpath_ori,'r','utf8').readlines()
    tgttext= codecs.open(inpath_tgt,'r','utf8').readlines()
    print len(oritext)
    print len(tgttext)
    ### Check if all rows have 4 elements
    assert len(oritext)==len(tgttext)
    
    ### Loop over all lines, collect input and output sentences
    linedict = {}
    
    for i,line in enumerate(oritext):
        alignment = align(line.strip(), tgttext[i].strip())
        k = line.strip()
        linedict[unicode(k)]={"ori": [],"tok":[], "tgt": [],"ne":[]}
        for el in alignment:
                
                linedict[k]["ori"].append(el[0])
                linedict[k]["tgt"].append(el[1][0])
                linedict[k]["tok"].append(el[1][0])
    print linedict
    return linedict
# def calculate_wer(ref,hyp):
#     errs = []
#     size = 0
#     print itertools.izip(ref, hyp)
#     for r, h in itertools.izip(ref, hyp):
#         words_r = r.split()
#         words_h = h.split()
#         print words_r
#         print words_h
#         if words_r and words_h:
#             R = distance(words_r, words_h)
#             errs.append(R)
#             size += len(words_r)
#     print "{0:.3f}".format(sum(errs)/size)
#     
#     
def zeros(shape):
    retval = []
    for x in range(shape[0]):
        retval.append([])
        for y in range(shape[1]):
            retval[-1].append(0)
    return retval

match_award      = 10
mismatch_penalty = -5
gap_penalty      = 2 # both for opening and extanding

def match_score(alpha, beta):
    if alpha == beta:
        return match_award
    elif alpha == '-' or beta == '-':
        return gap_penalty
    else:
        return mismatch_penalty

def finalize(align1, align2):
    align1 = align1[::-1]    #reverse sequence 1
    align2 = align2[::-1]    #reverse sequence 2
    
    i,j = 0,0
    
    #calcuate identity, score and aligned sequeces
    symbol = ''
    found = 0
    score = 0
    identity = 0
    for i in range(0,len(align1)):
        # if two AAs are the same, then output the letter
        if align1[i] == align2[i]:                
            symbol = symbol + align1[i]
            identity = identity + 1
            score += match_score(align1[i], align2[i])
    
        # if they are not identical and none of them is gap
        elif align1[i] != align2[i] and align1[i] != '-' and align2[i] != '-': 
            score += match_score(align1[i], align2[i])
            symbol += ' '
            found = 0
    
        #if one of them is a gap, output a space
        elif align1[i] == '-' or align2[i] == '-':          
            symbol += ' '
            score += gap_penalty
    
    #identity = float(identity) / len(align1) * 100
    

    w1=''
    w2=''
    results = []

    for i,char in enumerate(align1):
        if char ==" " and align2[i] ==" " and w1 !='' and w2!='':

            results.append([w1.replace("-","").replace(u"‡","-"),[w2.replace("-","").replace(u"‡","-")]])

            w1=''
            w2=''
        else:
            w1+=char
            w2+=align2[i]

    results.append([w1.replace("-","").replace(u"‡","-"),[w2.replace("-","").replace(u"‡","-")]])
    return results

def needle(seq1, seq2):
    m, n = len(seq1), len(seq2)  # length of two sequences
    
    # Generate DP table and traceback path pointer matrix
    score = zeros((m+1, n+1))      # the DP table
   
    # Calculate DP table
    for i in range(0, m + 1):
        score[i][0] = gap_penalty * i
    for j in range(0, n + 1):
        score[0][j] = gap_penalty * j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            match = score[i - 1][j - 1] + match_score(seq1[i-1], seq2[j-1])
            delete = score[i - 1][j] + gap_penalty
            insert = score[i][j - 1] + gap_penalty
            score[i][j] = max(match, delete, insert)

    # Traceback and compute the alignment 
    align1, align2 = '', ''
    i,j = m,n # start from the bottom right cell
    while i > 0 and j > 0: # end toching the top or the left edge
        score_current = score[i][j]
        score_diagonal = score[i-1][j-1]
        score_up = score[i][j-1]
        score_left = score[i-1][j]

        if score_current == score_diagonal + match_score(seq1[i-1], seq2[j-1]):
            align1 += seq1[i-1]
            align2 += seq2[j-1]
            i -= 1
            j -= 1
        elif score_current == score_left + gap_penalty:
            align1 += seq1[i-1]
            align2 += '-'
            i -= 1
        elif score_current == score_up + gap_penalty:
            align1 += '-'
            align2 += seq2[j-1]
            j -= 1

    # Finish tracing up to the top left cell
    while i > 0:
        align1 += seq1[i-1]
        align2 += '-'
        i -= 1
    while j > 0:
        align1 += '-'
        align2 += seq2[j-1]
        j -= 1

    finalize(align1, align2)

def water(seq1, seq2):
    m, n = len(seq1), len(seq2)  # length of two sequences
    
    # Generate DP table and traceback path pointer matrix
    score = zeros((m+1, n+1))      # the DP table
    pointer = zeros((m+1, n+1))    # to store the traceback path
    
    max_score = 0        # initial maximum score in DP table
    # Calculate DP table and mark pointers
    max_i=0
    max_j=0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            score_diagonal = score[i-1][j-1] + match_score(seq1[i-1], seq2[j-1])
            score_up = score[i][j-1] + gap_penalty
            score_left = score[i-1][j] + gap_penalty
            score[i][j] = max(0,score_left, score_up, score_diagonal)
            if score[i][j] == 0:
                pointer[i][j] = 0 # 0 means end of the path
            if score[i][j] == score_left:
                pointer[i][j] = 1 # 1 means trace up
            if score[i][j] == score_up:
                pointer[i][j] = 2 # 2 means trace left
            if score[i][j] == score_diagonal:
                pointer[i][j] = 3 # 3 means trace diagonal
            if score[i][j] >= max_score:
                max_i = i
                max_j = j
                max_score = score[i][j];
    
    align1, align2 = '', ''    # initial sequences
    
    i,j = max_i,max_j    # indices of path starting point
    
    #traceback, follow pointers
    while pointer[i][j] != 0:
        if pointer[i][j] == 3:
            align1 += seq1[i-1]
            align2 += seq2[j-1]
            i -= 1
            j -= 1
        elif pointer[i][j] == 2:
            align1 += '-'
            align2 += seq2[j-1]
            j -= 1
        elif pointer[i][j] == 1:
            align1 += seq1[i-1]
            align2 += '-'
            i -= 1

    results=finalize(align1, align2)
    oriwords=seq1.replace(u"‡","-").split()
    counter=0
    tmpres=''

   

    alori=''
    for el in results:
        alori+=el[0]+' '
    alori=alori.strip()
    if alori.strip()==seq1.replace(u"‡","-").strip():
        return results

    if len(results)==1 and results[0][0] != seq1.replace(u"‡","-"):
        results[0][0]=seq1.replace(u"‡","-")
        return results
    else:

        if results[0][0] != oriwords[counter] and results[0][0] in oriwords[counter]:
            results[0][0] = oriwords[counter]
        
        while tmpres.strip() != seq1.replace(u"‡","-") and oriwords[counter] not in results[0][0] and results[0][0] not in tmpres:
            tmpres +=oriwords[counter]+' '
            counter+=1 
        if oriwords[0] != results[0][0].split()[0] and tmpres=='':
            if results[0][0].split()[0] == oriwords[1]:
                results[0][0] =  oriwords[0]+' '+ results[0][0]
            else:
                results[0][0] =  oriwords[0]+' '+ ' '.join(results[0][0].split()[1:])
        if len(oriwords)>1 and len(results[0][0].split())>1 and oriwords[0] == oriwords[1] and (results[0][0].split()[0] != results[1][0].split()[0] or results[0][0].split()[0] !=results[0][0].split()[1]):
            results[0][0] = oriwords[0]+' '+ results[0][0]
        if len(oriwords)>2 and len(results[0][0].split())>2 and oriwords[0] == oriwords[1] and oriwords[1] != oriwords[2] and (results[0][0].split()[0] == results[0][0].split()[1] and results[0][0].split()[0] == results[0][0].split()[2]):
            results[0][0] = ' '.join(results[0][0].split()[1:])
        
        if tmpres.strip() == seq1.strip():
            results[0][0] = tmpres.strip().replace("  "," ")
            
        else:
            if tmpres !=''  and results[0][0].split()[0] in tmpres.strip().split()[-1] :
                results[0][0]=tmpres.strip()+' '+' '.join(results[0][0].split()[1:])

            elif results[0][0] in tmpres:
                results[0][0]=tmpres.strip()
            else:

                results[0][0]=tmpres.strip()+' '+results[0][0]
                results[0][0]=results[0][0].strip()

        for i in range(len(results)):
            results[i][0] = re.sub("[ ]{2,}"," ",results[i][0]).strip()
            
        return results
