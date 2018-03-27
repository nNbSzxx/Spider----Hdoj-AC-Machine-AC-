import requests
import re
import time
import logging

hostUrl = "http://acm.hdu.edu.cn"
loginUrl = "http://acm.hdu.edu.cn/userloginex.php?action=login"
testUrl = "http://acm.hdu.edu.cn/viewcode.php?rid=20086246"
submitUrl = "http://acm.hdu.edu.cn/submit.php?action=submit"
statusUrl = "http://acm.hdu.edu.cn/status.php"
# 要设置 request header 否则baidu爬不下来
headers = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}
# problem id = 1000, code :
code1000 = '' \
           '#include <cstdio>\n' \
           '#include <cstdlib>\n' \
           '#include <malloc.h>\n' \
           '\n' \
           'int main() {\n'  \
           '    int a, b;\n' \
           '    while(~scanf("%d%d", &a, &b)) {\n' \
           '        printf("%d\\n", a + b);\n' \
           '    }\n' \
           '    return 0;\n' \
           '}\n'

'''
submit request data form:
    check : 0
    problemid : 1000
    language : (0 for G++, 5 for JAVA)
    usercode : ...
'''

# 使用日志，定义日志全局变量
logger = None



#登录hdoj，提交代码，获得提交状态
class HDUAccesser(object):
    global logger
    # 常量定义
    __WAITING_STATE = {'Queuing', 'Waiting', 'Pending', 'Running', 'Compiling'}
    __WA_STATE = {'Runtime Error<br>(ACCESS_VIOLATION)',
                     'Runtime Error<br>(INTEGER_DIVIDE_BY_ZERO)',
                     'Compilation Error',
                     'Time Limit Exceeded',
                     'Memory Limit Exceeded',
                     'Output Limit Exceeded',
                     'Presentation Error'
                     }
    __ACCEPTED_STATE = {'Accepted'}
    # Status for login
    __BAD_LOGIN = 0
    __GOOD_LOGIN = 1
    # Status for submit
    __BAD_SUBMIT = 0
    __GOOD_SUBMIT = 1
    # Status for status
    __GET_STATUS_ERROR = 0
    __ACCEPTED_STATUS = 1
    __NOT_ACCEPTED_STATUS = 2
    __UNKNOWN_STATUS = 3

    # Status for solve
    NETWORK_ERROR = 0
    SUCCEED_SOLVED = 1
    UNSUCCEED_SOLVED = 2

    def __init__(self, username, password, headers = None, hostUrl = None, loginUrl = None, testUrl = None, submitUrl = None, statusUrl = None):
        self.__session = requests.session()
        self.__session.headers = headers
        # requests使用了urllib3库，默认的http connection是keep-alive的，requests设置False关闭，防止 max retries exceed
        self.__session.keep_alive = False
        self.__hostUrl = hostUrl
        self.__postUrl = loginUrl
        self.__testUrl = testUrl
        self.__submitUrl = submitUrl
        self.__statusUrl = statusUrl
        self.__cookies = dict()
        self.__language = 0
        self.__username = self.__password = None
        '''
        HDUAccess所用正则，可以合成一个正则表达式
            self.__regex1 = re.compile(r'<tr[\s]*?align=center[\s]*?><td[\s]*?height=22px[\s]*?>(.*?)(?=</tr>)')
            self.__regex1 = \
                    re.compile\
                        (r'(?:<tr[\s]*?[bgcolor=#D7EBFF]*?[\s]*?align=center[\s]*?><td[\s]*?height=22px[\s]*?>)'
                         r'([\s\S]*?)'
                         r'(?=</tr>)')
            self.__regex2 = re.compile(r'<font[\s]*?color=.*?>(.*?)(?=</font>)')
        '''
        self.__regex = \
            re.compile\
                ('(?:<tr[\s]*?[bgcolor=#D7EBFF]*?[\s]*?align=center[\s]*?><td[\s]*?height=22px[\s]*?>)(?:[\s\S]*?)(?:<font[\s]*?color=.*?>)(.*?)(?=</font>)')
        self.__username = username
        self.__password = password
        self.__hasLogged = False
        if self.__login()==self.__BAD_LOGIN:
            logger.warn('请检查用户名密码是否正确，网络是否连接')
            exit(-1)
        else:
            self.__hasLogged = True

    def __login(self):
        logger.info('正在登录...')
        values = {"username" : self.__username, "userpass": self.__password, "login" : "Sign In"}
        r = self.__session.post(loginUrl, values, cookies = self.__cookies)
        if (self.__session.post(self.__testUrl, cookies = self.__cookies).text.__contains__("Sign Out")):
            logger.info("登录成功")
            return self.__GOOD_LOGIN
        else:
            logger.warn("登录失败，请重试")
            return self.__BAD_LOGIN

    def __submit(self, id, code, langid):
        logger.info('正在提交...')
        data = {"check" : "1", "problemid" : str(id), "language" : str(langid), "usercode" : code}
        response = self.__session.post(self.__submitUrl, data, cookies = self.__cookies, )
        if (response.url == "http://acm.hdu.edu.cn/status.php") & (response.status_code == 200):
            logger.info(str(id) + "提交成功")
            return self.__GOOD_SUBMIT
        else:
            logger.info(str(id) + "提交失败")
            return self.__BAD_SUBMIT

    def __getStatus(self):
        logger.info('等待结果...')
        # data = {"first" : None, "pid" : None, "user" : self.__username, "lang" : "0", "status" : "0"}
        url = self.__statusUrl
        if self.__username != None:
            url = url + "?first=&pid=" + "&user="+ self.__username + "&lang=0&status="
        cnt = 0
        success = False
        status = None
        while True:
            time.sleep(1)
            response = self.__session.post(url, cookies=self.__cookies)
            html = response.text
            # print(response.url)
            status = re.findall(self.__regex, html)
            '''
            # print(m)
            # for i in m:
            #     print(i)
            # l = m[0]
            # print(l)
            # m = re.findall(self.__regex2, l)
            # print(m.__len__())
            # for i in m:
            #     print(i)
            # m = m[0]
            # print(m)
            m = m[0]
           '''
            cnt = cnt + 1
            # 防止因正则匹配失败返回空列表而导致的下标越界
            if (status == None) | (status.__len__() == 0):
                continue
            status = status[0]
            # print(str(cnt) + ":" + status)
            if status not in self.__WAITING_STATE:
                success = True
                break
            if cnt > 100:
                break
        if success:
            logger.info("成功提交 " + status)
            logger.info('休息一下， 半分钟后回来~')
            time.sleep(30)
            if status in self.__ACCEPTED_STATE:
                return self.__ACCEPTED_STATUS
            elif status in self.__WA_STATE:
                return self.__NOT_ACCEPTED_STATUS
            else:
                return self.__UNKNOWN_STATUS
        else:
            logger.warn("提交失败")
            return self.__GET_STATUS_ERROR

    def solve(self, id, code, lang):
        if lang == 'cpp':
            langid = 0
        elif lang == 'java':
            langid = 5
        elif lang == 'html':
            langid = 0
        else:
            return self.UNSUCCEED_SOLVED

        if self.__submit(id, code, langid) == self.__GOOD_SUBMIT:
            status = self.__getStatus()
            if status == self.__ACCEPTED_STATUS:
                return self.SUCCEED_SOLVED
            elif status == self.__GET_STATUS_ERROR:
                return self.NETWORK_ERROR
            else:
                return self.UNSUCCEED_SOLVED
        else:
            return self.NETWORK_ERROR





class CodeGetter:
    #(?<=\btpl="se_com_default"[\s]{0, 200}data-click="{'rsv_bdr':'0'[\s]{0, 200}}"[\s]{0, 200}>h3[\s]{0, 200}class="t">)href[\s]*?=[\s]*?"([\S]+)"(?=\btarget="_blank")
    '''
    self.__regex = re.compile(r'(?<=' + r'tpl="se_com_default"[\s]{0, 200}' + r'data-click="{' +
                                   r"'rsv_bdr':'0'\s" + r'}"[\s]{2}>' +
                                   # r'[\s\S]{0, 200}' +
                                   # r'}"[\s]{0, 200}' +
                                   r'<h3\sclass="t">)' + #look behind
                                   r'[\s\S]*?'
                                   + r'href[\s]*?=[\s]*?'        #find url
                                   r'"([\S]*?)"'                  #get url
                                   r'(?=target="_blank")'     #look forward
                                   )
    '''
    global logger
    def __init__(self, header, accesser):
        self.__homeUrl = 'https://www.baidu.com/s?wd=site%3Ablog.csdn.net%20hdoj%20'
        self.__headers = headers
        self.__s = requests.session()
        self.__s.headers = self.__headers
        # requests使用了urllib3库，默认的http connection是keep-alive的，requests设置False关闭，防止 max retries exceed
        self.__s.keep_alive = False
        #s = 'tpl="se_com_default"  data-click="{\'rsv_bdr\':\'0\' }"  ><h3 class="t">'
        # regex used for baidu
        self.__regex1 = re.compile(r'(?<=' + r'tpl="se_com_default")' + #look behind
                                   r'[\s\S]*?'+
                                   r'(?=target="_blank")' #look forward
                                   )
        self.__regex1 = re.compile(r'(?<=tpl="se_com_default")[\s\S]*?(?=target="_blank")')
        self.__regex2 = re.compile(r'href[\s]*?=[\s]*?"([\S]*?)"')
        # regex used for csdn, two possible patterns
        self.__regex3 = re.compile(r'<?(?:pre)?[\s]*?name="code"[\s]*?class="(\w+)">([\s\S]*?)(?=</pre>)')
        self.__regex4 = re.compile(r'<?(?:pre)?[\s]*?class="(\w+)"[\s]*?name="code">([\s\S]*?)(?=</pre>)')
        self.__regex6 = re.compile(r'(?:pre)[\s]*?class="(\w+)"[\s]*?>([\s\S]*?)(?=</pre>)')
        # get the title
        self.__regex5 = re.compile(r'<title>[\s\S]*?</title>')
        # regex for remove html labels in code
        self.__regex7 = re.compile(r'<span[\s\S]*?>')
        self.__regex8 = re.compile(r'</[\s\S]*?>')

        self.__accesser = accesser

    # testurl : http://blog.csdn.net/love_acm_love_mm/article/details/8827555
    def get(self, html, id):
        print(html)
        tups = re.findall(self.__regex3, html)
        if (tups.__len__() == 0):
            #logger.debug('aaa')
            tups = re.findall(self.__regex4, html)
        if (tups.__len__() == 0):
            #logger.debug('bbb')
            tups = re.findall(self.__regex6, html)
        if (tups.__len__() == 0):
            #logger.debug('ccc')
            pass
        # 常常有一些人在前面会先贴出错误的做法，然后最后再贴正解
        # 使用迭代器访问，避免了下标越界问题
        for tup in reversed(tups):
            # print(tup)
            code = tup[1]
            lang = -1
            # 有些题解可能会把思路和感慨写在代码框里面，也可能会有一些奇怪的东西混在前面
            if code.__contains__('#include'):
                lang = 'cpp'
                l = code.split('#include', 1)
                code = '#include' + l[1]
                # 加入万能头文件，防止因缺少头文件而导致的CE
                # 同时防止因包含万能头文件而导致的命名冲突
                if not (
                            code.__contains__('map') |
                            code.__contains__('hash') |
                            code.__contains__('set') |
                            code.__contains__('queue') |
                            code.__contains__('list') |
                            code.__contains__('rank') |
                            code.__contains__('vector') |
                            code.__contains__('priority_queue')
                        ):
                    code = '#include <bits/stdc++.h>\n' + code
                # 包含了以上名称的变量，所以不能引入万能头文件，否则会引起命名冲突
                elif not (code.__contains__('cstring')):
                    code = '#include <cstring>\n' + code
                # 防止因next变量名与标准库变量名冲突导致的CE
                code = code.replace('next', 'nt')
            elif code.__contains__('import'):
                lang = 'java'
                l = code.split('import', 1)
                code = 'import' + l[1]
            if lang != -1:
                # 处理html转义字符
                code = code.replace('&nbsp;', ' ')
                code = code.replace('&quot;', '"')
                code = code.replace('&amp;', '&')
                code = code.replace('&lt;', '<')
                code = code.replace('&gt;', '>')
                code = code.replace('&#39;', "'")
                code = code.replace('&#43;', '+')
                # 处理html标签
                code = self.__regex7.sub('', code)
                code = self.__regex8.sub('', code)
                logger.info('得到代码：')
                logger.debug(code)
                return (lang, code)
        return ('', '')

    # 返回百度后的网址列表
    def baidu(self, id):
        url = self.__homeUrl + str(id)

        '''
       尝试使用如下方法解决被远程主机拒绝访问的问题：
           1. sleep 企图通过减少访问频率而使得不被服务器拒绝访问
           2. 试图断开会话，再重新连接 
           3. 如果上述方法不能解决问题，let it crash
       '''
        html = ""
        cnt = 0
        sleepTime = 0
        while html == "":
            cnt = cnt + 1
            try:
                response = self.__s.get(url)
                html = response.text
                logger.info('搜索链接：')
                logger.info(response.url)
            except Exception as e:
                if cnt < 10:
                    sleepTime = sleepTime + 60
                    logger.exception('异常！异常！尝试使用sleep(%d)解决', sleepTime)
                    time.sleep(sleepTime)
                elif cnt < 15:
                    logger.exception('异常！异常！sleep（）失败！尝试断开会话重新连接, 并sleep(%d)', sleepTime)
                    self.__s.close()
                    time.sleep(sleepTime)
                    self.__s = requests.session()
                    self.__s.headers = self.__headers
                else:
                    logger.exception('我被异常打败了！')
                    self.__s.close()
                    raise
        m = re.findall(self.__regex1, html)
        s = ''
        # 迭代器访问避免下标越界
        for i in m:
            # print(i)
            s += i
        m = re.findall(self.__regex2, s)
        # print(m.__len__())
        logger.info('百度到如下csdn题解网址：')
        logger.info(m)
        # for i in m:
        #     print(i)
        return m

    # 顺次打开百度得到的网址，并将其中得到的代码提交
    def tryPromblem(self, l, id):
        # 判断baidu返回的结果是否合法
        if (l == None) | (l == []):
            cnt = 0
            while cnt < 10:
                cnt = cnt + 1
                l = self.baidu(id)
                if (l != None) & (l != []):
                    break
            if (l == None) | (l == []):
                logger.warn('百度搜索该题没有任何结果！请检查输入是否正确，网络是否正常')
                return
        solved = False
        # 从baidu返回结果中逐个打开，爬取代码
        for url in l:
            logger.info('正在下面网址中搜索代码...')
            logger.info(url)
            response = self.__s.get(url)
            # 防止正则匹配失败而导致的下标越界
            titles = re.findall(self.__regex5, response.text)
            if (titles == None) | (titles.__len__() == 0):
                logger.info("没有找到标题！")
                continue
            if (not titles[0].__contains__(str(id))):
                logger.info('标题中不含该题题号！')
                continue
            lang, code = self.get(response.text, id)
            state = self.__accesser.solve(id, code, lang)
            # 处理返回结果，AC直接跳出，WA进入下一个页面继续搜索代码，网络问题再次尝试
            if state == self.__accesser.SUCCEED_SOLVED:
                solved = True
                break
            elif state == self.__accesser.UNSUCCEED_SOLVED:
                pass
            elif state == self.__accesser.NETWORK_ERROR:
                cnt = 0
                state2 = None
                while cnt < 10:
                    cnt = cnt + 1
                    state2 = self.__accesser.solve(id, code, lang)
                    if state2 != self.__accesser.NETWORK_ERROR:
                        break
                if state2 == self.__accesser.SUCCEED_SOLVED:
                    solved = True
                    break
                elif state2 == self.__accesser.UNSUCCEED_SOLVED:
                    pass
                else:
                    logger.warn('无法提交！请检查输入是否正确，网络是否正常')

    def run(self, start, end):
        i = start
        while i <= end:
            logger.info('正在尝试' + str(i) + '...')
            l = self.baidu(i)
            self.tryPromblem(l, i)
            i = i + 1

def initLogger(filename):
    global logger
    # 设置向控制台打印的日志，打印所有等级的log
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S %p'
                        )
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                  datefmt = '%Y-%m-%d %H:%M:%S %p')

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    # 设置向文件打印的日志，打印info级别及以上的log
    fileHandler = logging.FileHandler(filename)
    fileHandler.setLevel(logging.INFO)
    fileHandler.setFormatter(formatter)
    # 添加handler
    logger.addHandler(fileHandler)

def main():
    print("Please input your hdoj username:")
    username = input()
    print("Please input your password:")
    password = input()
    print("Please input from which problem you want to start: (id)")
    begin = int(input())
    print("Please input to which problem you want to end: (id)")
    end = int(input())
    global logger
    filename = 'spider.log'
    initLogger(filename)
    logger.info('本次运行的log被记录在' + filename)
    logger.debug('debug 日志运行良好')
    logger.info('正在启动...')

    # 避免 max retries exceed，设置最高尝试次数
    requests.adapters.DEFAULT_RETRIES = 5

    hdu = HDUAccesser(username, password, headers, hostUrl, loginUrl, testUrl, submitUrl, statusUrl)
    baiduHeaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Referer' : 'https://www.baidu.com/',
        'is_referer': 'https://www.baidu.com/'
    }
    codeGetter = CodeGetter(headers, hdu)
    #begin = 1000
    #end = 1000
    logger.info('本次从%d题开始，到%d题结束', begin, end)
    codeGetter.run(begin, end)
    logger.info('运行结束.')
if __name__ == '__main__':
    main()


