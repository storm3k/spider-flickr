# coding:utf-8
import os
import flickrapi
from pprint import pprint
import time
import random
from tasks import dl_images

# 以 20 天为一个周期
OFFSET = 20
# 一个月的时间
ONE_DAY = OFFSET * 24 * 3600


# 现在的时间，Unix timestamp
T = int(time.time())


class FlickrDownloader(object):

    def __init__(self, tag, max_images=100):
        # 下载的标签
        self.tag = tag
        # 最大下载量
        self.max_images = 4000

        # 实例化API
        self.flickr = self.__gen_flickr()

        # 下载原图
        self.dl_size = 'url_o'
        # 页数记录
        self.page = 1
        self.per_page = 100

        # log
        self.id_log = './flickr/3.0/' + self.tag + '.txt'
        # pic_log
        self.pic_log = './flickr/3.0/pic/' + self.tag + '.txt'
        self.pic_43_log = './flickr/3.0/pic/' + self.tag + '_43' + '.txt'

        # 日期限制
        self.min_upload_date = T - ONE_DAY
        self.max_upload_date = T
        # print(self.min_upload_date, self.max_upload_date)

    @classmethod
    def __gen_flickr(cls):
        """实例化 flickr """

        def get_key():
            API_KEY, API_SECRET = random.choice(
                [
                    ("xx", "xx"),
                ]
            )
            return API_KEY, API_SECRET

        API_KEY, API_SECRET = get_key()
        # print(API_KEY)
        return flickrapi.FlickrAPI(
            API_KEY,
            API_SECRET,
            # 解析为 json
            format='parsed-json',
            # cache=True
        )

    def get_search_lst(self):
        try:
            photos_search = self.flickr.photos.search(
                    tags=self.tag,
                    per_page=str(self.per_page),
                    extras=self.dl_size,
                    page=self.page,
                    min_upload_date=self.min_upload_date,
                    max_upload_date=self.max_upload_date
                )

            # sleep
            # s = random.randint(1, 2)
            # time.sleep(s)

            status = photos_search['stat']
        except Exception as e:
            # print(e)
            return
        # 判断状态
        if status == 'ok':
            total_page = int(photos_search['photos']['pages'])
            if self.page >= total_page:
                return
            # 页面 +1
            self.page += 1
            print(self.page)
            # 返回图片列表
            # {'farm': 8,
            #    'id': '46376164884',
            #    'isfamily': 0,
            #    'isfriend': 0,
            #    'ispublic': 1,
            #    'owner': '47474132@N05',
            #    'secret': '176d79867c',
            #    'server': '7800',
            #    'title': 'A definition of photography'}
            return photos_search['photos']['photo']

    def filter_exif(self, pic_id):
        try:
            exif = self.flickr.photos.getExif(photo_id=pic_id)
        # 可能 flickrapi.exceptions.FlickrError: Error: 2: Permission denied
        except Exception:
            return False
        # 'photo': {'camera': 'Nikon D7200',
        #           'exif':[]
        exif = exif['photo']['exif']
        label_lst = [x['label'] for x in exif]
        if "Focal Length" in label_lst:
            return True
        return False

    def filter_sizes(self, pic_id, flag):
        try:
            pic_info = self.flickr.photos.getSizes(photo_id=pic_id)
        except Exception as e:
            # print(e)
            return False
        # 最后一个是原图或者最大图片的尺寸
        # 原图 Original
        pic_size_info = pic_info['sizes']['size'][-1]
        # 获取图片尺寸
        pic_h = pic_size_info['height']
        pic_w = pic_size_info.get('width')
        if not pic_w:
            pic_w = pic_h

        # 比例 h / w
        ratio = {0.65, 0.66, 0.67}
        h_w_ratio = int(pic_h) / int(pic_w)
        h_w_ratio = round(h_w_ratio, 2)

        if h_w_ratio in ratio:
            url = pic_size_info['source']
            self.__mk_pic_log(url)

            if flag:
                self.dl_url(url)
            return True

        # 0.75
        if h_w_ratio == 0.75:
            url = pic_size_info['source']
            self.__mk_pic_43_log(url)
        return False

    def run(self):
        while self.per_page * self.page < self.max_images:
            pic_lst = self.get_search_lst()
            if not pic_lst:
                break

            # 获取 id 列表
            pic_id = [x['id'] for x in pic_lst]
            # # 根据 exif 过滤
            # pic_id = filter(self.filter_exif, pic_id)
            # # 根据 size 过滤
            # pic_id = filter(self.filter_sizes, pic_id)
            # print(list(pic_id))

            # 记录 ID
            list(map(self.__mk_log, pic_id))

    def dl_url(self, url):
        save_path = '/mnt/data2/flickr/'
        save_path = os.path.join(save_path, self.tag)
        # 判断是否为原图
        if url[-5] == 'o':
            dl_images.delay(url, save_path)

    def __mk_log(self, s):
        # log
        line = s + '\n'
        self.log = open(self.id_log, 'a', encoding='utf-8')
        self.log.write(line)
        self.log.close()
        # print("写入成功")

    def __mk_pic_log(self, s):
        # log
        line = s + '\n'
        self.log = open(self.pic_log, 'a', encoding='utf-8')
        self.log.write(line)
        self.log.close()

    def __mk_pic_43_log(self, s):
        # log
        line = s + '\n'
        self.log = open(self.pic_43_log, 'a', encoding='utf-8')
        self.log.write(line)
        self.log.close()

    def run_filter(self, flag=False):
        """过滤所有ID, flag 下载标志"""
        path = self.id_log
        with open(path, 'r') as f:
            for n, line in enumerate(f.readlines()):
                if not n % 10000:
                    now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                    print(now, n)
                line = line.strip()
                if self.filter_exif(line):
                    self.filter_sizes(line, flag)


def dl_id():
    kw = [
        # ('street', 5),
        # ('office', 5),
        # ('hall', 5),
        ('yard', 5),
        ('road', 5),
        ('playground', 5),
        ('apartment', 5),
        ('restaurant', 5),
    ]

    for tag, n in kw:
        # 循环天数 flickr 2004年创建，因此不会超过15年
        i = 1
        while True:
            print("正在下载 %s %3d" % (tag, i))

            fd = FlickrDownloader(tag)
            fd.run()

            # 控制时间
            global T
            global ONE_DAY
            # 5天
            T -= ONE_DAY

            if T <= 1115042514:
                break

            i += 1

        # 恢复 time
        T = int(time.time())


def filter_id():
    kw = [
        ('street', 5),
        ('office', 5),
        ('hall', 5),
        ('yard', 5),
        # ('road', 5),
        ('playground', 5),
        ('apartment', 5),
        ('restaurant', 5),
    ]
    for tag, n in kw:
        print(tag)
        fd = FlickrDownloader(tag)
        fd.run_filter()


def cnt():
    """统计当前文件夹下 o 即原图的个数"""
    def cnt_o(path):
        n_o = 0
        n_line = 0
        with open(path, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if line[-5] == 'o':
                    n_o += 1
                n_line += 1
        print("%5d %5d -- %.2f" % (n_o, n_line, round(n_o / n_line, 2)))

    import os
    txt_file = [x for x in os.listdir('./') if os.path.isfile(x) and os.path.splitext(x)[1] == '.txt']
    for txt in txt_file:
        print("%20s" % txt, end='')
        cnt_o(txt)


def dl_from_tag(kw):
    """注意需要先创建好目录，为了少判断，这里没写"""
    fd = FlickrDownloader(kw)
    fd.run_filter(flag=True)


if __name__ == '__main__':
    # 下载 ID
    # dl_id()

    # 下载 url
    # filter_id()

    # 下载图片
    base_path = '/mnt/data2/flickr'
    kws = [
#        'yard',
#        'playground',
#        'restaurant',
#        'apartment',
        'hall',
        'office'
    ]

    for kw in kws:
        path = os.path.join(base_path, kw)
        if not os.path.exists(path):
            os.mkdir(path)
        dl_from_tag(kw)

