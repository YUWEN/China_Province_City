"""
    MZB
    sql语句：
        建表
        create table version (id int primary key auto_increment, url varchar(200) not null,check_time datetime default now());
        create table province (id int primary key auto_increment,code varchar(20) not null,title varchar(32) not null);
        create table city (id int primary key auto_increment,code varchar(20) not null,title varchar(32) not null,pro_code varchar(20));
        create table county (id int primary key auto_increment,code varchar(20) not null,title varchar(32) not null,ci_code varchar(20),pro_code varchar(20));

        连表查询
        select county.title,city.title,province.title from county inner join city on city.code=county.ci_code inner join province on province.code=city.pro_code;
"""

from selenium import webdriver
import json
import time
from threading import Thread
import pymysql


class MZBSpider(object):
    def __init__(self):
        self.__url = "http://www.mca.gov.cn/article/sj/xzqh/"
        self.__browser = webdriver.Chrome(executable_path="/Users/nelson/Downloads/chromedriver")
        self.db = pymysql.connect(
            host="localhost",
            port=3306,
            user="root",
            passwd="19930623..",
            charset="utf8",
            database="mzb_data"
        )
        self.cursor = self.db.cursor()
        self.__province = []
        self.__city = []
        self.__county = []

    def check_page(self):
        # pass
        self.__browser.get(url=self.__url)
        time.sleep(1)
        self.__browser.find_element_by_partial_link_text("县以上行政区划代码").click()
        time.sleep(3)
        handles = self.__browser.window_handles
        self.__browser.switch_to.window(handles[1])
        # 检查当前页面url是否存在于version表中
        url = self.__browser.current_url
        sql_line = 'select url from version where url="%s"' % url
        self.cursor.execute(sql_line)
        if self.cursor.fetchone():  # 判断如果url存在
            print('当前数据已是最新数据，无需更新...')
            sql_line = 'update version set check_time=now() where url="%s"' % url
            self.cursor.execute(sql_line)
            self.db.commit()
            return
        else:
            print('当前url未存在，将抓取最新数据并更新数据库内容...')
            sql_line = 'insert into version (url) values ("%s")' % url
            self.cursor.execute(sql_line)
            self.db.commit()
            # 以下是xpath匹配所有行政区划代码节点并返回节点列表
            info_lists = self.__browser.find_elements_by_xpath('//tbody/tr[@height="19"]')
            return info_lists

    def get_data(self):
        # self.__browser.get(url=self.__url)
        # time.sleep(1)
        # self.__browser.find_element_by_partial_link_text("县以上行政区划代码").click()
        # time.sleep(3)
        # handles = self.__browser.window_handles
        # self.__browser.switch_to.window(handles[1])
        # info_lists = self.__browser.find_elements_by_xpath('//tbody/tr[@height="19"]')
        info_lists = self.check_page()
        if info_lists is None:
            return
        else:
            for info in info_lists:
                # print(info.text.split(' '))
                code = info.text.split(' ')[0]
                title = info.text.split(' ')[-1]
                if code[2:] == "0000":
                    print("直辖市&省：", code, title)
                    self.__province.append([code, title])
                    if title in ['上海市', "天津市", "北京市", "重庆市"]:
                        pro_code = code[:2] + '0000'
                        print("市：", code, title, pro_code)
                        self.__city.append([code, title, pro_code])
                elif code[4:] == "00" and code[2:4] != "00":
                    pro_code = code[:2] + '0000'
                    print("市：", code, title, pro_code)
                    self.__city.append([code, title, pro_code])
                else:
                    ci_code = code[:4] + "00"
                    pro_code = code[:2] + '0000'
                    for ci in self.__city:
                        if ci_code in ci:
                            break
                    else:
                        ci_code = pro_code
                        ci_title = ''
                        for pro in self.__province:
                            if ci_code == pro[0]:
                                ci_title = pro[1]
                                break
                        if [ci_code, ci_title, pro_code] not in self.__city:
                            print("市：", ci_code, ci_title, pro_code)
                            self.__city.append([ci_code, ci_title, pro_code])
                    self.__county.append([code, title, ci_code, pro_code])
                    print('县&区：', code, title, ci_code, pro_code)
        return self.__province, self.__city, self.__county

    def save_to_mysql(self):
        data = self.get_data()
        self.__browser.quit()
        if data is None:
            return
        # 有最新抓取数据时候需要清空当前数据表内容
        else:
            # print(data[0])
            # print(data[1])
            # print(data[2])
            for table in ['province', 'city', 'county']:
                sql_line = 'delete from %s' % table
                self.cursor.execute(sql_line)
                self.db.commit()
            # 清空表之后保存最新行政区代码到对应表中
            # for province in data[0]:
            #     code = province[0]
            #     title = province[1]
            #     sql_line = 'insert into province (code,title) values ("%s","%s")' % (code, title)
            #     self.cursor.execute(sql_line)
            sql_line_pro = 'insert into province (code,title) values (%s,%s)'
            sql_line_ci = 'insert into city (code,title,pro_code) values (%s,%s,%s)'
            sql_line_co = 'insert into county (code,title,ci_code,pro_code) values (%s,%s,%s,%s)'
            # 省表中插入插入最新数据
            self.cursor.executemany(sql_line_pro, data[0])
            self.cursor.executemany(sql_line_ci, data[1])
            self.cursor.executemany(sql_line_co, data[2])
            # for city in data[1]:
            #     code = city[0]
            #     title = city[1]
            #     pro_code = city[2]  # pre_code表示市对应的省或者直辖市code
            #     sql_line = 'insert into city (code,title,pro_code) values ("%s","%s","%s")' % (code, title, pro_code)
            #     self.cursor.execute(sql_line)
            # self.db.commit()
            # for county in data[2]:
            #     code = county[0]
            #     title = county[1]
            #     ci_code = county[2]  # ci_code表示市对应的市区code
            #     pro_code = county[3]  # pro_code表示市对应的省或者直辖市code
            #     sql_line = 'insert into county (code,title,ci_code,pro_code) values ("%s","%s","%s","%s")' % (
            #         code, title, ci_code, pro_code)
            #     self.cursor.execute(sql_line)
            self.db.commit()
            self.cursor.close()
            # self.db.close()
            print('最新数据抓取并保存完成...')
        self.__browser.quit()

    def main(self):
        self.save_to_mysql()


if __name__ == "__main__":
    spider = MZBSpider()
    # spider.get_data()
    # spider.get_province(spider.get_page())
    spider.main()
