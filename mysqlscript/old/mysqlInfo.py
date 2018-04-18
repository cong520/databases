#!/usr/bin/env python
# -*- coding: utf-8 -*-
#@Time     : 2018-04-09 15:41:33
#@Author   : chengengcong
#@File     : mysqlInfo
#@Library  : pymysql
#@Parameter: {'user':}
import argparse
import json
import platform
import pymysql
import sys
class MysqlConnect(object):
    def __init__(self,host,port,user,passwd):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        try:
            self.conn = pymysql.connect(host=self.host,port=int(self.port), user=self.user, passwd=self.passwd,charset='utf8')
        except:
            print('mysql cannot connect！')
            sys.exit(2)
    def connectdb(self):
        cursor = self.conn.cursor()
        return cursor

    def closeconnect(self):
        self.conn.close()

    def show_databases(self,cursor):
        '''获取所有数据库名称'''
        cursor.execute("show databases")
        databases = []
        for i in cursor.fetchall():
            databases.append(i[0])
        return databases

    def databses_sizes(self,cursor):
        '''获取数据库大小'''
        cursor.execute("use information_schema")
        cursor.execute(
            "select concat(round(sum(DATA_LENGTH/1024/1024),2),'MB') as data from TABLES"
        )
        result = cursor.fetchone()
        return result[0]


    def databses_character(self,cursor):
        '''获取数据库字符集'''
        cursor.execute("SHOW VARIABLES like 'character_set_database'")
        result = cursor.fetchone()
        return result[1]

def os_type():
    '''获取操作系统类型'''
    return platform.system()



if __name__ == "__main__":
    # parser=argparse.ArgumentParser()
    # parser.add_argument('--verbose',type=int,default=1,help='verbose for output')
    # parser.add_argument('--user',default='root',help='user name for connect to mysql, default root')
    # parser.add_argument('--pw',default='',help='user password for connect to mysql, default None')
    # parser.add_argument('--host',default='127.0.0.1',help='mysql host ip, default 127.0.0.1')
    # parser.add_argument('--port',default=3306,type=int,help='mysql port, default 3306')
    # args=parser.parse_args()
    result = {}
    # mysql_info=get_mysql_info(args)

    # result['osType'] = os_type()
    # result['mysql_info'] = mysql_info
    # print(json.dumps(result,ensure_ascii=False))
    theMysql = MysqlConnect('127.0.0.1','3306','root','16899199')
    conn = theMysql.connectdb()
    result['show_databses'] =  theMysql.show_databases(conn)
    print(result)
    # print(sys.argv[1])
