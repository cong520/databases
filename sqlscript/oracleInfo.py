#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding:utf-8
#@Time     : 2018-04-09 15:41:33
#@Author   : chengengcong
#@File     : mysqlInfo
#@Library  : pymysql
#@Parameter: "{'host':'127.0.0.1','port':1521,'user':'orlc','passwd':'123456','db':'ORAL'}"
# import argparse
import json
import platform
import cx_Oracle
import sys,os,re
import collections
from subprocess import Popen, PIPE

class OracleConnect(object):
    def __init__(self,host,port,user,passwd,db):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.db = db
        try:
            self.tns=cx_Oracle.makedsn(self.host,int(self.port),self.db)
            self.conn = cx_Oracle.connect(self.user,self.passwd,self.tns)
        except:
            print('oracle cannot connect!')
            sys.exit(2)

    def connectdb(self):
        cursor = self.conn.cursor()
        return cursor

    def closeconnect(self):
        self.conn.close()
    
    def instance_name(self,cursor):
        '''获取数据库实例名'''
        cursor.execute("select instance_name from v$instance")
        result = cursor.fetchone()
        return result[0]
    
    def show_dbid(self,cursor):
        '''获取数据库实例ID'''
        cursor.execute("select dbid from v$database")
        result = cursor.fetchone()
        return result[0]

    def show_tables(self,cursor):
        '''显示当前数据库的所有表'''
        cursor.execute("select TABLE_NAME from user_tables")
        result = cursor.fetchall()
        tables = []
        for i in result:
            tables.append(i[0])
        return tables

    def db_block_size(self,cursor):
        '''获取数据库块大小(K)'''
        cursor.execute("select value from v$parameter where name='db_block_size'")
        result = cursor.fetchone()
        return result[0]
    
    def db_character(self,cursor):
        '''获取数据库字符集'''
        cursor.execute("select * from nls_database_parameters where parameter='NLS_NCHAR_CHARACTERSET'")
        result = cursor.fetchone()
        return result[1]

    def judge_if_arm(self,cursor):
        '''判断是否ASM'''
        cursor.execute("select name from v$datafile order by FILE# desc")
        result = cursor.fetchone()
        if result[0].startswith('+'):
            return 'YES'
        else:
            return 'NO'

    def judge_if_cdb(self,cursor):
        '''检查数据库是否为容器库CDB'''
        try:
            cursor.execute("select CDB from v$database")
        except:
            return 'NO'
        result = cursor.fetchone()
        return result[0]

    def db_version(self,cursor):
        '''获取数据库版本号'''
        cursor.execute("select * from v$version")
        result = cursor.fetchone()
        return result[0]
    
    def db_small_version(self,cursor):
        '''获取数据库小版本号'''
        cursor.execute("select version from product_component_version")
        result = cursor.fetchall()
        return result[1][0]
        
    def db_sga(self,cursor):
        '''获取当前，SGA使用大小MB'''
        cursor.execute("select name,total,round(total-free,2) used, round(free,2) free,round((total-free)/total*100,2) pctused from (select 'SGA' name,(select sum(value/1024/1024) from v$sga) total,(select sum(bytes/1024/1024) from v$sgastat where name='free memory')free from dual)")
        result = cursor.fetchall()
        return result[0][2]

    def db_pga(self,cursor):
        '''获取当前，PGA使用大小MB'''
        cursor.execute("select name,total,round(used,2)used,round(total-used,2)free,round(used/total*100,2)pctused from (select 'PGA' name,(select value/1024/1024 total from v$pgastat where name='aggregate PGA target parameter')total,(select value/1024/1024 used from v$pgastat where name='total PGA allocated')used from dual)")
        result = cursor.fetchall()
        return result[0][2]

def oracle_sqlplus(sql):
    '''公用函数'''
    proc = Popen(["sqlplus", "-S", "/", "as", "sysdba"], stdout=PIPE, stdin=PIPE, stderr=PIPE)
    proc.stdin.write(sql)
    (out, err) = proc.communicate()
    if err:
        return err
    else:
        return out

def amm_or_asmm():
    '''检查数据库实例内存管理机制'''
    result=oracle_sqlplus('show parameter memory_target')
    memory_target=re.findall( r'\d+',result, re.M)
    if int(memory_target[0]):
        return 'AMM'
    else:
        result=oracle_sqlplus('show parameter sga_target')
        sga_target=re.findall( r'\d+',result, re.M)
        if int(sga_target[0]):
            return 'ASMM'
        else:
            return 'all not'

def new_patch_version():
    '''获取数据库最新补丁版本'''
    cmd= '%ORACLE_HOME%/OPatch/opatch lsinventory'
    k=os.popen(cmd)
    result=k.read()
    matchObj = re.findall( r'(Patch.*?applied on.*?)\n', result, re.M)
    return matchObj

def os_type():
    '''获取操作系统类型'''
    return platform.system()

def judge_if_virtual():
    '''判断是否虚拟机'''
    os_type=platform.system().lower()
    if os_type == 'windows':
        # cmd= '''Systeminfo"'''
        # windows=os.popen(cmd)
        # return windows.read().lower().find('时区')
        return 'unknown'
    elif os_type == 'linux':
        shell= '''dmesg | grep -i "\<virtual" |wc l'''
        linux=os.popen(shell)
        if int(linux.read()):
            return 'YES'
        else:
            return 'NO'
    else:
        return 'unknown'

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('you should input Parameter!')
        sys.exit(2)
    parameter=eval(sys.argv[1])
    theOracle = OracleConnect(parameter['host'],parameter['port'],parameter['user'],parameter['passwd'],parameter['db'])
    conn = theOracle.connectdb()

    result = collections.OrderedDict()
    result['os_type'] = os_type()
    result['show_tables'] = theOracle.show_tables(conn)
    result['dbid'] = theOracle.show_dbid(conn)
    result['db_name'] = parameter['db']
    result['instance_name'] = theOracle.instance_name(conn)
    result['db_block_size'] = theOracle.db_block_size(conn)
    result['db_character'] = theOracle.db_character(conn)
    result['db_port'] = parameter['port']
    result['if_arm'] = theOracle.judge_if_arm(conn)
    result['if_cdb'] = theOracle.judge_if_cdb(conn)
    result['db_version'] = theOracle.db_version(conn)
    result['db_small_version'] = theOracle.db_small_version(conn)
    result['new_patch_version'] = new_patch_version()
    result['judge_if_virtual'] = judge_if_virtual()
    result['db_sga'] = theOracle.db_sga(conn)
    result['db_pga'] = theOracle.db_pga(conn)
    result['amm_or_asmm'] = amm_or_asmm()
    # result['databses_character'] = theMysql.databses_character(conn)
    # result['threads_connected'] = threads_connected(allMysqlStatus)
    # result['aborted_clients'] = aborted_clients(allMysqlStatus)
    # result['questions'] = questions(allMysqlStatus)
    # result['opened_tables'] = opened_tables(allMysqlStatus)
    # result['select_full_join'] = select_full_join(allMysqlStatus)
    # result['select_scan'] = select_scan(allMysqlStatus)
    # result['slow_queries'] = slow_queries(allMysqlStatus)
    # result['slow_launch_threads'] = slow_launch_threads(allMysqlStatus)
    # result['com_commit'] = com_commit(allMysqlStatus)
    # result['table_locks_waited'] = table_locks_waited(allMysqlStatus)
    # result['uptime'] = uptime(allMysqlStatus)
    # result['uptimedate'] = uptimedate(result['uptime'])
    # result = threshold_judge(result)

    #json.dumps 序列化时对中文默认使用的ascii编码.想输出真正的中文需要指定ensure_ascii=False,indent=4 格式化输出字典
    print(json.dumps(result,ensure_ascii=False,indent=4))



