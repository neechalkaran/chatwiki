#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import requests
from urllib.parse import urlencode
from urllib.request import urlopen
import dateutil.parser

def sparql_wikidata(query):
  url = 'https://query.wikidata.org/sparql?'
  params = urlencode({'format': 'json', 'query': query})
  #results = json.load(urlopen(url + params))
  results = json.loads(urlopen(url + params).read().decode('utf-8'))
  return results

def list_of_entities_from_sparql(query):
  results = sparql_wikidata(query)
  if 'results' not in results: return []
  if 'bindings' not in results['results']: return []
  vals = []
  for v in results['results']['bindings']:
    if 'entity' not in v: continue
    if 'type' not in v['entity']: continue
    if v['entity']['type'] != 'uri': continue
    if 'value' not in v['entity']: continue
    vals += [v['entity']['value'][31:]]
  return vals

def get_instance_name(name):
  url = "https://ta.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item&redirects=1&titles="+name+"&format=json"
  xpage= requests.get(url)
  xpage.encoding = 'utf-8'
  data=json.loads(xpage.text)
  for i in data['query']['pages']:
    if 'pageprops' not in data['query']['pages'][i]: continue
    qid= data['query']['pages'][i]['pageprops']['wikibase_item']
    return getlabel_in_from_sparql(qid, "P31")
  return name

def getlabel_in_from_sparql(Qid, pid):
  query = 'SELECT ?lLabel  WHERE { wd:'+Qid+' wdt:'+pid+' ?l SERVICE wikibase:label { bd:serviceParam wikibase:language "ta". }}'
  results = sparql_wikidata(query)
  if 'results' not in results: return ""
  if 'bindings' not in results['results']: return ""
  vals = ""
  label = []
  for v in results['results']['bindings']:
    if 'lLabel' not in v: continue
    if 'type' not in v['lLabel']: continue
    if v['lLabel']['type'] != 'literal': continue
    if 'value' not in v['lLabel']: continue
    label.append(v['lLabel']['value'])
  if(len(label)>1):
    return "மொத்தம் " + str(len(label)) +". " + ", ".join(label)
  elif(len(label)==1):
    return label[0]
  else:
    return ""

def count_from_sparql(query):
  results = sparql_wikidata(query)
  if 'results' not in results: return -1
  if 'bindings' not in results['results']: return -1
  if len(results['results']['bindings']) != 1: return -1
  if 'count' not in results['results']['bindings'][0]: return -1
  if 'type' not in results['results']['bindings'][0]['count']: return -1
  if results['results']['bindings'][0]['count']['type'] != 'literal': return -1
  if 'datatype' not in results['results']['bindings'][0]['count']: return -1
  if results['results']['bindings'][0]['count']['datatype'] != 'http://www.w3.org/2001/XMLSchema#integer': return -1
  if 'value' not in results['results']['bindings'][0]['count']: return -1
  return int(results['results']['bindings'][0]['count']['value'])


def getprop_in_label_from_sparql(label):
  query = 'SELECT ?item WHERE { ?item rdfs:label "'+label+'"@ta. ?item ?a ?b.  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } ?prop wikibase:directClaim ?a . } limit 1'
  query2 = 'SELECT ?item WHERE { ?item skos:altLabel "'+label+'"@ta. ?item ?a ?b.  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } ?prop wikibase:directClaim ?a . } limit 1'
  results = sparql_wikidata(query)
  if 'results' not in results: return ""
  if 'bindings' not in results['results']: return ""
  vals = ""
  Propid=""
  for v in results['results']['bindings']:
    Propid=v['item']['value'].replace('http://www.wikidata.org/entity/','')
  if re.search('P[0-9]+',Propid):  #^ Matches the start of the string
    return Propid
  else:#to remove if it is not prop id. it may return Qitem, so avoided
    results = sparql_wikidata(query2)#To check in alias name
    if 'results' not in results: return ""
    if 'bindings' not in results['results']: return ""
    for v in results['results']['bindings']:
      Propid=v['item']['value'].replace('http://www.wikidata.org/entity/','')

  if re.search('P[0-9]+',Propid):  #^ Matches the start of the string
    return Propid
  else:
    return ""


def getQid_in_label_from_sparql(label):
  query = 'SELECT ?item WHERE { ?item ?label "'+ label +'"@ta. ?item ?a ?b.SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } ?prop wikibase:directClaim ?a .} limit 1'
  query2 = 'SELECT ?item WHERE { ?item ?alias "'+ label +'"@ta. ?item ?a ?b.SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } ?prop wikibase:directClaim ?a .} limit 1'
  results = sparql_wikidata(query)
  if 'results' not in results: return ""
  if 'bindings' not in results['results']: return ""
  vals = ""
  Itemid= ""
  for v in results['results']['bindings']:
    Itemid= v['item']['value'].replace('http://www.wikidata.org/entity/','')
  if re.search('Q[0-9]+',Itemid):  #^ Matches the start of the string
    return Itemid
  else:#just to ensure it may return other item, so avoided
    results = sparql_wikidata(query2)#To check in alias name. example  #
    if 'results' not in results: return ""
    if 'bindings' not in results['results']: return ""
    for v in results['results']['bindings']:
      Itemid=v['item']['value'].replace('http://www.wikidata.org/entity/','')

  if re.search('Q[0-9]+',Itemid):  #^ Matches the start of the string
    return Itemid
  else:
    return ""

def getQid_in_label_from_API(lists):#[['தென் ஆப்பிரிக்கா', 'குடியரசுத் தலைவர்'], ['தென்', 'ஆப்பிரிக்கா', 'குடியரசு', 'தலைவர்'], ['தென்', 'ஆப்பிரிக்காவின்', 'குடியரசு
  string_list =[]
  for a in lists:
    if(len(a)>0):
      string_list.append([a[0]," ".join(a)])
    if(len(a)>1):
      string_list.append([a[0]+" "+a[1]," ".join(a)])#'தெற்கு கரோலினா உருவான நாள்'
      string_list.append([a[0]+a[1],"".join(a)])
  strings = []
  for x in string_list:
    if x not in strings:
        strings.append(x)
  #print(strings)
  matched=[]
  searched=[]#used when no match found. பெருவுடையார் ஆலயம்
  for u in strings:
    sentence = u[1] #திருவள்ளுவர் பல்கலைக்கழகம் நிர்வாகப்பகுதி
    query_url ="https://www.wikidata.org/w/api.php?action=wbsearchentities&search="+u[0]+"&format=json&errorformat=plaintext&language=en&uselang=en&type=item&limit=500"
    r = requests.get(url = query_url)#.content.decode('utf-8')
    r.encoding = 'utf-8'
    data = r.json()
    #print(data['search'])
    if(len(data['search'])>49):#when it has more results. 'இந்திய', 'சுதந்திர', 'நாள்
      item = getQid_in_label_from_sparql(u[0])
      if(item !=""): matched.append([u[0], item])#["இந்தியா", "Q668"]
    for v in data['search']:
      #print(v['match']['text'])
      searched.append(v['id'])
      if(sentence.find(v['match']['text'])==0):#when matched with starting letters
         matched.append([v['match']['text'],v['id']])
    if(len(matched)==0):#ஜெயலலிதா not matched in search as it is alias
      item = getQid_in_label_from_sparql(u[0])
      if(item !=""): matched.append([u[0], item])
  #print(matched)
  searched =list(dict.fromkeys(searched))
  if(len(searched)==1): return searched[0]
  if(len(matched)==0): return ""
  elif(len(matched)==1): return matched[0][1]
  else:
    matched.sort(key=lambda x: int(x[1][1:]), reverse=False)#sort to pick earliest property get matched
    matched.sort(key=lambda x: len(x[0]), reverse=True)

    return matched[0][1]

def getProp_in_label_from_API(array):#[['தென் ஆப்பிரிக்கா', 'குடியரசுத் தலைவர்'], ['தென்', 'ஆப்பிரிக்கா', 'குடியரசு', 'தலைவர்'], ['தென்', 'ஆப்பிரிக்காவின்', 'குடியரச]
  string_list =[]
  for a in array:
    if(len(a)>0):
      string_list.append(a[-1])
    if(len(a)>1):
      string_list.append(a[-2]+" "+a[-1])#'இந்தியா உருவான நாள்'
      string_list.append(a[-2]+a[-1])
#  print(string_list)
  string_list =list(dict.fromkeys(string_list))
  matched=[]
  for u in string_list:
    #print(u[-1])
    query_url ="https://www.wikidata.org/w/api.php?action=query&list=search&srsearch="+u+"&format=json&srnamespace=120&srlimit=500&srprop=extensiondata"
    r = requests.get(url = query_url)#.content.decode('utf-8')
    r.encoding = 'utf-8'
    data = r.json()

    for v in data['query']['search']:
      #print(v['extensiondata']['wikibase']['extrasnippet'])
      if(u==" ".join(word_tokenize(v['extensiondata']['wikibase']['extrasnippet']))):
        matched.append([u,v['title']])
    if(len(matched)==0):
      prop = getprop_in_label_from_sparql(u)# நினைவு நாள் doesn't comeup in search
      if(prop != ""): matched.append([u, "Property:"+prop])

  #print(matched)
  if(len(matched)==0): return ""
  elif(len(matched)==1): return matched[0][1].split(":")[1]
  else:
    matched.sort(key=lambda x: int(x[1][10:]), reverse=False)#sort to pick earliest property get matched
    #print(matched)
    matched.sort(key=lambda x: len(x[0]), reverse=True)
    #print(matched)
    return matched[0][1].split(":")[1]



def word_tokenize(text):
  words = re.findall("[ஂ-௺]+",text)
  whlist =["என்ன","யார்","என்று","எப்போது","எது","எவை","எத்தனை","எவ்வளவு","உள்ளன"]
  for a in whlist:
    if a in words:
      words.remove(a)
  return words

def get_entities(words):
  URL = "http://vaani.neechalkaran.com/v2/ner"
  r = requests.post(url = URL, data={"tamilwords":"|".join(words)})
  data = r.json()
#  print(data)
  entity=[]
  for i in data:
    for j in range(len(i["NERWords"])):
      if(i["Solspan"]>0):
        entity.append(i["NERWords"][j].split("+")[0])
    #print(i)
  return(entity)



def get_roots(words):
  URL = "http://vaani.neechalkaran.com/v2/parse"
  r = requests.post(url = URL, data={"tamilwords":"|".join(words)})
  data = r.json()
  roots=[]
  for i in data:
    for j in range(len(i["RootWords"])):
      if(i["Flag"]==True):
        roots.append(i["RootWords"][j].split("+")[0])
  return(roots)

def date_string(dvalue):
  if (isfloat(dvalue)): return dvalue
  tmonth="ஜனவரி,பிப்ரவரி,மார்ச்,ஏப்ரல்,மே,ஜூன்,ஜூலை,ஆகஸ்ட்,செப்டம்பர்,அக்டோபர்,நவம்பர்,டிசம்பர்".split(',')
  tvalue=dvalue
  try:
    frame = dateutil.parser.parse(dvalue)
  except :
    return dvalue
  tvalue = str(frame.year) +" "+ tmonth[int(frame.month)-1] +" "+ str(frame.day)
  return tvalue

def isfloat(str):
  try:
    float(str)
  except ValueError:
    return False
  return True
