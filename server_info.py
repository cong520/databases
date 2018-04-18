#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time     : 2018.4.8
# @Author   : Tanxiaoshu
# @File     : server_info.py
# @Library  :
# @Parameter:{'cpu_percent':"90",'mem_percent':"90",'disk_percent':"90"}

import platform
import time
import socket
import subprocess
import re
import os
import multiprocessing
from collections import namedtuple
import json
import sys

minions = eval(sys.argv[1])
#minions = {'cpu_percent':"90",'mem_percent':"90",'disk_percent':"90"}
result = {}

if platform.system().lower() == 'linux':
	def ip():
		'''获取主机IP地址'''
		try:
			sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
			sock.connect(('8.8.8.8',80))
			Ip = sock.getsockname()[0]
			result['ip'] = Ip
			#print(result['ip'])
			return result['ip']
		except:
			result['ip'] = None
			return result['ip']

	def os_version():
		'''获取主机类型及版本'''
		result['os_version'] = platform.platform()
		return result['os_version']

	def uptime():
		'''主机运行时间'''
		with open("/proc/uptime") as f:
			for line in f:
				up_time = float(line.split()[0].split(".")[0]) / 86400
				result['os_uptime'] = str(float("%.1f" % up_time)) + "day"
				# print(result['os_uptime'])
				return result['os_uptime']

	def now_time():
		'''主机当前时间'''
		result['now_time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
		return result['now_time']


	def lv():
		'''主机LVM状态'''
		try:
			res = subprocess.Popen(['lvdisplay'], stdout=subprocess.PIPE, shell=True)
			stdout = res.stdout
			# print(stdout)
			lv_status = []
			for line in stdout.readlines():
				# print(line)
				if re.search('LV Status', line):
					status = line.split()[2]
					if status == "NOT available":
						lv_status.append(status)

			result['lv_status'] = len(lv_status)
			#print(result['lv_status'])
		except:
			result['lv_status'] = None

	def message_log():
		'''主机message日志巡检'''
		month = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'June', '07': 'July', '08': 'Aug', '09': 'Sept', '10': 'Oct', '11': 'Nov', '12': 'Dec'}
		try:
			os_month = time.strftime("%m", time.localtime())
			os_day = re.search('[1-9].?', time.strftime("%d", time.localtime())).group()
			if int(os_day) < 10:
				day = month[os_month] + '  ' + os_day
			else:
				day = month[os_month] + ' ' + os_day

			with open('/var/log/messages', 'r') as f:
				i = 0
				for line in f:
					# print(line)
					if re.search(r'%s.*(Error|error)' % (day), line):
						i += 1
				result['message_log'] = i
			return result['message_log']
		except:
			result['message_log'] = None
			return result['message_log']

	def dmesg_log():
		'''主机dmesg日志巡检'''
		try:
			with open('/var/log/dmesg', 'r') as f:
				i = 0
				for line in f:
					# print(line)
					if re.search(r'(Error|error)', line):
						i += 1
				result['dmesg_log'] = i
			return result['dmesg_log']
		except:
			result['dmesg_log'] = None
			return result['dmesg_log']

	def cpu():
		'''获取主机CPU状态及使用率'''
		result['cpu_core'] = multiprocessing.cpu_count()
		cmd1 = subprocess.Popen('cat /proc/stat|grep -w cpu', shell=True, stdout=subprocess.PIPE)
		cpu_info1 = cmd1.stdout.read().strip().split()
		cpu_used1 = int(cpu_info1[1])
		total1 = int(cpu_info1[1]) + int(cpu_info1[2]) + int(cpu_info1[3]) + int(cpu_info1[4]) + int(cpu_info1[5]) + int(cpu_info1[6]) + int(cpu_info1[7])
		time.sleep(1)
		cmd2 = subprocess.Popen('cat /proc/stat|grep -w cpu', shell=True, stdout=subprocess.PIPE)
		cpu_info2 = cmd2.stdout.read().strip().split()
		cpu_used2 = int(cpu_info2[1])
		total2 = int(cpu_info2[1]) + int(cpu_info2[2]) + int(cpu_info2[3]) + int(cpu_info2[4]) + int(cpu_info2[5]) + int(cpu_info2[6]) + int(cpu_info2[7])
		cpu_idel = cpu_used2 - cpu_used1
		total = total2 - total1
		cpu_used = cpu_idel * 100 // total
		# cpu_result['cpu_used'] = cpu_used
		if int(cpu_used) > int(minions['cpu_percent']):
			result['cpu_status'] = "异常"
		else:
			result['cpu_status'] = "正常"
		# print(result['cpu_status'])
		return result['cpu_status']

	def process():
		'''获取主机进程数'''
		stdout = subprocess.Popen('ps -ef|wc -l',shell=True,stdout=subprocess.PIPE).stdout.read().strip()
		result['process'] = stdout
		return result['process']

	def process_zombie():
		'''获取主机僵尸进程数'''
		stdout = subprocess.Popen('top -n1|head -2|tail -1', shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		#print(stdout)
		#zombie = re.search(r'stopped,\s*?([0-9]).*zombie',stdout)
		zombie = re.split('\s+',stdout)
		result['zombie'] = zombie[-2]
		#print(result['zombie'])
		return result['zombie']



	#巡检磁盘
	disk_ntuple = namedtuple('partition', 'device mountpoint fstype')
	usage_ntuple = namedtuple('usage', 'total used free percent')  # 获取当前操作系统下所有磁盘

	def disk_partitions(all=False):
		# 获取文件系统及所使用的分区
		"""Return all mountd partitions as a nameduple. 
		If all == False return phyisical partitions only. 
		"""
		phydevs = []
		f = open("/proc/filesystems", "r")
		for line in f:
			if not line.startswith("nodev"):
				phydevs.append(line.strip())
		# print(phydevs)
		f.close()

		retlist = []
		f = open('/etc/mtab', "r")
		for line in f:
			if not all and line.startswith('none'):
				continue
			fields = line.split()
			device = fields[0]
			mountpoint = fields[1]
			# print(mountpoint)
			fstype = fields[2]
			# print(line)
			if not all and fstype not in phydevs:
				continue
			if device == 'none':
				device = ''
			ntuple = disk_ntuple(device, mountpoint, fstype)
			retlist.append(ntuple)
		f.close
		# print(retlist)
		return retlist

	def disk_usage(path):
		# 统计某磁盘使用情况，返回对象
		"""Return disk usage associated with path."""
		st = os.statvfs(path)
		free = (st.f_bavail * st.f_frsize)
		total = (st.f_blocks * st.f_frsize)
		used = (st.f_blocks - st.f_bfree) * st.f_frsize
		try:
			percent = (float(used) / total) * 100
		except ZeroDivisionError:
			percent = 0
		return usage_ntuple(total, used, free, int(percent))

	def disk():
		for i in disk_partitions():
			#获取磁盘使用率
			# print(i[1])
			value = list(disk_usage(i[1]))
			result[i[1]] = str(value[3]) + "%"
			if int(value[3]) < minions['disk_percent']:
				result[i[1] + "_status"] = "OK"
			else:
				result[i[1] + "_status"] = "ERROR"
			# print(result[i[1]],result[i[1] + "status"])
		# print(result)


	def mem_info():
		'''获取内存大小，使用率等'''
		meminfo = {}
		with open('/proc/meminfo') as f:
			for line in f:
				meminfo[line.split(':')[0]] = int(line.split(':')[1].strip().split()[0])
		result['mem_total'] = str(int(meminfo['MemTotal']) // 1024) + "M"
		# mem_result['free_mem'] = meminfo['MemFree']
		used_mem = int(meminfo['MemTotal']) - int(meminfo['MemFree']) - int(meminfo['Buffers']) - int(meminfo['Cached'])
		result['mem_used'] = str((int(meminfo['MemTotal']) - int(meminfo['MemFree']) - int(meminfo['Buffers']) - int(meminfo['Cached'])) // 1024) + "M"
		# print(mem_result)
		mem_used_percent = int(used_mem) * 100 // int(meminfo['MemTotal'])
		result['mem_used_percent'] = str(mem_used_percent) + "%"
		# print(mem_used_percent)
		if mem_used_percent > minions['mem_percent']:
			result['mem_status'] = '异常'
		else:
			result['mem_status'] = '正常'
		#print(result)
		#return {'mem_total': result['total_mem'], 'mem_percent': result['mem_status']}

	def swap():
		'''获取swap大小及使用率等'''
		with open('/proc/meminfo','r') as f:
			for line in f:
				if line.startswith('SwapTotal'):
					swaptotal = line.split()[1]
					result['swaptotal'] = str(int(swaptotal) // 1024) + "M"
					#print(swaptotal)
				elif line.startswith('SwapFree'):
					swapfree = line.split()[1]
					#print(swapfree)
			swap_used = (int(swaptotal) - int(swapfree)) // int(swaptotal) * 100
			swap_used_percent = '{:.0%}'.format(swap_used)
			result['swap_used_percent'] = swap_used_percent
			return result['swap_used_percent']


elif platform.system().lower() == 'windows':
	pass
elif platform.system().lower() == 'aix':
	pass


if platform.system().lower() == 'linux' and os.geteuid() != 0:
	print('please run used root')
elif platform.system().lower() == 'linux':
	ip()
	os_version()
	uptime()
	now_time()
	lv()
	message_log()
	dmesg_log()
	cpu()
	process()
	process_zombie()
	disk()
	mem_info()
	swap()
	data = json.dumps(result,ensure_ascii=False,indent=4)
	print(data)

