# -*- coding: utf-8 -*-
import math
import os
import tensorflow as tf
import numpy as np
import pandas as pd
import pickle
import pickle as pkl
import cv2
import skimage

import tensorflow.python.platform
from tensorflow.python.ops import rnn
from keras.preprocessing import sequence
from collections import Counter
from collections import defaultdict
import itertools
test_image_path='./data/acoustic-guitar-player.jpg'
vgg_path='./data/vgg16-20160129.tfmodel'
n=2**19-3
def map_lambda():
    return n+1
def rev_map_lambda():
    return "<UNK>"
def load_text(n,capts=None,num_samples=None):
    # fname = 'Oxford_English_Dictionary.txt'
    # txt = []
    # with open(fname,'rb') as f:
    #   txt = f.readlines()

    # txt = [x.decode('utf-8').strip() for x in txt]
    # txt = [re.sub(r'[^a-zA-Z ]+', '', x) for x in txt if len(x) > 1]

    # List of words
    # word_list = [x.split(' ', 1)[0].strip() for x in txt]
    # # List of definitions
    # def_list = [x.split(' ', 1)[1].strip()for x in txt]
    with open('./training_data/training_data.pkl','rb') as raw:
        word_list,dl=pkl.load(raw)
    def_list=[] 
    # def_list=[' '.join(defi) for defi in def_list]
    i=0
    while i<len( dl):
        defi=dl[i]
        if len(defi)>0:
            def_list+=[' '.join(defi)]
            i+=1
        else:
            dl.pop(i)
            word_list.pop(i)


    maxlen=0
    minlen=100
    for defi in def_list:
        minlen=min(minlen,len(defi.split()))
        maxlen=max(maxlen,len(defi.split()))
    print(minlen)
    print(maxlen)
    maxlen=30

    # # Initialize the "CountVectorizer" object, which is scikit-learn's
    # # bag of words tool.  
    # vectorizer = CountVectorizer(analyzer = "word",   \
    #                              tokenizer = None,    \
    #                              preprocessor = None, \
    #                              stop_words = None,   \
    #                              max_features = None, \
    #                              token_pattern='\\b\\w+\\b') # Keep single character words

    # _map,rev_map=get_one_hot_map(word_list,def_list,n)
    _map=pkl.load(open('maps.pkl','rb'))
    rev_map=pkl.load(open('rev_maps.pkl','rb'))
    if num_samples is not None:
        if capts is not None:
            num_samples=len(capts)
        else:
            num_samples=len(word_list)
    # X = map_one_hot(word_list[:num_samples],_map,1,n)
    # y = (36665, 56210)
    # print _map
    # y,mask = map_one_hot(capts[:num_samples],_map,maxlen,n)
    # np.save('X',X)
    # np.save('yc',y)
    # np.save('maskc',mask)
    X=np.load('Xs.npy','r')
    if capts is not None:
        y=np.load('yc.npy','r')
        mask=np.load('maskc.npy','r')
    else:
        y=np.load('ys.npy','r')
        mask=np.load('masks.npy','r')
    print (np.max(y))
    return X, y, mask,rev_map

def get_one_hot_map(to_def,corpus,n):
    # words={}
    # for line in to_def:
    #   if line:
    #       words[line.split()[0]]=1

    

    # counts=defaultdict(int)
    # uniq=defaultdict(int)
    # for line in corpus:
    #   for word in line.split():
    #       if word not in words:
    #           counts[word]+=1
    # words=list(words.keys())
    words=[]
    counts=defaultdict(int)
    uniq=defaultdict(int)
    for line in to_def+corpus:
        for word in line.split():
            if word not in words:
                counts[word]+=1
    _map=defaultdict(lambda :n+1)
    rev_map=defaultdict(lambda:"<UNK>")
    # words=words[:25000]
    for i in counts.values():
        uniq[i]+=1
    print (len(words))
    # random.shuffle(words)

    words+=list(map(lambda z:z[0],reversed(sorted(counts.items(),key=lambda x:x[1]))))[:n-len(words)]
    print (len(words))
    i=0
    # random.shuffle(words)
    for num_bits in range(binary_dim):
        for bit_config in itertools.combinations_with_replacement(range(binary_dim),num_bits+1):
            bitmap=np.zeros(binary_dim)
            bitmap[np.array(bit_config)]=1
            num=bitmap*(2** np.arange(binary_dim ))
            num=np.sum(num).astype(np.uint32)
            word=words[i]
            _map[word]=num
            rev_map[num]=word
            i+=1
            if i>=len(words):
                break
        if i>=len(words):
                break
    #   for word in words:
    #       i+=1
    #       _map[word]=i
    #       rev_map[i]=word
    rev_map[n+1]='<UNK>'
    if zero_end_tok:
        rev_map[0]='.'
    else:
        rev_map[0]='Start'
        rev_map[n+2]='End'
    print (list(reversed(sorted(uniq.items()))))
    print (len(list(uniq.items())))
    # print rev_map
    return _map,rev_map
def map_word_emb(corpus,_map):
    ### NOTE: ONLY WORKS ON TARGET WORD (DOES NOT HANDLE UNK PROPERLY)
    rtn=[]
    rtn2=[]
    for word in corpus:
        mapped=_map[word]
        rtn.append(mapped)
        if get_rand_vec:
            mapped_rand=random.choice(list(_map.keys()))
            while mapped_rand==word:
                mapped_rand=random.choice(list(_map.keys()))
            mapped_rand=_map[mapped_rand]
            rtn2.append(mapped_rand)
    if get_rand_vec:
        return np.array(rtn),np.array(rtn2)
    return np.array(rtn)

def map_one_hot(corpus,_map,maxlen,n):
    if maxlen==1:
        if not form2:
            total_not=0
            rtn=np.zeros([len(corpus),n+3],dtype=np.float32)
            for l,line in enumerate(corpus):
                if len(line)==0:
                    rtn[l,-1]=1
                else:
                    mapped=_map[line]
                    if mapped==75001:
                        total_not+=1
                    rtn[l,mapped]=1
            print (total_not,len(corpus))
            return rtn
        else:
            total_not=0
            if not onehot:
                rtn=np.zeros([len(corpus),binary_dim],dtype=np.float32)
            else:
                rtn=np.zeros([len(corpus),2**binary_dim],dtype=np.float32)
            for l,line in enumerate(corpus):
            # if len(line)==0:
            #   rtn[l]=n+2
            # else:
            #   if line not in _map:
            #       total_not+=1
                mapped=_map[line]
                if mapped==75001:
                    total_not+=1
                if onehot:
                    binrep=np.zeros(2**binary_dim)
                    print line
                    binrep[mapped]=1
                else:
                    binrep=(1&(mapped/(2**np.arange(binary_dim))).astype(np.uint32)).astype(np.float32)
                rtn[l]=binrep
            print (total_not,len(corpus))
            return rtn
    else:
        if form2:
            rtn=np.zeros([len(corpus),maxlen+2,binary_dim],dtype=np.float32)
        else:
            rtn=np.zeros([len(corpus),maxlen+2],dtype=np.int32)
        print (rtn.shape)
        mask=np.zeros([len(corpus),maxlen+2],dtype=np.float32)
        print (mask.shape)
        mask[:,1]=1.0
        totes=0
        nopes=0
        wtf=0
        for l,_line in enumerate(corpus):
            x=0
            line=_line.split()
            for i in range(min(len(line),maxlen)):
                # if line[i] not in _map:
                #   nopes+=1

                mapped=_map[line[i]]
                if form2:
                    binrep=(1&(mapped/(2**np.arange(binary_dim))).astype(np.uint32)).astype(np.float32)
                    rtn[l,i+1,:]=binrep
                else:
                    rtn[l,i+1]=mapped
                if mapped==75001:
                    wtf+=1
                mask[l,i+1]=1.0
                totes+=1
                x=i+1
            to_app=n+2
            if zero_end_tok:
                to_app=0
            if form2:
                rtn[l,x+1,:]=(1&(to_app/(2**np.arange(binary_dim))).astype(np.uint32)).astype(np.float32)
            else:
                rtn[l,x+1]=to_app
            mask[l,x+1]=1.0

        print (nopes,totes,wtf)
        return rtn,mask


def xavier_init(fan_in, fan_out, constant=1e-4): 
    """ Xavier initialization of network weights"""
    # https://stackoverflow.com/questions/33640581/how-to-do-xavier-initialization-on-tensorflow
    low = -constant*np.sqrt(6.0/(fan_in + fan_out)) 
    high = constant*np.sqrt(6.0/(fan_in + fan_out))
    return tf.random_uniform((fan_in, fan_out), 
                             minval=low, maxval=high, 
                             dtype=tf.float32)

class Caption_Generator():
    def __init__(self, dim_in, dim_embed, dim_hidden, batch_size, n_lstm_steps, n_words, init_b=None,from_image=False,n_input=None,n_lstm_input=None,n_z=None):

        self.dim_in = dim_in
        self.dim_embed = dim_embed
        self.dim_hidden = dim_hidden
        self.batch_size = batch_size
        self.n_lstm_steps = n_lstm_steps
        self.n_words = n_words
        self.n_input = n_input
        self.n_lstm_input=n_lstm_input
        self.n_z=n_z
        
        if from_image: 
            with open(vgg_path,'rb') as f:
                fileContent = f.read()
                graph_def = tf.GraphDef()
                graph_def.ParseFromString(fileContent)
            self.images = tf.placeholder("float32", [1, 224, 224, 3])
            tf.import_graph_def(graph_def, input_map={"images":self.images})
            graph = tf.get_default_graph()
            self.sess = tf.InteractiveSession(graph=graph)

        self.from_image=from_image

        # declare the variables to be used for our word embeddings
        self.word_embedding = tf.Variable(tf.random_uniform([self.n_z, self.dim_embed], -0.1, 0.1), name='word_embedding')

        self.embedding_bias = tf.Variable(tf.zeros([dim_embed]), name='embedding_bias')
        
        # declare the LSTM itself
        self.lstm = tf.contrib.rnn.BasicLSTMCell(dim_hidden)
        
        # declare the variables to be used to embed the image feature embedding to the word embedding space
        self.img_embedding = tf.Variable(tf.random_uniform([dim_in, dim_hidden], -0.1, 0.1), name='img_embedding')
        self.img_embedding_bias = tf.Variable(tf.zeros([dim_hidden]), name='img_embedding_bias')

        # declare the variables to go from an LSTM output to a word encoding output
        self.word_encoding = tf.Variable(tf.random_uniform([dim_hidden, n_words], -0.1, 0.1), name='word_encoding')
        # initialize this bias variable from the preProBuildWordVocab output
        # optional initialization setter for encoding bias variable 
        if init_b is not None:
            self.word_encoding_bias = tf.Variable(init_b, name='word_encoding_bias')
        else:
            self.word_encoding_bias = tf.Variable(tf.zeros([n_words]), name='word_encoding_bias')

        self.embw=tf.Variable(xavier_init(self.n_input,self.n_z),name='embw')
        self.embb=tf.Variable(tf.zeros([self.n_z]),name='embb')
        self.all_encoding_weights=[self.embw,self.embb]

    def build_model(self):
        # declaring the placeholders for our extracted image feature vectors, our caption, and our mask
        # (describes how long our caption is with an array of 0/1 values of length `maxlen`  
        img = tf.placeholder(tf.float32, [self.batch_size, self.dim_in])
        caption_placeholder = tf.placeholder(tf.float32, [self.batch_size, self.n_lstm_steps, self.n_input])
        mask = tf.placeholder(tf.float32, [self.batch_size, self.n_lstm_steps])
        self.output_placeholder = tf.placeholder(tf.int32, [self.batch_size, self.n_lstm_steps])

        network_weights = self._initialize_weights()
        
        # getting an initial LSTM embedding from our image_imbedding
        image_embedding = tf.matmul(img, self.img_embedding) + self.img_embedding_bias
        
        flat_caption_placeholder=tf.reshape(caption_placeholder,[self.batch_size*self.n_lstm_steps,-1])

        #leverage one-hot sparsity to lookup embeddings fast
        embedded_input,KLD_loss=self._get_word_embedding([network_weights['variational_encoding'],network_weights['biases_variational_encoding']],network_weights['input_meaning'],flat_caption_placeholder,logit=True)
        KLD_loss=tf.multiply(KLD_loss,tf.reshape(mask,[-1,1]))
        KLD_loss=tf.reduce_sum(KLD_loss)
        embedded_input=tf.matmul(embedded_input,self.word_embedding)+self.embedding_bias
        word_embeddings=tf.reshape(embedded_input,[self.batch_size,self.n_lstm_steps,-1])
        #initialize lstm state
        state = self.lstm.zero_state(self.batch_size, dtype=tf.float32)
        rnn_output=[]
        with tf.variable_scope("RNN"):
            # unroll lstm
            for i in range(self.n_lstm_steps): 
                if i > 0:
                   # if this isn’t the first iteration of our LSTM we need to get the word_embedding corresponding
                   # to the (i-1)th word in our caption 
                    
                    current_embedding = word_embeddings[:,i-1,:]
                else:
                     #if this is the first iteration of our LSTM we utilize the embedded image as our input 
                    current_embedding = image_embedding
                if i > 0: 
                    # allows us to reuse the LSTM tensor variable on each iteration
                    tf.get_variable_scope().reuse_variables()

                out, state = self.lstm(current_embedding, state)

                rnn_output.append(tf.expand_dims(out,1))
        #perform classification of output
        rnn_output=tf.concat(rnn_output,axis=1)
        rnn_output=tf.reshape(rnn_output,[self.batch_size*self.n_lstm_steps,-1])
        encoded_output=tf.matmul(rnn_output,self.word_encoding)+self.word_encoding_bias
        #get loss
        xentropy=tf.nn.sparse_softmax_cross_entropy_with_logits(logits=encoded_output,labels=tf.reshape(self.output_placeholder,[-1]))

        #mask zero embeddings
        masked_xentropy=tf.multiply(tf.reshape(xentropy,[self.batch_size,-1])[:,1:],mask[:,1:])
        #average over timeseries length

        total_loss=tf.reduce_sum(masked_xentropy)/tf.reduce_sum(mask[:,1:])
        self.print_loss=total_loss
        total_loss+=KLD_loss/tf.reduce_sum(mask)
        return total_loss, img,  caption_placeholder, mask

    def build_generator(self, maxlen, batchsize=1,from_image=False):
        #same setup as `build_model` function

        img = tf.placeholder(tf.float32, [self.batch_size, self.dim_in])
        image_embedding = tf.matmul(img, self.img_embedding) + self.img_embedding_bias
        state = self.lstm.zero_state(batchsize,dtype=tf.float32)

        #declare list to hold the words of our generated captions
        all_words = []
        with tf.variable_scope("RNN"):
            # in the first iteration we have no previous word, so we directly pass in the image embedding
            # and set the `previous_word` to the embedding of the start token ([0]) for the future iterations
            output, state = self.lstm(image_embedding, state)
            previous_word = tf.nn.embedding_lookup(self.word_embedding, [0]) + self.embedding_bias

            for i in range(maxlen):
                tf.get_variable_scope().reuse_variables()

                out, state = self.lstm(previous_word, state)


                # get a get maximum probability word and it's encoding from the output of the LSTM
                logit = tf.matmul(out, self.word_encoding) + self.word_encoding_bias
                best_word = tf.argmax(logit, 1)

                with tf.device("/cpu:0"):
                    # get the embedding of the best_word to use as input to the next iteration of our LSTM 
                    previous_word = tf.nn.embedding_lookup(self.word_embedding, best_word)

                previous_word += self.embedding_bias

                all_words.append(best_word)
        self.img=img
        self.all_words=all_words
        return img, all_words
    def _initialize_weights(self):
        all_weights = dict()
        trainability=True
        if not same_embedding:
            all_weights['input_meaning'] = {
                'affine_weight': tf.Variable(xavier_init(self.n_z, self.n_lstm_input),name='affine_weight',trainable=trainability),
                'affine_bias': tf.Variable(tf.zeros(self.n_lstm_input),name='affine_bias',trainable=trainability)}
        if not vanilla:
            all_weights['biases_variational_encoding'] = {
                'out_mean': tf.Variable(tf.zeros([self.n_z], dtype=tf.float32),name='out_meanb',trainable=trainability),
                'out_log_sigma': tf.Variable(tf.zeros([self.n_z], dtype=tf.float32),name='out_log_sigmab',trainable=trainability)}
            all_weights['variational_encoding'] = {
                'out_mean': tf.Variable(xavier_init(self.n_z, self.n_z),name='out_mean',trainable=trainability),
                'out_log_sigma': tf.Variable(xavier_init(self.n_z, self.n_z),name='out_log_sigma',trainable=trainability)}
            
        else:
            all_weights['biases_variational_encoding'] = {
                'out_mean': tf.Variable(tf.zeros([self.n_z], dtype=tf.float32),name='out_meanb',trainable=trainability)}
            all_weights['variational_encoding'] = {
                'out_mean': tf.Variable(xavier_init(self.n_z, self.n_z),name='out_mean',trainable=trainability)}
            
        # self.no_reload+=all_weights['input_meaning'].values()
        # self.var_embs=[]
        # if transfertype2:
        #     self.var_embs=all_weights['biases_variational_encoding'].values()+all_weights['variational_encoding'].values()

        # self.lstm=tf.contrib.rnn.BasicLSTMCell(n_lstm_input)
        # if lstm_stack>1:
        #     self.lstm=tf.contrib.rnn.MultiRNNCell([self.lstm]*lstm_stack)
        # all_weights['LSTM'] = {
        #     'affine_weight': tf.Variable(xavier_init(n_z, n_lstm_input),name='affine_weight2'),
        #     'affine_bias': tf.Variable(tf.zeros(n_lstm_input),name='affine_bias2'),
        #     'encoding_weight': tf.Variable(xavier_init(n_lstm_input,n_input),name='encoding_weight'),
        #     'encoding_bias': tf.Variable(tf.zeros(n_input),name='encoding_bias'),
        #     'lstm': self.lstm}
        all_encoding_weights=[all_weights[x].values() for x in all_weights]
        
        for w in all_encoding_weights:
            self.all_encoding_weights+=w
        return all_weights
    def _get_word_embedding(self, ve_weights, lstm_weights, x,logit=False):
        x=tf.matmul(x,self.embw)+self.embb
        if logit:
            z,vae_loss=self._vae_sample(ve_weights[0],ve_weights[1],x)
        else:
            if not form2:
                z,vae_loss=self._vae_sample(ve_weights[0],ve_weights[1],x, True)
            else:
                z,vae_loss=self._vae_sample(ve_weights[0],ve_weights[1],tf.one_hot(x,depth=self.n_input))
                all_the_f_one_h.append(tf.one_hot(x,depth=self.n_input))

        embedding=tf.matmul(z,lstm_weights['affine_weight'])+lstm_weights['affine_bias']
        embedding=z
        return embedding,vae_loss
    def _vae_sample(self, weights, biases, x, lookup=False):
            #TODO: consider adding a linear transform layer+relu or softplus here first 
            if not lookup:
                mu=tf.matmul(x,weights['out_mean'])+biases['out_mean']
                if not vanilla:
                    logvar=tf.matmul(x,weights['out_log_sigma'])+biases['out_log_sigma']
            else:
                mu=tf.nn.embedding_lookup(weights['out_mean'],x)+biases['out_mean']
                if not vanilla:
                    logvar=tf.nn.embedding_lookup(weights['out_log_sigma'],x)+biases['out_log_sigma']

            if not vanilla:
                epsilon=tf.random_normal(tf.shape(logvar),name='epsilon')
                std=tf.exp(.5*logvar)
                z=mu+tf.multiply(std,epsilon)
            else:
                z=mu
            KLD=0.0
            if not vanilla:
                KLD = -0.5 * tf.reduce_sum(1 + logvar - tf.pow(mu, 2) - tf.exp(logvar),axis=-1)
                print logvar.shape,epsilon.shape,std.shape,z.shape,KLD.shape
            return z,KLD
    def crop_image(self,x, target_height=227, target_width=227, as_float=True,from_path=True):
        #image preprocessing to crop and resize image
        image = (x)
        if from_path==True:
            image=cv2.imread(image)
        if as_float:
            image = image.astype(np.float32)

        if len(image.shape) == 2:
            image = np.tile(image[:,:,None], 3)
        elif len(image.shape) == 4:
            image = image[:,:,:,0]

        height, width, rgb = image.shape
        if width == height:
            resized_image = cv2.resize(image, (target_height,target_width))

        elif height < width:
            resized_image = cv2.resize(image, (int(width * float(target_height)/height), target_width))
            cropping_length = int((resized_image.shape[1] - target_height) / 2)
            resized_image = resized_image[:,cropping_length:resized_image.shape[1] - cropping_length]

        else:
            resized_image = cv2.resize(image, (target_height, int(height * float(target_width) / width)))
            cropping_length = int((resized_image.shape[0] - target_width) / 2)
            resized_image = resized_image[cropping_length:resized_image.shape[0] - cropping_length,:]

        return cv2.resize(resized_image, (target_height, target_width))

    def read_image(self,path=None):
        # parses image from file path and crops/resizes
        if path is None:
            path=test_image_path
        img = crop_image(path, target_height=224, target_width=224)
        if img.shape[2] == 4:
            img = img[:,:,:3]

        img = img[None, ...]
        return img

    def get_caption(self,x=None):
        #gets caption from an image by feeding it through imported VGG16 graph
        if self.from_image:
            feat = read_image(x)
            fc7 = self.sess.run(graph.get_tensor_by_name("import/Relu_1:0"), feed_dict={self.images:feat})
        else:
            fc7=np.load(x,'r')
        
        generated_word_index= self.sess.run(self.generated_words, feed_dict={self.img:fc7})
        generated_word_index = np.hstack(generated_word_index)
        generated_words = [ixtoword[x] for x in generated_word_index]
        punctuation = np.argmax(np.array(generated_words) == '.')+1

        generated_words = generated_words[:punctuation]
        generated_sentence = ' '.join(generated_words)
        return (generated_sentence)
def get_data(annotation_path, feature_path):
    #load training/validation data
    annotations = pd.read_table(annotation_path, sep='\t', header=None, names=['image', 'caption'])
    return np.load(feature_path,'r'), annotations['caption'].values
def preProBuildWordVocab(sentence_iterator, word_count_threshold=30): # function from Andre Karpathy's NeuralTalk
    #process and vectorize training/validation captions
    print('preprocessing %d word vocab' % (word_count_threshold, ))
    word_counts = {}
    nsents = 0
    for sent in sentence_iterator:
      nsents += 1
      for w in sent.lower().split(' '):
        word_counts[w] = word_counts.get(w, 0) + 1
    vocab = [w for w in word_counts if word_counts[w] >= word_count_threshold]
    print('preprocessed words %d -> %d' % (len(word_counts), len(vocab)))

    ixtoword = {}
    ixtoword[0] = '.'  
    wordtoix = {}
    wordtoix['#START#'] = 0 
    ix = 1
    for w in vocab:
      wordtoix[w] = ix
      ixtoword[ix] = w
      ix += 1

    word_counts['.'] = nsents
    bias_init_vector = np.array([1.0*word_counts[ixtoword[i]] for i in ixtoword])
    bias_init_vector /= np.sum(bias_init_vector) 
    bias_init_vector = np.log(bias_init_vector)
    bias_init_vector -= np.max(bias_init_vector) 
    return wordtoix, ixtoword, bias_init_vector.astype(np.float32)

dim_embed = 256
dim_hidden = 256
dim_in = 4096
batch_size = 128
momentum = 0.9
n_epochs = 25

def train(learning_rate=0.001, continue_training=False):
    
    tf.reset_default_graph()

    feats, captions = get_data(annotation_path, feature_path)
    wordtoix, ixtoword, init_b = preProBuildWordVocab(captions)

    np.save('data/ixtoword', ixtoword)

    print ('num words:',len(ixtoword))

    


    sess = tf.InteractiveSession()
    n_words = len(wordtoix)
    maxlen = 30
    X, final_captions, mask, _map = load_text(2**19-3,captions)
    X,y,aux_mask,_map
    running_decay=1
    decay_rate=0.9999302192204246
    with tf.device('/gpu:0'):
        caption_generator = Caption_Generator(dim_in, dim_hidden, dim_embed, batch_size, maxlen+2, n_words, init_b,n_input=n_input,n_lstm_input=n_lstm_input,n_z=n_z)

        loss, image, sentence, mask = caption_generator.build_model()

    saver = tf.train.Saver(max_to_keep=100)
    train_op = tf.train.AdamOptimizer(learning_rate).minimize(loss)
    tf.global_variables_initializer().run()
    tf.train.Saver(var_list=caption_generator.all_encoding_weights,max_to_keep=100).restore(sess,tf.train.latest_checkpoint('modelsvardefdefsingle'))
    if continue_training:
        saver.restore(sess,tf.train.latest_checkpoint(model_path))
    losses=[]

    for epoch in range(n_epochs):
        if epoch==1:
            for w in caption_generator.all_encoding_weights:
                w.trainable=True
        index = (np.arange(len(feats)).astype(int))
        np.random.shuffle(index)
        index=index[:]
        i=0
        for start, end in zip( range(0, len(index), batch_size), range(batch_size, len(index), batch_size)):
            #format data batch
            current_feats = feats[index[start:end]]
            current_captions = captions[index[start:end]]
            current_caption_ind = [x for x in map(lambda cap: [wordtoix[word] for word in cap.lower().split(' ')[:-1] if word in wordtoix], current_captions)]

            current_caption_matrix = sequence.pad_sequences(current_caption_ind, padding='post', maxlen=maxlen+1)
            current_caption_matrix = np.hstack( [np.full( (len(current_caption_matrix),1), 0), current_caption_matrix] )

            current_mask_matrix = np.zeros((current_caption_matrix.shape[0], current_caption_matrix.shape[1]))
            nonzeros = np.array([x for x in map(lambda x: (x != 0).sum()+2, current_caption_matrix )])
            current_capts=final_captions[index[start:end]]

            for ind, row in enumerate(current_mask_matrix):
                row[:nonzeros[ind]] = 1

            _, loss_value,total_loss = sess.run([train_op, caption_generator.print_loss,loss], feed_dict={
                image: current_feats.astype(np.float32),
                caption_generator.output_placeholder : current_caption_matrix.astype(np.int32),
                mask : current_mask_matrix.astype(np.float32),
                sentence : current_capts.astype(np.float32)
                })

            print("Current Cost: ", loss_value, "\t Epoch {}/{}".format(epoch, n_epochs), "\t Iter {}/{}".format(start,len(feats)))
            losses.append(loss_value*running_decay)
            # if epoch<9:
            #     if i%3==0:
            #         running_decay*=decay_rate
            # else:
            #     if i%8==0:
            #         running_decay*=decay_rate
            i+=1
            print losses[-1]
        print("Saving the model from epoch: ", epoch)
        pkl.dump(losses,open('losses/loss.pkl','wb'))
        saver.save(sess, os.path.join(model_path, 'model'), global_step=epoch)
        learning_rate *= 0.95
def test(sess,image,generated_words,ixtoword,idx=0): # Naive greedy search

    feats, captions = get_data(annotation_path, feature_path)
    feat = np.array([feats[idx]])
    
    saver = tf.train.Saver()
    sanity_check= False
    # sanity_check=True
    if not sanity_check:
        saved_path=tf.train.latest_checkpoint(model_path)
        saver.restore(sess, saved_path)
    else:
        tf.global_variables_initializer().run()

    generated_word_index= sess.run(generated_words, feed_dict={image:feat})
    generated_word_index = np.hstack(generated_word_index)

    generated_sentence = [ixtoword[x] for x in generated_word_index]
    print(generated_sentence)

if __name__=='__main__':

    model_path = './models/tensorflow_e2e'
    feature_path = './data/feats.npy'
    annotation_path = './data/results_20130124.token'
    import sys
    feats, captions = get_data(annotation_path, feature_path)
    n_input=19
    binary_dim=n_input
    n_lstm_input=1024
    n_z=512
    zero_end_tok=True
    form2=True
    vanilla=True
    onehot=False
    same_embedding=False

    if sys.argv[1]=='train':
        train()
    elif sys.argv[1]=='test':
        ixtoword = np.load('data/ixtoword.npy').tolist()
        n_words = len(ixtoword)
        maxlen=15
        sess = tf.InteractiveSession()
        batch_size=1
        caption_generator = Caption_Generator(dim_in, dim_hidden, dim_embed, 1, maxlen+2, n_words,n_input=n_input,n_lstm_input=n_lstm_input,n_z=n_z)


        image, generated_words = caption_generator.build_generator(maxlen=maxlen)
        test(sess,image,generated_words,ixtoword,1)