import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlsplit, parse_qsl, urlencode
import config

DOWNLOADED_FILENAME='quantking.xlsx'

def download_quantking():
    if os.path.exists(DOWNLOADED_FILENAME):
        os.remove(DOWNLOADED_FILENAME)

    base_url = "http://www.quantking.co.kr"
    url = base_url+"/lib/login_process.php"
    login_info = {
        "Login": "Login",
        "prev_url": "/page/main.php",
        "U_ID1": config.id, # id
        "U_ID2": config.mail,
        "U_Pass": config.pw # password
    }

    def download(url, file_name):
        with open(file_name, "wb") as file:
            response = requests.get(url)
            file.write(response.content)

    with requests.Session() as s:
        req = s.post(url, data=login_info)
        print(req.status_code)

        메뉴_유료용 = base_url+"/page/charge.php?boardid=JS_board_charge&mode=list"
        r = s.get(메뉴_유료용)
        print(r.status_code)

        soup = BeautifulSoup(r.text, 'lxml')
        links = soup.find_all("a")
        for a in links:
            href = a.attrs['href']
            text = a.text
            if text != None and '퀀트데이터' in text:
                print(f"{text} ==> {href}")
                break
        # href = "/page/charge.php?boardid=JS_board_charge&mode=view&no=1079&start=0&search_str=&val=""
        # http://www.quantking.co.kr/page/charge.php?boardid=JS_board_charge&mode=view&no=1079&start=0&search_str=&val=

        download_link_url = base_url+href
        r = s.get(download_link_url, headers=dict(referer = "http://www.quantking.co.kr/page/charge.php?boardid=JS_board_charge&mode=list"))
        print(r.status_code)
        # print(r.text)
        soup = BeautifulSoup(r.text, 'lxml')
        file_name=soup.find('input', {'name':'file_name'}).get('value')
        real_name = soup.find('input', {'name':'real_name'}).get('value')
        print(f"file_name:{file_name}")
        print(f"real_name:{real_name}")
        p = dict(parse_qsl(urlsplit(href).query))
        params=dict()
        params['LinkPage'] = 'board'
        params['boardid'] = 'JS_board_charge'
        params['mode'] = 'view'
        params['no'] = p['no']
        params['start'] = '0'
        params['val'] = ''
        params['sort'] = ''
        params['file_name'] = file_name
        params['real_name'] = real_name
        params['mode_X'] = 'download'
        params['fd'] = '..'
        print("+++++++++++++++++++++++++++++++++")
        download_url = base_url+"/page/charge.php?"+urlencode(params)
        print(download_url)
        download(download_url, DOWNLOADED_FILENAME)
        print("+++++++++++++++++++++++++++++++++")
        return real_name

if __name__ == '__main__':
    '''
    <div class="line"><label for="">첨부파일</label>\n\t\t\t
    <form name=\'down1\' action=\'/page/charge.php\' method=\'get\'>\n\t\t\t
    <input type=\'hidden\' name=\'LinkPage\' value=\'board\' />\n\t\t\t
    <input type=\'hidden\' name=\'boardid\' value=\'JS_board_charge\' />\n\t\t\t
    <input type=\'hidden\' name=\'mode\' value=\'view\' />\n\t\t\t
    <input type=\'hidden\' name=\'no\' value=\'1079\' />\n\t\t\t
    <input type=\'hidden\' name=\'start\' value=\'0\' />\n\t\t\t
    <input type=\'hidden\' name=\'val\' value=\'\' />\n\t\t\t
    <input type=\'hidden\' name=\'sort\' value=\'\' />\n\t\t\t
    <input type=\'hidden\' name=\'file_name\' value=\'1653487890_1.xlsx\' />\n\t\t\t
    <input type=\'hidden\' name=\'real_name\' value=\'퀀트데이터2022.05.25(22년1Q실적발표반영).xlsx\' />\n\t\t\t
    <input type=\'hidden\' name=\'mode_X\' value=\'download\' />\n\t\t\t
    <input type=\'hidden\' name=\'fd\' value=\'..\' />\t\t\t\t\t\t\t\t\t\t\t\n\t\t\t
    <a href="#self" onclick="document.down1.submit();">퀀트데이터2022.05.25(22년1Q실적발표반영).xlsx</a>
    </span>\n\t\t\t</form>\n\t\t\t</div>\n\t\t\t\t\t\t<div class="btbox">\t\t\t\t\n\t\t\t\t
    <div class="f_left btgray mgmg">
    <a href="/page/charge.php?LinkPage=board&boardid=JS_board_charge&mode=list&start=0&search_str=&val=&sort=">목록</a></div>\n\t\t\t
    </div>\n\t\t</div>
    '''
    '''
    Request URL: http://www.quantking.co.kr/page/charge.php?LinkPage=board&boardid=JS_board_charge&mode=view&no=1079&start=0&val=&
    sort=&file_name=1653487890_1.xlsx&real_name=%ED%80%80%ED%8A%B8%EB%8D%B0%EC%9D%B4%ED%84%B02022.05.25%2822%EB%85%841Q%EC%8B%A4%EC%A0%81%EB%B0%9C%ED%91%9C%EB%B0%98%EC%98%81%29.xlsx&mode_X=download&fd=..

    LinkPage: board
    boardid: JS_board_charge
    mode: view
    no: 1079
    start: 0
    val:
    sort:
    file_name: 1653487890_1.xlsx
    real_name: 퀀트데이터2022.05.25(22년1Q실적발표반영).xlsx
    mode_X: download
    fd: ..
    '''

# %%
