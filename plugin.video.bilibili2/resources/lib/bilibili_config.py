#coding=utf-8

APPKEY = '19bf1f1192873efa'
APPSECRET = '87677fc06b0afc08cb86e008183390e5'

API_URL = 'http://api.bilibili.com'
HOME_URL = 'http://www.bilibili.com'
VIEW_URL = API_URL + '/view?{}'
LIST_URL = API_URL + '/list?{}'
DYNAMIC_URL = API_URL + '/x/feed/pull?type=0&ps={}&pn={}'
SP_URL = API_URL + '/sp'
LOGIN_URL = 'https://passport.bilibili.com/web/login'
LOGIN_CAPTCHA_URL = 'https://passport.bilibili.com/captcha?r={}'
LOGIN_HASH_URL = 'https://passport.bilibili.com/login?act=getkey&r={}'
HISTORY_URL = API_URL + '/x/v2/history?pn={}&ps={}'
FAV_BOX_URL = 'http://space.bilibili.com/ajax/fav/getBoxList?mid={}'
FAV_URL = 'http://space.bilibili.com/ajax/fav/getList?mid={}&page={}&pagesize={}&fid={}'
TIMELINE_URL = 'http://bangumi.bilibili.com/jsonp/timeline_v2.ver?callback=timeline'
MY_INFO_URL = 'http://space.bilibili.com/ajax/member/MyInfo'
AV_URL = 'http://www.bilibili.com/widget/getPageList?aid={}'
BANGUMI_CHASE_URL = 'http://space.bilibili.com/ajax/Bangumi/getList?mid={}&page={}&pagesize={}'
BANGUMI_SEASON_URL = 'http://bangumi.bilibili.com/jsonp/seasoninfo/{}.ver'
ADD_HISTORY_URL = 'http://interface.bilibili.com/player?id=cid:{}&aid={}'
ATTENTION_URL = 'http://space.bilibili.com/ajax/friend/GetAttentionList?mid={}&page={}&pagesize={}'
ATTENTION_VIDEO_URL = 'https://space.bilibili.com/ajax/member/getSubmitVideos?mid={}&page={}&pagesize={}&tid={}'
ATTENTION_CHANNEL_URL = 'https://space.bilibili.com/ajax/channel/getChannel?mid={}'
ATTENTION_CHANNEL_LIST_URL = 'https://space.bilibili.com/ajax/channel/getVideo?mid={}&cid={}&p={}&num={}'

INTERFACE_URL = r'http://interface.bilibili.com/playurl?cid={}&from=miniplay&player=1&sign={}'
INTERFACE_PARAMS = r'cid={}&from=miniplay&player=1{}'
SECRETKEY_MINILOADER = r'1c15888dc316e05a15fdd0a02ed6584f'


LOGIN_ERROR_MAP = {
    -105: "验证码错误",
    -618: "昵称重复或含有非法字符",
    -619: "昵称不能小于3个字符或者大于30个字符",
    -620: "该昵称已被使用",
    -622: "Email已存在",
    -625: "密码错误次数过多",
    -626: "用户不存在",
    -627: "密码错误",
    -628: "密码不能小于6个字符或大于16个字符",
    -645: "昵称或密码过短",
    -646: "请输入正确的手机号",
    -647: "该手机已绑定另外一个账号",
    -648: "验证码发送失败",
    -652: "历史遗留问题，昵称与手机号重复，请联系管理员",
    -662: "加密后的密码已过期",
}

ORDER = [
    {
        'title': u'日排行榜',
        'value': 'hot',
        'days': 1,
    },
    {
        'title': u'三日排行榜',
        'value': 'hot',
        'days': 3,
    },
    {
        'title': u'周排行榜',
        'value': 'hot',
        'days': 7,
    },
    {
        'title': u'最新动态',
        'value': 'new',
        'days': 30,
    },
    {
        'title': u'最新投稿',
        'value': 'default',
        'days': 30,
    },
#    {
#        'title': u'按评论数从高至低排序',
#        'value': 'review'
#    },
#    {
#        'title': u'按弹幕数从高至低排序',
#        'value': 'damku'
#    },
#    {
#        'title': u'按推荐数从高至低排序',
#        'value': 'comment'
#    },
#    {
#        'title': u'按宣传数排序（硬币）',
#        'value': 'default'
#    },
]


CATEGORY = {
    "146": {
        "url": "http://www.bilibili.com/video/movie_japan_1.html", 
        "subs": [], 
        "title": "日本电影"
    }, 
    "153": {
        "url": "http://www.bilibili.com/video/bangumi_chinese_1.html ", 
        "subs": [], 
        "title": "国产动画"
    }, 
    "152": {
        "url": "http://www.bilibili.com/video/bagumi_offical_1.html", 
        "subs": [], 
        "title": "官方延伸"
    }, 
    "155": {
        "url": "http://www.bilibili.com/video/fashion.html", 
        "subs": [
            "157", 
            "158", 
            "164", 
            "159"
        ], 
        "title": "时尚"
    }, 
    "154": {
        "url": "http://www.bilibili.com/video/three-dimension-dance-1.html", 
        "subs": [], 
        "title": "三次元舞蹈"
    }, 
    "157": {
        "url": "http://www.bilibili.com/video/fashion-makeup-fitness-1.html", 
        "subs": [], 
        "title": "美妆"
    }, 
    "156": {
        "url": "http://www.bilibili.com/video/dance-demo-1.html", 
        "subs": [], 
        "title": "舞蹈教程"
    }, 
    "159": {
        "url": "http://www.bilibili.com/video/fashion-info-1.html", 
        "subs": [], 
        "title": "资讯"
    }, 
    "37": {
        "url": "http://www.bilibili.com/video/tech-popular-science-1.html", 
        "subs": [], 
        "title": "纪录片"
    }, 
    "164": {
        "url": "http://www.bilibili.com/video/fashion-body-1.html", 
        "subs": [], 
        "title": "健身"
    }, 
    "131": {
        "url": "http://www.bilibili.com/video/ent-korea-1.html", 
        "subs": [], 
        "title": "Korea相关"
    }, 
    "130": {
        "url": "http://www.bilibili.com/video/music-collection-1.html", 
        "subs": [], 
        "title": "音乐选集"
    }, 
    "137": {
        "url": "http://www.bilibili.com/video/ent-circle-1.html", 
        "subs": [], 
        "title": "明星"
    }, 
    "65": {
        "url": "http://www.bilibili.com/video/game-ctary-network-1.html", 
        "subs": [], 
        "title": "网游·电竞"
    }, 
    "129": {
        "url": "http://www.bilibili.com/video/dance.html", 
        "subs": [
            "20", 
            "154", 
            "156"
        ], 
        "title": "舞蹈"
    }, 
    "82": {
        "url": "http://www.bilibili.com/video/movie-presentation-1.html", 
        "subs": [], 
        "title": "电影相关"
    }, 
    "83": {
        "url": "http://www.bilibili.com/video/movie-movie-1.html", 
        "subs": [], 
        "title": "其他国家"
    }, 
    "138": {
        "url": "http://www.bilibili.com/video/ent_funny_1.html", 
        "subs": [], 
        "title": "搞笑"
    }, 
    "119": {
        "url": "http://www.bilibili.com/video/kichiku.html", 
        "subs": [
            "22", 
            "26", 
            "126", 
            "127"
        ], 
        "title": "鬼畜"
    }, 
    "170": {
        "url": "http://www.bilibili.com/video/guochuang-offical-1.html", 
        "subs": [], 
        "title": "资讯"
    }, 
    "24": {
        "url": "http://www.bilibili.com/video/douga-mad-1.html", 
        "subs": [], 
        "title": "MAD·AMV"
    }, 
    "25": {
        "url": "http://www.bilibili.com/video/douga-mmd-1.html", 
        "subs": [], 
        "title": "MMD·3D"
    }, 
    "76": {
        "url": "http://www.bilibili.com/video/ent-food-1.html", 
        "subs": [], 
        "title": "美食圈"
    }, 
    "27": {
        "url": "http://www.bilibili.com/video/douga-else-1.html", 
        "subs": [], 
        "title": "综合"
    }, 
    "20": {
        "url": "http://www.bilibili.com/video/dance-1.html", 
        "subs": [], 
        "title": "宅舞"
    }, 
    "21": {
        "url": "http://www.bilibili.com/video/ent-life-1.html", 
        "subs": [], 
        "title": "日常"
    }, 
    "22": {
        "url": "http://www.bilibili.com/video/ent-Kichiku-1.html", 
        "subs": [], 
        "title": "鬼畜调教"
    }, 
    "23": {
        "url": "http://bangumi.bilibili.com/movie/", 
        "subs": [
            "82", 
            "85", 
            "145", 
            "146", 
            "147", 
            "83"
        ], 
        "title": "电影"
    }, 
    "47": {
        "url": "http://www.bilibili.com/video/douga-voice-1.html", 
        "subs": [], 
        "title": "短片·手书·配音"
    }, 
    "28": {
        "url": "http://www.bilibili.com/video/music-original-1.html", 
        "subs": [], 
        "title": "原创音乐"
    }, 
    "29": {
        "url": "http://www.bilibili.com/video/music-coordinate-1.html", 
        "subs": [], 
        "title": "三次元音乐"
    }, 
    "1": {
        "url": "http://www.bilibili.com/video/douga.html", 
        "subs": [
            "24", 
            "25", 
            "47", 
            "27"
        ], 
        "title": "动画"
    }, 
    "0": {
        "url": "http://www.bilibili.com", 
        "subs": [
            "1", 
            "13", 
            "167", 
            "3", 
            "129", 
            "4", 
            "36", 
            "160", 
            "119", 
            "155", 
            "165", 
            "5", 
            "23", 
            "11"
        ], 
        "title": "全部"
    }, 
    "3": {
        "url": "http://www.bilibili.com/video/music.html", 
        "subs": [
            "28", 
            "31", 
            "30", 
            "59", 
            "29", 
            "54", 
            "130"
        ], 
        "title": "音乐"
    }, 
    "5": {
        "url": "http://www.bilibili.com/video/ent.html", 
        "subs": [
            "71", 
            "137", 
            "131"
        ], 
        "title": "娱乐"
    }, 
    "4": {
        "url": "http://www.bilibili.com/video/game.html", 
        "subs": [
            "17", 
            "65", 
            "136", 
            "19", 
            "121"
        ], 
        "title": "游戏"
    }, 
    "158": {
        "url": "http://www.bilibili.com/video/fashion-clothing-1.html", 
        "subs": [], 
        "title": "服饰"
    }, 
    "71": {
        "url": "http://www.bilibili.com/video/ent-variety-1.html", 
        "subs": [], 
        "title": "综艺"
    }, 
    "163": {
        "url": "http://www.bilibili.com/video/ent-sports-1.html", 
        "subs": [], 
        "title": "运动"
    }, 
    "26": {
        "url": "http://www.bilibili.com/video/douga-kichiku-1.html", 
        "subs": [], 
        "title": "音MAD"
    }, 
    "75": {
        "url": "http://www.bilibili.com/video/ent-animal-1.html", 
        "subs": [], 
        "title": "动物圈"
    }, 
    "147": {
        "url": "http://www.bilibili.com/video/movie_chinese_1.html", 
        "subs": [], 
        "title": "国产电影"
    }, 
    "145": {
        "url": "http://www.bilibili.com/video/movie_west_1.html", 
        "subs": [], 
        "title": "欧美电影"
    }, 
    "128": {
        "url": "http://www.bilibili.com/video/tv-presentation-1.html", 
        "subs": [], 
        "title": "电视剧相关"
    }, 
    "39": {
        "url": "http://www.bilibili.com/video/speech-course-1.html", 
        "subs": [], 
        "title": "演讲•公开课"
    }, 
    "15": {
        "url": "http://www.bilibili.com/video/soap-three-1.html", 
        "subs": [], 
        "title": "连载剧集"
    }, 
    "121": {
        "url": "http://www.bilibili.com/video/gmv-1.html", 
        "subs": [], 
        "title": "GMV"
    }, 
    "122": {
        "url": "http://www.bilibili.com/video/tech-wild-1.html", 
        "subs": [], 
        "title": "野生技术协会"
    }, 
    "168": {
        "url": "http://www.bilibili.com/video/guochuang-fanvid-1.html ", 
        "subs": [], 
        "title": "国产原创相关"
    }, 
    "169": {
        "url": "http://www.bilibili.com/video/glove-puppetry-1.html ", 
        "subs": [], 
        "title": "布袋戏"
    }, 
    "126": {
        "url": "http://www.bilibili.com/video/kichiku-manual_vocaloid-1.html", 
        "subs": [], 
        "title": "人力VOCALOID"
    }, 
    "127": {
        "url": "http://www.bilibili.com/video/kichiku-course-1.html", 
        "subs": [], 
        "title": "教程演示"
    }, 
    "95": {
        "url": "http://www.bilibili.com/video/tech-future-digital-1.html", 
        "subs": [], 
        "title": "数码"
    }, 
    "165": {
        "url": "http://www.bilibili.com/video/ad-ad-1.html", 
        "subs": [], 
        "title": "广告"
    }, 
    "86": {
        "url": "http://www.bilibili.com/video/tv-sfx-1.html", 
        "subs": [], 
        "title": "特摄"
    }, 
    "167": {
        "url": "http://bangumi.bilibili.com/guochuang/", 
        "subs": [
            "153", 
            "168", 
            "169", 
            "170"
        ], 
        "title": "国创"
    }, 
    "160": {
        "url": "http://www.bilibili.com/video/life.html", 
        "subs": [
            "138", 
            "21", 
            "76", 
            "75", 
            "161", 
            "162", 
            "163"
        ], 
        "title": "生活"
    }, 
    "161": {
        "url": "http://www.bilibili.com/video/ent-handmake-1.html", 
        "subs": [], 
        "title": "手工"
    }, 
    "162": {
        "url": "http://www.bilibili.com/video/ent-painting-1.html", 
        "subs": [], 
        "title": "绘画"
    }, 
    "96": {
        "url": "http://www.bilibili.com/video/tech-future-military-1.html", 
        "subs": [], 
        "title": "星海"
    }, 
    "11": {
        "url": "http://bangumi.bilibili.com/tv/", 
        "subs": [
            "15", 
            "34", 
            "86", 
            "128"
        ], 
        "title": "电视剧"
    }, 
    "13": {
        "url": "http://bangumi.bilibili.com/22/", 
        "subs": [
            "33", 
            "32", 
            "51", 
            "152"
        ], 
        "title": "番剧"
    }, 
    "59": {
        "url": "http://www.bilibili.com/video/music-perform-1.html", 
        "subs": [], 
        "title": "演奏"
    }, 
    "17": {
        "url": "http://www.bilibili.com/video/game-video-1.html", 
        "subs": [], 
        "title": "单机联机"
    }, 
    "98": {
        "url": "http://www.bilibili.com/video/tech-future-other-1.html", 
        "subs": [], 
        "title": "机械"
    }, 
    "33": {
        "url": "http://www.bilibili.com/video/bangumi-two-1.html", 
        "subs": [], 
        "title": "连载动画"
    }, 
    "32": {
        "url": "http://www.bilibili.com/video/part-twoelement-1.html", 
        "subs": [], 
        "title": "完结动画"
    }, 
    "31": {
        "url": "http://www.bilibili.com/video/music-Cover-1.html", 
        "subs": [], 
        "title": "翻唱"
    }, 
    "30": {
        "url": "http://www.bilibili.com/video/music-vocaloid-1.html", 
        "subs": [], 
        "title": "VOCALOID·UTAU"
    }, 
    "51": {
        "url": "http://www.bilibili.com/video/douga-else-information-1.html", 
        "subs": [], 
        "title": "资讯"
    }, 
    "36": {
        "url": "http://www.bilibili.com/video/technology.html", 
        "subs": [
            "37", 
            "124", 
            "122", 
            "39", 
            "96", 
            "95", 
            "98"
        ], 
        "title": "科技"
    }, 
    "34": {
        "url": "http://www.bilibili.com/video/tv-drama-1.html", 
        "subs": [], 
        "title": "完结剧集"
    }, 
    "19": {
        "url": "http://www.bilibili.com/video/game-mugen-1.html", 
        "subs": [], 
        "title": "Mugen"
    }, 
    "54": {
        "url": "http://www.bilibili.com/video/music-oped-1.html", 
        "subs": [], 
        "title": "OP/ED/OST"
    }, 
    "124": {
        "url": "http://www.bilibili.com/video/tech-fun-1.html", 
        "subs": [], 
        "title": "趣味科普人文"
    }, 
    "85": {
        "url": "http://www.bilibili.com/video/tv-micromovie-1.html", 
        "subs": [], 
        "title": "短片"
    }, 
    "136": {
        "url": "http://www.bilibili.com/video/music-game-1.html", 
        "subs": [], 
        "title": "音游"
    }
}
