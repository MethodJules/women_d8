cd stanford-corenlp-full-2018-10-05
nohup java -Xmx6g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -port 9000 -annotators tokenize,ssplit,pos,ner,kbp,lemma,coref -preload tokenize,ssplit,pos,lemma,ner,depparse,coref,kbp &
