<<<<<<< HEAD
# Spider----Hdoj-AC-Machine-AC爬虫

*  环境要求           
    安装python 3运行环境  
    安装requests包

*  使用指南  
    运行spider.py，按照提示输入Hdoj的账号密码，
    以及要从哪一题开始哪一题结束，之后就可以自动A题啦。

*  阅读代码指南  
    由于是信马由缰地写的，所以写的比较混乱，请多见谅。   
    
    HDUAccesser：负责登录OJ，交题，并得到交题之后的状态。  
    login函数实现了登录杭电oj的功能。  
    submit实现了对代码的提交。  
    getStatus实现了对最近一次提交的代码的提交状态的获取

    CodeGetter： 负责搜索题解，爬取代码。
    baidu函数负责获取题解博客的网址列表。  
    tryPromblem函数负责一一尝试baidu得到的网址，
    并调用get得到代码，
    并把代码传递给HDUAccesser对象，
    并根据提交的结果决定是否继续尝试提交代码。  
    CodeGetter留下了run函数作为接口，在循环内一直调用baidu和tryProblem函数，尝试解决多个问题。

*  如果你想写自己的“AC自动机”  
    大概步骤如下  

    登录OJ：需要抓取登录时提交的数据包，得到数据包格式，
    然后使用类似于requests这样的HTTP包提交post请求实现登录  

    搜索题解：使用搜索引擎搜索关键字，在这里通常是get请求  

    抓取搜索结果：使用正则表达式抓取搜索到的网页链接  

    抓取代码：正则表达式  

    提交代码：同样需要抓取提交代码的数据包，同样也是post请求  

    获取交题后状态：使用requests包获取status页面的html文本，
    使用正则表达式获取状态    


Just a Toy

