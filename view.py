from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.label import Label
from kivymd.uix.button import MDIconButton
from kivy.config import Config
from kivy.factory import Factory
from lib import *
import webbrowser
import json

Config.set("graphics", "resizable", "0")
Config.set("graphics", "width", "1000")
Config.set("graphics", "height", "700")

Window.clearcolor = (.80, .242, .126, 1)

class App(MDApp):

    def __init__(self):
        super().__init__()
        self.all_terms = []
        self.doc_images = []
        self.url_array = []
        self.number_record = 0
        self.number_page = 1
        self.current_page = 1
        self.number_record_per_page = 10
        self.curr_answer = []
        self.statistic = []
        self.key_word = []
        self.active = True

    def build(self):
        self.download_data()
        print(self.url_array)
        root = Builder.load_file('app_view.kv')
        return root

    def on_stop(self):
        self.save_data()

    def download_data(self):
        try:
            with open('data.json', 'r') as file:
                data = json.load(file)
                self.all_terms = data[0]
                self.doc_images = data[1]
                self.url_array = data[2]
                self.statistic = data[3]
        except :
            pass

    def save_data(self):
        with open('data.json', 'w') as file:
            json.dump([self.all_terms, self.doc_images, self.url_array, self.statistic], file)

    def to_first_page(self, current_page):
        path = self.root.ids.search_screen.ids.res
        path.clear_widgets()
        self.current_page = 1
        current_page.text = str(self.current_page)
        self.show_data()

    def to_last_page(self, current_page):
        path = self.root.ids.search_screen.ids.res
        path.clear_widgets()
        self.current_page = len(self.curr_answer) // self.number_record_per_page + 1
        current_page.text = str(self.current_page)
        self.show_data()

    def to_x_page(self, current_page, sign):
        path = self.root.ids.search_screen.ids.res
        path.clear_widgets()
        if sign == '+':
            if (len(self.curr_answer) // self.number_record_per_page) >= self.current_page:
                self.current_page += 1
                current_page.text = str(self.current_page)
        elif sign == '-':
            if self.current_page - 1 > 0:
                self.current_page -= 1
                current_page.text = str(self.current_page)
        self.show_data()

    def download_sources(self, edit_form):
        self.url_array += edit_form.text.replace(" ", "").split(",")
        self.url_array = list(set(self.url_array))
        print(self.url_array)
        self.all_terms, self.doc_images = index_documents(self.url_array)

    def show_data(self):

        x = self.root.ids.search_screen.ids.res
        self.number_record = len(self.curr_answer)
        self.root.ids.search_screen.ids.number_record.text = "Кол-во записей: " + str(self.number_record)

        n = (self.current_page - 1) * self.number_record_per_page

        if self.number_record == 0:
            x.add_widget(Label(text='Ничего не найдено', color=(0, .26, .41, 1), halign='center', valign='center',
                               text_size=(150, 700 / self.number_record_per_page)))


        for j in range(self.number_record_per_page):

            if len(self.curr_answer) <= j:
                for k in range(1):
                    x.add_widget(Label(text='', color=(0, .26, .41, 1), halign='center', valign='center',
                                       text_size=(150, 700 / self.number_record_per_page)))
                    x.add_widget(Label(text='', color=(0, .26, .41, 1), halign='center', valign='center',
                                       text_size=(150, 700 / self.number_record_per_page)))
                    x.add_widget(Label(text='', color=(0, .26, .41, 1), halign='center', valign='center',
                                       text_size=(150, 700 / self.number_record_per_page)))
            elif n + j >= len(self.curr_answer):
                for k in range(1):
                    x.add_widget(Label(text='', color=(1, .26, .41, 1), halign='center', valign='center',
                                       text_size=(150, 700 / self.number_record_per_page)))
                    x.add_widget(Label(text='', color=(0, .26, .41, 1), halign='center', valign='center',
                                       text_size=(150, 700 / self.number_record_per_page)))
                    x.add_widget(Label(text='', color=(0, .26, .41, 1), halign='center', valign='center',
                                       text_size=(150, 700 / self.number_record_per_page)))

            else:
                x.add_widget(
                    Label(text=str(self.curr_answer[j + n]), color=(0, .26, .41, 1), halign='center', valign='center',
                          text_size=(400, 700 / self.number_record_per_page)))
                x.add_widget(MDIconButton(id=f'{self.curr_answer[j + n]}', icon="lightbulb-outline", on_press=self.link,
                                             icon_color=(.14, .26, 1, 1), halign='center',
                                             valign='center', size_hint=(1, 1), ))
                x.add_widget(
                    Label(text=str(self.key_word[j + n]), color=(0, .26, .41, 1), halign='center', valign='center',
                          text_size=(250, 700 / self.number_record_per_page)))


        self.root.ids.search_screen.ids.last_page.text = str(
            len(self.curr_answer) // self.number_record_per_page + 1)

    def search(self, q):
        path = self.root.ids.search_screen.ids.res
        path.clear_widgets()
        tmp = []
        if(self.active):
            tmp = parse_search_formula_syn(q.text, self.all_terms, self.doc_images)
        else:
            tmp = parse_search_formula(q.text, self.all_terms, self.doc_images)
        self.key_word = self.get_words_in_doc(q.text, tmp)
        self.curr_answer = [self.url_array[i] for i in tmp]

        self.show_data()


    def get_words_in_doc(self, req, docs):
        result = [""]*len(docs)
        words = re.findall(r"'([A-Za-z]+)'", req)
        for i in range(len(docs)):
            for w in words:
                lemmatizer = WordNetLemmatizer()
                lemma = lemmatizer.lemmatize(w).lower()
                im_req = create_doc_image(self.all_terms, [lemma])
                if numpy.matmul(self.doc_images[docs[i]], numpy.transpose(im_req)) != 0:
                    result[i]+=" "+w
        return result

    def change_active(self):
        self.active = False if self.active == True else True
        print(self.active)


    def link(self, path):
        webbrowser.open(path.id)

    def save_statistic(self,kol_rel):
        self.statistic.append([self.number_record, int(kol_rel.text)])
        print(self.statistic)

    def clear_search_screen(self):
        self.number_record = 0
        self.number_page = 1
        self.current_page = 1
        self.curr_answer = []
        path = self.root.ids.search_screen.ids.res
        path.clear_widgets()
        self.root.ids.search_screen.ids.question.text = ""
        self.root.ids.search_screen.ids.kol_rel.text = ""
        self.key_word = []
        self.show_data()

    def count_statistica(self):
        recall_list, precision_list, accuracy_list, error_list, fmeasure_list = get_metrix(self.statistic)
        recall = get_avg_metrix(recall_list)
        precision = get_avg_metrix(precision_list)
        accuracy = get_avg_metrix(accuracy_list)
        error = get_avg_metrix(error_list)
        fmeasure = get_avg_metrix(fmeasure_list)
        self.root.ids.statistic_screen.ids.recall.text = f"Recall: {recall}"
        self.root.ids.statistic_screen.ids.precision.text = f"Precision: {precision}"
        self.root.ids.statistic_screen.ids.accuracy.text = f"Accuracy: {accuracy}"
        self.root.ids.statistic_screen.ids.error.text = f"Error: {error}"
        self.root.ids.statistic_screen.ids.fmeasure.text = f"Fmeasure: {fmeasure}"


    class MenuScreen(Screen):
        pass

    class StatisticScreen(Screen):
        pass

    class SearchScreen(Screen):
        pass

    class HelpScreen(Screen):
        pass

    class WindowManager(ScreenManager):
        pass