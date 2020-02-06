﻿
import sys
import os
import time
import json
import getpass
import codecs
import traceback
import math
from datetime import date, timedelta
# from time import gmtime, strftime

from PTTLibrary import PTT
import Util

search_list = [
    ('Gossiping', ['Bignana', 'xianyao'], 5),
    ('Wanted', ['LittleCalf', 'somisslove'], 3),
    ('give', ['gogin'], 3),
    ('HatePolitics', ['kero2377'], 5),
    ('Gamesale', ['mithralin'], 1),
]

ask = False
publish = False
mail = False
# False True

author_list = dict()
ip_list = dict()
publish_content = None
new_line = '\r\n'


def post_handler(post_info):
    if post_info is None:
        return
    global author_list
    global ip_list

    author = post_info.author
    if '(' in author:
        author = author[:author.find('(')].strip()

    # author is OK
    title = post_info.title
    delete_status = post_info.delete_status
    ip = post_info.ip

    if delete_status == PTT.data_type.PostDeleteStatus.AUTHOR:
        title = '(本文已被刪除) [' + author + ']'
    elif delete_status == PTT.data_type.PostDeleteStatus.MODERATOR:
        title = '(本文已被刪除) <' + author + '>'
    elif delete_status == PTT.data_type.PostDeleteStatus.UNKNOWN:
        # title = '(本文已被刪除) <' + author + '>'
        pass

    if title is None:
        title = ''
    # title is OK

    # print(f'==>{author}<==>{title}<')

    if author not in author_list:
        author_list[author] = []

    if ip is not None and ip not in ip_list:
        ip_list[ip] = []

    if delete_status == PTT.data_type.PostDeleteStatus.NOT_DELETED:
        if '[公告]' in title:
            return
        if ip is not None:
            ip_list[ip].append(author + '     □ ' + title)

    author_list[author].append(title)


def multi_po(board, moderators, max_post):

    global author_list
    global ip_list
    global new_line
    global ptt_bot
    global publish
    global ask
    global mail
    global dayAgo

    Util.ptt_bot = ptt_bot
    Util.post_search = f'({board})'
    Util.Moderators = moderators

    global publish_content
    if publish_content is None:

        publish_content = '此內容由抓超貼程式產生' + new_line
        publish_content += '由 CodingMan 透過 PTT Library 開發，' + new_line * 2

        publish_content += 'PTT Library: https://tinyurl.com/umqff3v' + new_line
        publish_content += '開發手冊: https://hackmd.io/@CodingMan/PTTLibraryManual' + new_line
        publish_content += '抓超貼程式: https://github.com/PttCodingMan/PTTBots' + new_line * 2

        publish_content += f'PTT Library 版本: {PTT.version.V}' + new_line

    start_time = time.time()
    author_list = dict()
    ip_list = dict()
    current_date = Util.get_date(dayAgo)

    ptt_bot.log(f'開始 {board} 板昨天的超貼偵測')
    ptt_bot.log('日期: ' + current_date)
    start, end = Util.find_post_range(dayAgo, show=False)
    ptt_bot.log('編號範圍 ' + str(start) + ' ~ ' + str(end))

    ErrorPostList, DeleteCount = ptt_bot.crawl_board(
        PTT.data_type.IndexType.BBS,
        post_handler,
        Util.current_board,
        start_index=start,
        end_index=end,
        search_type=Util.post_search_type,
        search_condition=Util.post_search,
        query=True,
    )

    end_time = time.time()

    multi_po_result = ''
    for Suspect, TitleAuthorList in author_list.items():

        if len(TitleAuthorList) <= max_post:
            continue
        # print('=' * 5 + ' ' + Suspect + ' ' + '=' * 5)

        if multi_po_result != '':
            multi_po_result += new_line
        for title in TitleAuthorList:
            if not title.startswith('R:'):
                multi_po_result += current_date + ' ' + \
                                 Suspect + ' □ ' + title + new_line
            else:
                multi_po_result += current_date + ' ' + \
                                 Suspect + ' ' + title + new_line

    ip_result = ''
    for IP, SuspectList in ip_list.items():
        # print('len:', len(SuspectList))
        if len(SuspectList) <= max_post:
            continue

        # print('IP:', IP)
        ip_result += 'IP: ' + IP + new_line

        for Line in SuspectList:
            # print('>   ' + current_date + ' ' + Line)
            ip_result += current_date + ' ' + Line + new_line

    title = current_date + f' {board} 板超貼結果'

    publish_content += new_line
    publish_content += f'◆ {board} 板超貼結果'

    time_temp = math.ceil(end_time - start_time)
    min_ = int(time_temp / 60)
    sec = int(time_temp % 60)

    content = '此內容由抓超貼程式產生' + new_line

    content += '共耗時'
    publish_content += '共耗時'
    if min_ > 0:
        content += f' {min_} 分'
        publish_content += f' {min_} 分'
    content += f' {sec} 秒執行完畢' + new_line * 2
    publish_content += f' {sec} 秒執行完畢' + new_line * 2

    content += '此程式是由 CodingMan 透過 PTT Library 開發，' + new_line * 2
    content += f'蒐集範圍為 ALLPOST 搜尋 ({board}) 情況下編號 ' + \
               str(start) + ' ~ ' + str(end) + new_line
    content += f'共 {end - start + 1} 篇文章' + new_line * 2

    publish_content += f'    蒐集範圍為 ALLPOST 搜尋 ({board}) 情況下編號 ' + \
                       str(start) + ' ~ ' + str(end) + new_line
    publish_content += f'    共 {end - start + 1} 篇文章' + new_line * 2

    if multi_po_result != '':
        content += multi_po_result

        multi_po_result = multi_po_result.strip()
        for line in multi_po_result.split(new_line):
            publish_content += '    ' + line + new_line
    else:
        content += '◆ 無人違反超貼板規' + new_line
        publish_content += '    ' + '◆ 無人違反超貼板規' + new_line

    if ip_result != '':
        content += ip_result
        ip_result = ip_result.strip()
        for line in ip_result.split(new_line):
            publish_content += '    ' + line + new_line
    else:
        content += new_line + f'◆ 沒有發現特定 IP 有 {max_post + 1} 篇以上文章' + new_line
        publish_content += new_line + \
            f'    ◆ 沒有發現特定 IP 有 {max_post + 1} 篇以上文章' + new_line

    content += new_line + '內容如有失準，歡迎告知。' + new_line
    content += '此訊息同步發送給 ' + ' '.join(Util.Moderators) + new_line
    content += new_line
    content += pttid

    print(title)
    print(content)

    # with open('Test.txt', 'w', encoding='utf8') as in_file:
    #     in_file.write(content)

    if ask:
        choise = input('要發佈嗎? [Y]').lower()
        publish = (choise == 'y') or (choise == '')

    if mail:
        for Moderator in Util.Moderators:
            ptt_bot.mail(Moderator, title, content, 0)
            ptt_bot.log('寄信給 ' + Moderator + ' 成功')
    else:
        ptt_bot.log('取消寄信')


if __name__ == '__main__':

    dayAgo = 1

    try:
        with open('Account.txt') as AccountFile:
            Account = json.load(AccountFile)
            pttid = Account['ID']
            password = Account['Password']
    except FileNotFoundError:
        pttid = input('請輸入帳號: ')
        password = getpass.getpass('請輸入密碼: ')

    ptt_bot = PTT.Library(
        # LogLevel=PTT.LogLevel.TRACE
    )
    ptt_bot.login(pttid, password)

    try:
        for (current_board, ModeratorList, MaxPost) in search_list:
            multi_po(current_board, ModeratorList, MaxPost)

        publish_content += new_line + '歡迎其他板主來信新增檢查清單' + new_line
        publish_content += '內容如有失準，歡迎告知。' + new_line
        publish_content += 'CodingMan'

        print(publish_content)

        if publish:
            CurrentDate = Util.get_date(dayAgo)

            ptt_bot.post('Test', CurrentDate + ' 超貼結果', publish_content, 1, 0)
            ptt_bot.log('在 Test 板發文成功')
        else:
            ptt_bot.log('取消備份')
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        print(e)
    except KeyboardInterrupt:
        pass

    ptt_bot.logout()
