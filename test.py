# -*- coding: utf-8 -*-
import codecs
from collections import Counter
import nltk
import itertools
import kenlm


model = kenlm.LanguageModel("/root/kenlm/build/new.bin")
#读取文件内容
def readfile(filepath):
    fp = codecs.open(filepath, "r", encoding="utf-8")
    content = fp.read()
    fp.close()
    return  content

#按行加载文件
#对文件内容进行行切分 返回一个列表
def read_words_list(filepath):
    wordslist = readfile(filepath).splitlines()
    return wordslist

#保存文件的方法
def save_file(savepath, content):
    fp = codecs.open(savepath, "a", encoding="utf-8")
    fp.write(content)
    fp.close()

#统计句子的a和an个数
def get_target_num(line):
    #返回某一行的a或an的数量
    if "a" in line or "an" in line:
        count = Counter(nltk.word_tokenize(line))["a"] + Counter(nltk.word_tokenize(line))["an"]
    return count

#对a和an分布的可能性进行枚举，然后对句子中a和an所在的位置进行替换插入
def generate_candidate_list(template_str, count):
    res = []
    tem_arr = template_str.split()
    #根据count 生成排列组合
    all_iters = list(itertools.product(("a", "an"), repeat = count))
    for iter in all_iters:#取一个组合  对原句子的###进行替换
        sentence = generate_sentence(tem_arr, iter)#得到替换后的新句子
        res.append(sentence)#res存储基于所有组合，替换后的新句子
    return res

#将列表中的数据插入到句子的占位符中
def generate_sentence(tem_arr, iter):
    s = []
    id = 0
    for i in range(0, len(tem_arr)):#遍历句子的每一个词
        term = tem_arr[i]
        if term != "###":#如果不等于### 直接追加
            s.append(term)
        else: #如果是占位符   则把生成的组合 依次填到###中
            s.append(iter[id])
            id += 1
    print(' '.join(s))
    return  ' '.join(s)#返回一个字符串 用空格分离


#将原来句子中的a或an替换成占位符
def generate_new_sentence(tem_arr):
    s = []
    tem_arr = tem_arr.split()
    for i in range(0, len(tem_arr)):#遍历句子的每一个词
        term = tem_arr[i]
        if (term != "a" and term != "an"):#如果不等于a或者an 直接追加
            s.append(term)
        else: #如果是a或an 则替换为###
            s.append("###")
    return  ' '.join(s)#返回一个字符串 用空格分离

#定义输入和输出文件路径
input_file = "/root/kenlm/build/test.txt"
output_file = "/root/kenlm/build/output.txt"

#判断句子中是否存在一个a或an，如果有就将对应的a替换成an
#分别对含有a和an的句子进行打分，用语言模型判别每个句子的得分
#如果替换后的得分更加高了，说明原来句子里的a/an 使用错误

def spelling_correction(input_file, output_file):
    changed_line_num = 0
    for line in read_words_list(input_file):
        print(line)
        if "a" in line or "an" in line:
            #获取句子中含有的a/an 单独子串的数量
            count = Counter(nltk.word_tokenize(line))["a"] + Counter(nltk.word_tokenize(line))["an"]
            #将句子中相应位置的子串都变为占位符###
            line_new = generate_new_sentence(line)
            #得到新生成后的替换后的句子列表
            candidates = generate_candidate_list(line_new, count)
            #判断得分最高的句子是否为原句子
            line_best = line #存储得分最高的句子 初始化为原句子
            changed = 0 #相比较使用句子字符串比对或者重新比较原句子和最高分句子的得分 使用标志位更方便
            for s in candidates:#遍历基于所有组合 替换后得到的句子
                if model.score(s) > model.score(line_best):
                    line_best = s
                    changed += 1
            if changed != 0:#打印替换信息
                changed_line_num += 1
                str_output = str(changed_line_num) + ":\n" + line + "\n>>\n" + line_best + "\n"
                print(str_output)
                save_file(output_file, str_output)
    print("完成所有内容校对和纠正！")


spelling_correction(input_file, output_file)