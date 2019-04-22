import spacy
from spacy import displacy
import subprocess
import os
import re
import requests
import json
from lxml import html
from stanfordcorenlp import StanfordCoreNLP 
from builtins import str

dir_path = os.path.dirname(os.path.realpath(__file__))

text = u'Jenny Aloni (née Rosenbaum) was born on 7.9.1917 to Henriette and Moritz Rosenbaum in Paderborn, Germany and died on 30.9.1993 in Ganei Yehuda in Israel. She grew up in a well-established family in Paderborn and attended a Catholic Lyceum until 1935. In reaction to the increasing number of anti-Semitic hostilities since 1933, she turned to Zionism as well as to socialist ideas. In 1935, she began preparing for her immigration to Palestine in the Spreenhagen hachschara training school. Out of consideration to her parents, she delayed her plans to leave for Palestine and instead studied in the school of the Berlin synagogue Adass Iisroel from 1936 until her graduation. Nonetheless, she continued to make contacts with socialist groups within the Zionist movement and learned Hebrew and Arabic. Following her graduation from high school in 1939, she worked as a hachschara or training group leader in the Schniebinchen (today Świbinki, western Poland) training camp. She soon thereafter immigrated to Palestine via Trieste with a youth aliyah group transporting Jewish children and adolescents. In Jerusalem, she studied literature at the Hebrew University and did voluntary social work for neglected children and adolescents. In 1942, she enlisted in the medical service of the Jewish Brigade of the British Army. In 1946, began her studies in Jerusalem to train to work in social service. She reflected on this training in her diaries, which have now been published. Jenny did not complete her studies but did continue her voluntary social work. Between 1938 and 1950 she worked with the Labor youth movement as a vocational counsellor. Later, in Paris and Munich, she helped to repatriate Jews to their home countries or to immigrate to Palestine. In 1948, Jenny Rosenbaum married Esra Aloni, who had immigrated to Palestine in 1934. Jenny served as a paramedic during Israel’s War of Independence in 1948. In 1950, her daughter Ruth was born, and in 1955, Jenny Aloni visited her hometown of Paderborn for the first time since 1935. Beginning in 1957, the family Aloni lived in Ganei Yehuda near Tel Aviv. For nearly 20 years, Jenny Aloni was a volunteer at the public psychiatric clinic in Be’er Ya’akov. Because she was so successful in her work, she was able to participate in case conferences in the clinic. Before and after immigrating to Israel, Jenny’s primary vocation was that of a writer. She wrote short papers and poems in Hebrew that were published in Dovrat Ha-Poelat, a feminist socialist journal, but most of her writing was in German. Her works included short stories, poems and diaries. Her diaries recounted such events as her childhood in the Third Reich, the ingathering of exiles in Israel and the Israeli-Palestinian conflict. In the 1960s, she received attention from the renowned writers Max Brod and Heinrich Böll. Jenny Aloni is considered to be among the most important writers who wrote in German in Israel. In 1967, she won the Paderborn Cultural Award for her writings. She was awarded the President’s award for her volunteer work in the Be’er Yaacov psychiatric hospital in 1976. In 1991, she received the Annette von Droste-Hülshoff literary prize.'

text = re.sub(r'\([^()]*\)', '', text)
text = text.replace("‘", '').replace("’", '').replace("'", '').replace("  ", " ")

nlp = spacy.load('en_core_web_lg', disable=["tagger", "ner"])

for word in nlp.Defaults.stop_words:
    lex = nlp.vocab[word]
    lex.is_stop = True

doc = nlp(text)
result = {}
sent_counter = 0

parser_info = ['java', '-jar',
             dir_path + '/ClausIEpy/clausie.jar','-c',
             dir_path + '/ClausIEpy/resources/clausie.conf', 
             '-v', '-s']

for sent in doc.sents:
    
    result[sent_counter] = {}
    result[sent_counter]['clauses'] = {}
    result[sent_counter]['tags'] = {}
    result[sent_counter]['original_sent'] = sent.text
    shorten_sent = nlp(' '.join([str(t) for t in sent if not t.is_stop]))
        
    shorten_lemma_original = ""
    
    tag_counter = 0
    for token in shorten_sent:
        if (token.lemma_ not in ['.', ',', ';', '-']):
            shorten_lemma_original += token.lemma_ + " "
        
            result[sent_counter]['tags'][tag_counter] = {}
            result[sent_counter]['tags'][tag_counter]['label'] = token.lemma_
            result[sent_counter]['tags'][tag_counter]['synonyms'] = {}
            
            response = requests.get('https://www.synonym.com/synonyms/' + token.lemma_)
            tree = html.fromstring(response.content)
            synonyms = tree.xpath('//li[@class="syn"]/a/text()')
               
            syn_counter = 0 
            for syn in synonyms:
                if (syn_counter < 4):                
                    result[sent_counter]['tags'][tag_counter]['synonyms'][syn_counter] = syn
                syn_counter += 1
            
            
            tag_counter += 1        
        
    result[sent_counter]['shorten_lemma_original'] = shorten_lemma_original.strip().replace("  ", "")
        
    cmd = subprocess.Popen(parser_info, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
    print(sent)
    
        
    cmd.stdin.write(sent.text)

    stdout = cmd.communicate()
    clause_counter = 0
    for line in stdout[0].splitlines():        
        if (line[0] == "1"):
            clause = line.replace('1\t"', "").replace('"\t"', ' ').replace('"', '')
            
            existing = False
            for key,value in result[sent_counter]['clauses'].items():
                if (clause in value['original_clause']):
                    existing = True
                    break
                    
            if (existing == False):
                clause_nlp = nlp(clause)                
                shorten_clause = nlp(' '.join([str(t) for t in clause_nlp if not t.is_stop]))
                
                if (len(shorten_clause) > 1):
                    result[sent_counter]['clauses'][clause_counter] = {}
                    result[sent_counter]['clauses'][clause_counter]['original_clause'] = clause + '.'            
                    
                    shorten_lemma_clause = ""
                    for token in shorten_clause:
                        if (token.lemma_ not in ['.', ',', ';', '-']):
                            shorten_lemma_clause += token.lemma_ + ' '
                    result[sent_counter]['clauses'][clause_counter]['shorten_lemma_clause'] = shorten_lemma_clause.strip().replace("  ", "")
            clause_counter += 1
    sent_counter += 1
    
clauses_merged = ""

for key, value in result.items():
    clauses_merged += "[[" + str(key) + "]]. "    
    for key2, value2 in value['clauses'].items():
        clauses_merged += value2['original_clause'] + " "

print(json.dumps(result))
print(clauses_merged)

nlp = StanfordCoreNLP(r'http://192.168.2.120', port=9000)

props={'timeout': '100000',
       'annotators': 'ssplit,ner,kbp',
       'pipelineLanguage':'en',
       'outputFormat': 'json'
       }


result = nlp.annotate(clauses_merged, properties=props)
#print(result)
result_dict = json.loads(result)    

relations = {}
entities = {}


pronouns = ['he', 'she', 'it', 'we', 'they', 'theirs', 'ours', 'hers', 'his', 'its', 'her', 'his', 'their', 'our']
for sen in result_dict['sentences']:
    
    sent_token = ""
    for token in sen['tokens']:
        sent_token += token["originalText"]
    
    sent_number = re.search("\[\[(.*?)\]\]", sent_token)
    
    if (sent_number != None):        
        sen_count = int(sent_number.group(1))
        entities[sen_count] = {}
        relations[sen_count] = {}
        en_count = 0
        rel_count = 0
        continue
    
    for ent in sen['entitymentions']:
        
        if (ent['text'].lower() not in pronouns):
            
            existing = False
            for key,value in entities[sen_count].items():
                if (value['text'] == ent['text'] and value['ner'] == ent['ner']):
                    existing = True
                    
            if (existing == False):    
                entities[sen_count][en_count] = {}
                entities[sen_count][en_count]['text'] = ent['text']
                entities[sen_count][en_count]['ner'] = ent['ner']
                #print(entities)
                en_count += 1
        
    #if (sen_count in entities):
    #    if (len(entities[sen_count]) == 0):
    #        del entities[sen_count]
    
    for kbp in sen['kbp']:
        
        existing = False
        for key,value in relations[sen_count].items():
            if (value['subject'] == kbp['subject'] and value['relation'] == re.sub(r'.*?\:', '', kbp['relation']) and value['object'] == kbp['object']):
                existing = True
                
        if (existing == False):                
            relations[sen_count][rel_count] = {}
            relations[sen_count][rel_count]['subject'] = kbp['subject']
            relations[sen_count][rel_count]['relation'] = re.sub(r'.*?\:', '', kbp['relation'])
            relations[sen_count][rel_count]['object'] = kbp['object']
            
            for sen2 in result_dict['sentences']:
                for ent in sen2['entitymentions']:
                    if (kbp['subject'] == ent['text']):
                        relations[sen_count][rel_count]['subject_ner'] = ent['ner']
                    if (kbp['object'] == ent['text']):
                        relations[sen_count][rel_count]['object_ner'] = ent['ner']
            
            rel_count += 1
        
    #if (sen_count in relations):
    #    if (len(relations[sen_count]) == 0):
    #       del relations[sen_count]        
    
print(json.dumps(entities))
print(json.dumps(relations))

