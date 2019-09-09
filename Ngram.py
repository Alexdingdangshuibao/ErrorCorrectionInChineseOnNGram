# -*- coding: utf-8 -*-
import kenlm
import jieba
from pypinyin import lazy_pinyin, Style
import itertools
import os
import sys

#该方法的思路：
#    使用kenlm工具 训练出2/3/4语言模型，将skip_window的值规定在【2,4】区间内，
#    根据滑动窗口，一次对创口内的内容进行替换，替换的方法，根据中文拼音的同音
#    异形字词作为候选，然后选择候选组合中，得分最高的选择进行更改替换。
#    分别针对窗口内容进行2/3/4语言模型的替换，选择各自模型下的最高分，最后在
#    三者中，选择对于整个句子得分最高的作为最终替换
input_file = "Data/data.txt"#初始训练文本路径
data_seg_file = "Data/data_seg.txt"#分词后的文本路径
vocab = "Data/vocab.txt"#生成的词表文件
stop_voc = "Data/stop-voc"#停用词的文件路径
vocab_lazy_pinyin = "Data/vocab-lazy-pinyin.txt"#对词表进行不带音调的拼音注释['zhong', 'xin']
vocab_pinyin = "Data/vocab-pinyin.txt"#对词表进行带音调的拼音注释['zhong1', 'xin1']
def stopwordslist(filepath):
    #根据停词表生成停词list
    stopwords = [line.strip() for line in open(filepath, 'r', encoding='utf-8').readlines()]
    return stopwords

def Generate_vocab(input_file, data_seg_file, vocab, threshold):
    """根据输入文件 生成对应的词表
    @Arguments:
    input_file: 输入文件路径
    data_seg_file: 分词后文本路径
    vocab: 词表文件路径
    threshold: 用于过滤出现次数低于某个值的阈值"""
    #首先对文本进行分词操作
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open(data_seg_file, 'wb+') as f:
        for line in lines:
            content = line.strip('\r\n')
            word_iter = jieba.cut(content)
            word_content = ''
            stopwords = stopwordslist(stop_voc)
            # 消除分词结果中的空格
            for word in word_iter:
                word = word.strip(' ')
                if word not in stopwords:
                    if word != '':
                        word_content += word + ' '
            out_line = '%s\n' % word_content.strip()
            f.write(out_line.encode('utf-8'))
    #根据分词后的文件，进行词表生成
    word_dict = {}
    with open(data_seg_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        content = line.strip('\r\n')
        for word in content.split(' '):
            word_dict.setdefault(word, 0)
            word_dict[word] += 1
    # 根据词语的频率，进行降序排列
    print(word_dict)
    sorted_word_dict = sorted(word_dict.items(), key=lambda d: d[1], reverse=True)
    with open(vocab, 'wb+') as f:
        f.write('<UNK>\t1000000\n'.encode('utf-8'))
        for item in sorted_word_dict:
            if item[1] < threshold:
                continue
            out_line = '%s\t%d\n' % (item[0], item[1])
            f.write(out_line.encode('utf-8'))

def Genvocab_pinyin(vocab, vocab_lazy_pinyin, vocab_piniyin):
    '''根据生成的词表文件，生成每一个词或者字 对应的拼音
    :param vocab: 词表
    :param vocab_lazy_pinyin: 对应的拼音词表  不带音调
    :param vocab_pinyin: 对应的拼音词表 带音调
    :return:
    '''
    with open(vocab, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    with open(vocab_lazy_pinyin, 'wb+') as f:
        for line in lines:
            word_iter = line.split()
            '''
            list = [1, 2, 3, 4, 5]

            ''.join(list) 结果即为：12345

            ','.join(list) 结果即为：1,2,3,4,5'''
            s = ''.join(lazy_pinyin(word_iter[0], style=Style.NORMAL))
            out_line = '%s\t%s\n' % (word_iter[0], s)
            print(out_line)
            f.write(out_line.encode('utf-8'))
    with open(vocab_piniyin, 'wb+') as f:
        for line in lines:
            word_iter = line.split()
            s = ''.join(lazy_pinyin(word_iter[0], style=Style.TONE3))
            out_line = '%s\t%s\n' % (word_iter[0], s)
            f.write(out_line.encode('utf-8'))

def Genvocabpinyin_dict(vocab_lazy_pinyin, vocab_pinyin):
    '''
    生成带音调和不带音调的dict
    :param vocab_lazy_pinyin: 不带音调的拼音注释
    :param vocab_pinyin: 带音调的拼音注释
    :return: 带音调与不带音调的拼音词典
    '''

    word_lazy_pinyin_dict = {}
    word_pinyin_dict = {}
    with open(vocab_lazy_pinyin, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        content = line.split()
        word_lazy_pinyin_dict[content[0]] = content[1]

    with open(vocab_pinyin, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        content = line.split()
        word_pinyin_dict[content[0]] = content[1]
    return word_lazy_pinyin_dict, word_pinyin_dict

def Getword_pinyin(word, lazy_pinyin_dict, pinyin_dict):
    '''
    根据带音调和不带音调的字典 获取改词的拼音
    :param word: 待获取拼音的词
    :param lazy_pinyin_dict: 不带音调的拼音字典
    :param pinyin_dict: 带音调的拼音字典
    :return: 获取词带音调和不带音调的拼音
    '''
    '''
    使用以下这样的方式存在一个弊端 当需要纠正的词不在词库里面时，则无法获取到其注音信息；
    因此建议使用另外一种思路，即直接通过pypinyin库获取其带音调和不带音调的注音
    lazy_pinyin = lazy_pinyin_dict.get(word, '字典中不存在改词对应的拼音')
    pinyin = pinyin_dict.get(word, '字典中不存在改词对应的拼音')
    '''
    lazypinyin = ''.join(lazy_pinyin(word, style=Style.NORMAL))
    pinyin = ''.join(lazy_pinyin(word, style=Style.TONE3))
    return lazypinyin, pinyin

def GenSamepinyin_word(lazy_pinyin, pinyin, lazy_pinyin_dict, pinyin_dict):
    '''
    根据传入的拼音，查询对应字典，获取具有相同拼音的字或词
    :param lazy_pinyin: 不带音调的拼音
    :param pinyin: 带音调的拼音
    :param lazy_pinyin_dict: 不带音调的字典
    :param pinyin_dict: 带音调的字典
    :return: 返回两个对应的list
    '''
    lazy_list = []#对应不带音调的list
    list = []#对应带音调的list

    for item in lazy_pinyin_dict.items():
        if item[1] == lazy_pinyin:
            lazy_list.append(item[0])

    for item in pinyin_dict.items():
        if item[1] == pinyin:
            list.append(item[0])
    return lazy_list, list

#统计句子中待替换的位置数，即是 句子中‘*###*’个数
def get_target_num(module_list):
    #返回某一行的a或an的数量
    count = 0
    for item in module_list:
        if item == '*###*':
            count = count+1
    return count

def Generate_sentence(module_list,list):
    '''
    生成替换后的句子，即是将module中的‘*###*’依次替换成list中的值
    :param module_list: 待替换的句子模板
    :param list: 替换候选项
    :return: 返回更改后的句子
    '''
    new_sentence = []
    j = 0
    for i in range(len(module_list)):
        if module_list[i] == '*###*':
            new_sentence.append(list[j])
            j = j+1
        else:
            new_sentence.append(module_list[i])
        i = i+1
    return new_sentence

#第一步，对输入的待检验的句子进行分词处理
def CutSentence(sentence):
    '''
    进行分词 并将结果以列表的形式返回
    :param sentence: 待分词的句子
    :return: 分词后的结果 list
    '''
    cut_list = []
    content = sentence.strip('\r\n')
    word_iter = jieba.cut(content)
    stopwords = stopwordslist(stop_voc)
    # 消除分词结果中的空格
    for word in word_iter:
        word = word.strip(' ')
        if word not in stopwords:
            if word != '':
                cut_list.append(word)
    return cut_list

#第二步 根据原始句子和分词结果，生成待替换的句子模板
def Genmodule(sentence, cut_list):
    '''
    生成待替换的句子模板
    :param sentence: 原始句子
    :param cut_list: 句子的分词结果
    :return:
    '''
    #将原始句子，通过分词从一个String转变为一个list，方便模板的建立
    sentence_list= []
    sentence_content = jieba.cut(sentence)
    # 消除分词结果中的空格
    for word in sentence_content:
        word = word.strip(' ')
        if word != '':
            sentence_list.append(word)
    j = 0
    print(len(sentence_list))
    for i in range(len(sentence_list)):
        if j == len(cut_list):
            break
        if cut_list[j] == sentence_list[i]:
            sentence_list[i] = '*###*'
            j = j+1
        i = i+1
    return sentence_list

#第三步 根据句子的分词结果，生成每个位置对应的候选项
def GenCandicate(cut_list, vocab_lazy_pinyin, vocab_pinyin):
    '''
    生成对应位置的候选项 以列表方式存储
    :param cut_list: 原始句子的分词结果（即可替换项）
    :param vocab_lazy_pinyin: 不带音调的注释拼音文本
    :param vocab_pinyin: 带音调的注释拼音文本
    :return:
    '''
    word_lazy_pinyin_dict, word_pinyin_dict = Genvocabpinyin_dict(vocab_lazy_pinyin,
                                                                  vocab_pinyin)
    All_lazy_list = []#用来记录所有带音调的拼音候选项列表
    All_list = []#用来记录所有不带音调的拼音候选列表
    for word in cut_list:
        lazy_pinyin , pinyin = Getword_pinyin(word, word_lazy_pinyin_dict, word_pinyin_dict)
        lazy_list, list = GenSamepinyin_word(lazy_pinyin, pinyin, word_lazy_pinyin_dict, word_pinyin_dict)
        #如果没有找到同样拼音的候选项，则用原来的词语替代
        if len(lazy_list) == 0 and len(list) == 0:
            lazy_list.append(word)
            list.append(word)
        All_lazy_list.append(lazy_list)
        All_list.append(list)
    return All_lazy_list, All_list

#第四步，根据生成的模板和候选项进行替换，生成候选句子
def ChangeSentence(module_list, All_lazy_list, All_list):
    '''
    将模板中的‘*###*’依次替换为候选项中的值 ，生成一个候选项句子集合
    :param module_list: 替换模板list
    :param All_lazy_list: 待替换的lazy候选项
    :param All_list: 待替换的带音调的候选项
    :return:
    '''
    count = get_target_num(module_list)
    All_lazy_res = []
    All_res = []
    '''
    All_list=[[1,2],[3,4],[5,6]]
    for item in itertools.product(All_list[0], All_list[1], All_list[2]):
        print(item)
    for item in itertools.product(*All_list):
        print(item)
    上述两种方法效果一样
    '''
    #根据count 生成排列组合
    all_lazy_iters = list(itertools.product(*All_lazy_list))
    all_iters = list(itertools.product(*All_list))
    print(all_lazy_iters)
    print(all_iters)
    for iter in all_lazy_iters:#取一个组合  对原句子的###进行替换
        new_sentence_list = Generate_sentence(module_list, iter)#得到替换后的新句子
        All_lazy_res.append(new_sentence_list)#res存储基于所有组合，替换后的新句子
    for iter in all_iters:#取一个组合  对原句子的###进行替换
        new_sentence_list = Generate_sentence(module_list, iter)#得到替换后的新句子
        All_res.append(new_sentence_list)#res存储基于所有组合，替换后的新句

    return All_lazy_res, All_res

#第五步，对所有的候选生成的句子进行评分，取最高分的句子为最后结果
def GetResult(sentence, All_lazy_res, All_res):
    '''
    对句子进行打分，获取最高分的结果
    :param setence: 原始句子
    :param All_lazy_res: 不带音调的句子备选
    :param All_res: 带音调的句子备选
    :return: 最终得分最高的句子
    '''
    sentence_list= []
    sentence_content = jieba.cut(sentence)
    # 消除分词结果中的空格
    for word in sentence_content:
        word = word.strip(' ')
        if word != '':
            sentence_list.append(word)
    top_score = model.score(' '.join(sentence_list))#将原始句子作为最高分
    best_sentence = ''
    print("原始句子得分为：")
    print(top_score)
    print('######采用不带音调的候选次进行替换######')
    for lazy_sentence in All_lazy_res:
        s = ' '.join(lazy_sentence)
        score = model.score(s)
        num_list_new = [str(x) for x in lazy_sentence]  # 避免list中有数字
        new_sentence = "".join(num_list_new)
        print(new_sentence + '该句子得分为：')
        print(score)
        print('------------------------------------')
        if score > top_score:
            best_sentence = new_sentence
            top_score = score
    print('######采用带音调的候选次进行替换######')
    for sentence in All_res:
        s = ' '.join(sentence)
        score = model.score(s)
        num_list_new = [str(x) for x in sentence]#避免list中有数字
        new_sentence = "".join(num_list_new)
        print(new_sentence + '该句子得分为：')
        print(score)
        print('------------------------------------')
        if score > top_score:
            best_sentence = new_sentence
            top_score = score
            print("eqeq"+best_sentence)
    print(top_score)
    print(best_sentence)
    return best_sentence
#Generate_vocab(input_file, data_seg_file, vocab, 3)
#Genvocab_pinyin(vocab, vocab_lazy_pinyin, vocab_pinyin)


model = kenlm.LanguageModel("/root/kenlm/build/ngram.bin")#ngram.bin 为一个trigram
sentence = "徐凤年成为了天下地衣之后，非常西环喝酒。因此，没过多久之后，他在和别人的战豆中又一次是白了"
cut_list = CutSentence(sentence)
print(cut_list)

model_result = Genmodule(sentence, cut_list)
print(model_result)

All_lazy_list, All_list = GenCandicate(cut_list, vocab_lazy_pinyin, vocab_pinyin)
print(All_lazy_list)
print(All_list)

All_lazy_res, All_res = ChangeSentence(model_result, All_lazy_list, All_list)
print(All_lazy_res)
print(All_res)

best_sentence = GetResult(sentence, All_lazy_res, All_res)
print(best_sentence)






#定义需要使用到的一些变量
skip_window = 2 #滑动窗口大小
Ngram = 2 #使用到的语言模型
Thread = 1 #进行概率比较的阈值大小
