from pypinyin import pinyin
from pypinyin import lazy_pinyin, Style
import jieba
import itertools
import kenlm
model = kenlm.LanguageModel("/root/kenlm/build/ngram.bin")
sentence1 = "徐凤年成为天下地衣"
sentence2 = "徐凤年 成为 天下 第一"
print(model.score(sentence1))
print(model.score(sentence2))
print(lazy_pinyin('西环', style=Style.NORMAL))
print(lazy_pinyin('西环', style=Style.TONE3))