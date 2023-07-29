import undetected_chromedriver as uc  # undetected_chromedriver нужен, чтобы пройти cloudflare
from selenium.webdriver.common.by import By
import time
import requests
import os
from tqdm import tqdm  # класс tqdm используем для отслеживания прогресса скачивания фильма


headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}


class Downloader:
    def __init__(self, name,  main_url, quality):
        self.name = name
        self.main_url = main_url
        self.quality = quality
        self.segment_urls = None

    def prepare_for_downloading(self):  # функция получает список с ссылками на куски видео
        print('Идёт подготовка к скачиванию фильма...')
        if not os.path.isdir('movies'):
            os.mkdir('movies')
        options_chrome = uc.ChromeOptions()
        options_chrome.add_argument('--headless')
        with uc.Chrome(options=options_chrome) as browser:
            browser.get(self.main_url)
            browser.implicitly_wait(5)
            url = browser.find_element(By.XPATH, '//div[@class="tabs-b video-box visible"]//iframe').get_attribute('src')
            browser.get(url)
            time.sleep(3)
            all_requests = browser.execute_script("return window.performance.getEntries();")
            for request in all_requests:
                if 'index.m3u8' in request['name']:
                    url_1 = request['name'].replace('index', f'hls/{self.quality}')
                    break
        self.segment_urls = self.get_segment_urls(url_1)

    @staticmethod
    def get_segment_urls(url):
        resp = requests.get(url, headers=headers)
        lst_urls = list(filter(lambda el: 'https' in el, resp.text.split('\n')))
        return lst_urls

    def download_movie(self):  # проходимся по списку с ссылками, скачиваем и сохраняем
        print('Начинаем скачивание...')
        for i, url in tqdm(enumerate(self.segment_urls), total=len(self.segment_urls)):
            try:
                response = requests.get(url, headers=headers)
            except:
                time.sleep(5)
                response = requests.get(url, headers=headers)
            with open(fr'movies\{self.name}{i}.avi', 'wb') as f:
                f.write(response.content)
        self.concat_segments()
        print('Скачивание завершено!')

    def concat_segments(self):  # соединяем куски видео в один фильм
        print('Идёт подготовка видео..')
        main_segment = fr'movies\{self.name}.avi'
        os.rename(fr'movies\{self.name}0.avi', main_segment)
        for i in range(1, len(self.segment_urls)):
            with open(fr'movies\{self.name}{i}.avi', 'rb') as f:
                segment = f.read()
            with open(main_segment, 'ab') as f:
                f.write(segment)
        self.delete_segments()

    def delete_segments(self):
        for i in range(1, len(self.segment_urls)):
            os.remove(fr'movies\{self.name}{i}.avi')


movie_name = input('Введите название фильма: ')
movie_url = input('Введите ссылку на фильм: ')
quality = input('Для выбора качества введите число из списка 360, 480, 720, 1080: ')
dl = Downloader(movie_name, movie_url, quality)
dl.prepare_for_downloading()
dl.download_movie()