import re
import requests
from bs4 import BeautifulSoup
import nltk
from nltk import word_tokenize, pos_tag
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
import numpy

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')


def create_doc_image(all_terms, text):
    image = []
    for term in all_terms:
        if term in text:
            image.append(1)
        else:
            image.append(0)
    return image


def index_documents(url_array):
    all_terms = []
    texts_array = []
    for url in url_array:
        html_text = requests.get(url).text
        soup = BeautifulSoup(html_text, 'lxml')
        texts = soup.find_all('p')
        result_text = ''
        for text in texts:
            result_text += text.text
        words = word_tokenize(result_text)
        lemmatizer = WordNetLemmatizer()
        text_array = []
        # отбор существительных и прилагатель
        for word in words:
            if word.isalpha():  # слово состоит только из букв

                lemma = lemmatizer.lemmatize(word).lower()
                if ('NN' in pos_tag([lemma])[0][1] or 'JJ' in pos_tag([lemma])[0][
                    1]):
                    text_array.append(lemma)
                    if lemma not in all_terms:
                        all_terms.append(lemma)
        texts_array.append(text_array)
    doc_images = []
    for text in texts_array:
        doc_images.append(create_doc_image(all_terms, text))
    return all_terms, doc_images


def question_image_w(quest, all_t):
    q = quest[0]
    lemmatizer = WordNetLemmatizer()
    qq = []
    lemma = lemmatizer.lemmatize(q).lower()
    qq.append(lemma)
    for w in get_synonyms(lemma):
        qq.append(w)
        print(w)
    q_image = create_doc_image(all_t, qq)
    return q_image

def question_image(quest, all_t):
    q = quest[0]
    lemmatizer = WordNetLemmatizer()
    qq = []
    lemma = lemmatizer.lemmatize(q).lower()
    qq.append(lemma)
    q_image = create_doc_image(all_t, qq)
    return q_image


def multi_matrix(doc_im, q_im):
    multi = numpy.matmul(doc_im, numpy.transpose(q_im))
    # max = multi.max()
    rez = []
    for i in range(len(multi)):
        max = multi.max()
        for m in range(len(multi)):
            if multi[m] == max and max != 0:
                rez.append(m)
                multi[m] = 0
    return rez


def rez_texts(multi_rez, url_array):
    url_rezult = []
    for m in multi_rez:
        url_rezult.append(url_array[m])
    return url_rezult


def get_synonyms(word):
    synonyms = []

    # Получаем синонимы из WordNet для каждой части речи
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            if '_' not in lemma.name() and '-' not in lemma.name() and word != lemma.name():
                synonyms.append(lemma.name())
    tmp = list(set(synonyms))
    return tmp if len(tmp) < 4 else tmp[:4]  # Преобразуем в множество, чтобы убрать дубликаты


def calculate_or(first, second):
    for num in second:
        if num not in first:
            first.append(num)
    return first


def calculate_and(first, second):
    result = []
    for num in first:
        if num in second:
            result.append(num)
    return result


def calculate_not(body, doc_image):
    result = []
    for i in range(0, len(doc_image)):
        if i not in body:
            result.append(i)
    return result


def parse_search_formula(formula, all_terms, doc_image):
    formula = formula.replace(' ', '')
    if formula[0] == '(' and formula[-1] == ')':
        formula = formula[1:-1]
        count = 0
        for i in range(0, len(formula)):
            if formula[i] == '(':
                count += 1
            elif formula[i] == ')':
                count -= 1
            if count == 0:
                if formula[i] == '/':
                    right = parse_search_formula(formula[0:i], all_terms, doc_image)
                    left = parse_search_formula(formula[i + 1:len(formula)], all_terms, doc_image)
                    return calculate_or(right, left)
                elif formula[i] == '!':
                    body = parse_search_formula(formula[i + 1:len(formula)], all_terms, doc_image)
                    return calculate_not(body, doc_image)
                elif formula[i] == '+':
                    right = parse_search_formula(formula[0:i], all_terms, doc_image)
                    left = parse_search_formula(formula[i + 1:len(formula)], all_terms, doc_image)
                    return calculate_and(right, left)

    else:
        return multi_matrix(doc_image, question_image(re.findall(r"'([A-Za-z]+)'", formula), all_terms))

def parse_search_formula_syn(formula, all_terms, doc_image):
    formula = formula.replace(' ', '')
    if formula[0] == '(' and formula[-1] == ')':
        formula = formula[1:-1]
        count = 0
        for i in range(0, len(formula)):
            if formula[i] == '(':
                count += 1
            elif formula[i] == ')':
                count -= 1
            if count == 0:
                if formula[i] == '/':
                    right = parse_search_formula_syn(formula[0:i], all_terms, doc_image)
                    left = parse_search_formula_syn(formula[i + 1:len(formula)], all_terms, doc_image)
                    return calculate_or(right, left)
                elif formula[i] == '!':
                    body = parse_search_formula_syn(formula[i + 1:len(formula)], all_terms, doc_image)
                    return calculate_not(body, doc_image)
                elif formula[i] == '+':
                    right = parse_search_formula_syn(formula[0:i], all_terms, doc_image)
                    left = parse_search_formula_syn(formula[i + 1:len(formula)], all_terms, doc_image)
                    return calculate_and(right, left)

    else:
        return multi_matrix(doc_image, question_image_w(re.findall(r"'([A-Za-z]+)'", formula), all_terms))


def get_metrix(metric_list):
    recall_list = []
    precision_list = []
    accuracy_list = []
    error_list = []
    fmeasure_list = []
    for i in metric_list:
        f_rel = i[1]#a
        f_nrel = i[0] - i[1]#b
        nf_rel = 0#c
       # nf_nrel = len(url_array) - i[0]#d
        nf_nrel = 5 - i[0]
        r = f_rel/(f_rel+nf_rel)
        recall_list.append(r)
        p = f_rel/(f_rel +f_nrel )
        precision_list.append(p)
        accuracy_list.append((f_rel+nf_nrel)/(f_rel+f_nrel+nf_rel+nf_nrel))
        error_list.append((f_nrel+nf_rel)/(f_rel+f_nrel+nf_rel+nf_nrel))
        if r == 0 or p == 0:
            f = 0
        elif r == p:
            f = r
        else:
            f = 2/((r+p)/(r*p))
        fmeasure_list.append(f)
    return recall_list, precision_list, accuracy_list, error_list, fmeasure_list


def get_avg_metrix(m_list):
    sum = 0
    for m in m_list:
        sum += m
    avg = sum/len(m_list)
    return avg
#recall_list, precision_list, accuracy_list, error_list, fmeasure_list = get_metrix(metric_list)

#print(recall_list, precision_list, accuracy_list, error_list, fmeasure_list)
#print(get_avg_metrix(precision_list))

#n_rel = 4
#list_rel = [1,2,4,15]
#rez_url = [1,2,3,3,4,5,6,7,8,98,9,34,3,3,3,3,17,18,19,20]
def get_grafic(rez_url,list_rel,n_rel):
    xy_list = []
    count = numpy.zeros(len(rez_url))
    for i in list_rel:
        count[i-1] = 1
    print(count)
    rel = 0
    for i in range(len(count)):
        rel += count[i]
        r = rel / (rel +n_rel -rel)
        p = rel / (rel + (i + 1 -rel))
        xy_list.append([r,p])
    return xy_list

#all_terms, doc_image = index_documents(
 #   ['https://www.english-online.at/news-articles/environment/coca-cola-to-recycle-all-packaging-by-2030.htm',
 #    'https://www.english-online.at/news-articles/world/africa/how-coca-cola-saves-lives-in-africa.htm',
 #    'https://www.english-online.at/economy/world-hunger/hunger-global-food-crisis.htm'])
#request = "('plastic' / (!'bottle'))"
#print(parse_search_formula(request, all_terms, doc_image))
