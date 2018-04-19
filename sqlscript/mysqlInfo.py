#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding:utf-8
#@Time     : 2018-04-09 15:41:33
#@Author   : chengengcong
#@File     : mysqlInfo
#@Library  : pymysql
#@Parameter: "{'host':'127.0.0.1','port':3306,'user':'root','passwd':'123456','com_commit':'60','table_locks_waited':'5','slow_launch_threads':5}"
import argparse
import json
import platform
import pymysql
import sys
import time

class MysqlConnect(object):
    def __init__(self,host,port,user,passwd):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        try:
            self.conn = pymysql.connect(host=self.host,port=int(self.port), user=self.user, passwd=self.passwd,charset='utf8')
        except:
            print('mysql cannot connect!')
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
        '''获取数据库默认字符集'''
        cursor.execute("SHOW VARIABLES like 'character_set_database'")
        result = cursor.fetchone()
        return result[1]

    def show_status(self,cursor):
        '''获取数据库所有状态参数'''
        cursor.execute("SHOW STATUS")
        result = cursor.fetchall()
        allMysqlStatus = {}
        for i in result:
            allMysqlStatus[i[0]]=i[1]
        return allMysqlStatus

def threshold_judge(result):
    '''自动化阈值判断'''
    parameter=eval(sys.argv[1])
    for key in result:
        if key in parameter:
            if(str(result[key])>str(parameter[key])):
                result[key]="abnormal"
            else:
                result[key]="normal"
    return result

def os_type():
    '''获取操作系统类型'''
    return platform.system()

def threads_connected(allMysqlStatus):
    '''获取当前客户端已连接的数量'''
    return allMysqlStatus['Threads_connected']

def aborted_clients(allMysqlStatus):
    '''客户端被异常中断的数值'''
    return allMysqlStatus['Aborted_clients']

def questions(allMysqlStatus):
    '''每秒钟获得的查询数量'''
    return allMysqlStatus['Questions']

def opened_tables(allMysqlStatus):
    '''表缓存没有命中的数量'''
    return allMysqlStatus['Opened_tables']

def select_full_join(allMysqlStatus):
    '''没有主键（key）联合（Join）的执行。该值可能是零。'''
    return allMysqlStatus['Select_full_join']

def select_scan(allMysqlStatus):
    '''执行全表搜索查询的数量。'''
    return allMysqlStatus['Select_scan']

def slow_queries(allMysqlStatus):
    '''超过该值（--long-query-time）的查询数量，或没有使用索引查询数量。'''
    return allMysqlStatus['Slow_queries']

def slow_launch_threads(allMysqlStatus):
    '''查看创建时间超过slow_launch_time秒的线程数。'''
    return allMysqlStatus['Slow_launch_threads']

def com_commit(allMysqlStatus):
    '''每秒事务量。'''
    return allMysqlStatus['Com_commit']

def table_locks_waited(allMysqlStatus):
    '''查看不能立即获得的表的锁的次数。如果该值较高，并且有性能问题，你应首先优化查询，然后拆分表或使用复制'''
    return allMysqlStatus['Table_locks_waited']

def uptime(allMysqlStatus):
    '''查看MySQL本次启动后的运行时间(单位：秒)'''
    return allMysqlStatus['Uptime']

def uptimedate(uptime):
    '''查看MySQL本次启动的日期'''
    t = time.time() - int(uptime)
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('you should input Parameter!')
        sys.exit(2)
    parameter=eval(sys.argv[1])
    theMysql = MysqlConnect(parameter['host'],parameter['port'],parameter['user'],parameter['passwd'])
    conn = theMysql.connectdb()
    allMysqlStatus=theMysql.show_status(conn)
    result = {}
    result['os_type'] = os_type()
    result['show_databses'] =  theMysql.show_databases(conn)
    result['databses_sizes'] = theMysql.databses_sizes(conn)
    result['databses_character'] = theMysql.databses_character(conn)
    result['threads_connected'] = threads_connected(allMysqlStatus)
    result['aborted_clients'] = aborted_clients(allMysqlStatus)
    result['questions'] = questions(allMysqlStatus)
    result['opened_tables'] = opened_tables(allMysqlStatus)
    result['select_full_join'] = select_full_join(allMysqlStatus)
    result['select_scan'] = select_scan(allMysqlStatus)
    result['slow_queries'] = slow_queries(allMysqlStatus)
    result['slow_launch_threads'] = slow_launch_threads(allMysqlStatus)
    result['com_commit'] = com_commit(allMysqlStatus)
    result['table_locks_waited'] = table_locks_waited(allMysqlStatus)
    result['uptime'] = uptime(allMysqlStatus)
    result['uptimedate'] = uptimedate(result['uptime'])
    result = threshold_judge(result)
    theMysql.closeconnect()
    print(json.dumps(result))


