#!/usr/bin/env python
# encoding: utf-8

import sys
import codecs


def get_2grams(inputl):
    list_2grams = []
    for line in inputl:
        inputlist=line.split()
        if len(inputlist)>1:
            #if first word in line check sentence boundary before
            list_2grams.append('<s> '+inputlist[0].strip())
            for i in range (0,len(inputlist)-1):
                if inputlist[i].strip()+' '+inputlist[i+1].strip() not in list_2grams:
                    list_2grams.append(inputlist[i].strip()+' '+inputlist[i+1].strip())
            #if last word in line check sentence boundary after
            list_2grams.append(inputlist[-1].strip()+' </s>')
    return list_2grams
    
inlines = codecs.open(sys.argv[1],'r','utf8')

bigrams = get_2grams(inlines)
outf = codecs.open(sys.argv[1]+'2gram.lm','w','utf8')
outf.write('\n'.join(bigrams))
