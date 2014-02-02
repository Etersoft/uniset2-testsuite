#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import threading
import datetime
import copy

from TestSuiteGlobal import *
import uniset
from ProcessMonitor import *
import TestSuitePlayer

class tt(): # test type
   Unknwn = 0
   Check = 1
   Action = 2
   Test = 3
   Outlink = 4
   Link = 5

class TestSuiteXMLPlayer(TestSuitePlayer.TestSuitePlayer):

    def __init__(self, testsuiteinterface, xmlfile,ignore_runlist=False):
        
        TestSuitePlayer.TestSuitePlayer.__init__(self,testsuiteinterface)
        
        # список мониторов (ключ в словаре - название xml-файла)
        self.pmonitor = dict()
        
        # список запущенных reset-потоков
        self.reset_thread_event = threading.Event()
        self.reset_thread_dict = dict()
        
        # словарь загруженных файлов
        # для реализации механизма ссылок на внешние файлы
        self.xmllist = dict()
        
        # словарь замен (для реализации шаблонов)
        self.replace_global_dict = dict()
        self.replace_test_dict = dict()
        self.replace_dict = dict()
        
        # загружаем основной файл
        self.global_ignore_runlist = ignore_runlist
        # словарь флагов игнорирование запуска <RunList>
        self.ignore_rlist = dict()
        # специальный Null process monitor
        self.null_pm = ProcessMonitor([])
        
        self.xml = self.loadXML(xmlfile)
       
        # воспользуемся свойством питон и добавим к классу нужное нам поле
        self.xml.begnode = None
        self.test_conf = ""
        
        self.show_result_report = False
        self.initConfig(self.xml)
        self.initTestList(self.xml)
        self.initProcessMonitor(self.xml)
    
    def get_begin_test_node(self,xml):
        return xml.begnode
    
    def getXML(self, fname):
        if fname in self.xmllist:
           return self.xmllist[fname]
        return None
        
    def loadXML(self, xmlfile):
        try:
           xml = None
           if not xmlfile in self.xmllist:
              xml = UniXML(xmlfile)
              self.xmllist[xmlfile] = xml              
           else:
              xml = self.xmllist[xmlfile]

           self.initConfig(xml)
           self.initTestList(xml)
           self.initProcessMonitor(xml)
           return xml
        
        except UniXMLException, e:
            self.tsi.log(t_FAILED,"(TestSuiteXMLPlayer:loadXML)","FAILED load xmlfile=%s err='%s'"%(xmlfile,e.getError()),False)
            raise TestSuiteException(e.getError())

    def initConfig(self,xml):
         rnode = xml.findNode(xml.getDoc(),"TestList")[0]
         if rnode == None:
            self.tsi.log(t_FAILED,"(TestSuiteXMLPlayer)","<TestList> not found?!",True)
            raise TestSuiteException("<TestList> not found?!")

         scenario_type = to_str(rnode.prop("type"))
         if scenario_type == "":
            scenario_type = "uniset"

         node = xml.findNode(xml.getDoc(),"Config")[0]
         if node == None:
            return

         node = xml.findNode(node,"aliases")[0]
         if node == None:
            return

         node = xml.firstNode(node.children)
         while node != None:

               c_type = to_str(node.prop("type"))
               if c_type == "":
                  c_type = scenario_type

               if c_type == "uniset":
                  ui = self.tsi.add_uniset_config(node.prop("confile"),node.prop("alias"))
                  if to_str(node.prop("default")) != "":
                     self.tsi.set_default_ui(ui)
               elif c_type == "modbus":
                  ui = self.tsi.add_modbus_config(node.prop("mbslave"),node.prop("alias"))
                  if to_str(node.prop("default")) != "":
                     self.tsi.set_default_ui(ui)
               else:
                  self.tsi.log(t_FAILED,"(TestSuiteXMLPlayer:initConfig)","Unknown scenario type='%s' Must be 'uniset' or 'modbus'"%c_type,True)
                  raise TestSuiteException("(TestSuiteXMLPlayer:initConfig): Unknown scenario type='%s' Must be 'uniset' or 'modbus'"%c_type)

               #print "add_config: " + str(node)
               node = xml.nextNode(node)

    def initTestList(self,xml):
         xml.begnode = xml.findNode(xml.getDoc(),"TestList")[0]
         if xml.begnode != None:
            trunc = to_int(self.replace(xml.begnode.prop("logfile_trunc")))
            self.tsi.set_logfile( self.replace(xml.begnode.prop("logfile")), trunc)
            self.tsi.set_notimestamp( to_int( self.replace(xml.begnode.prop("notimestamp"))) )
            self.add_to_global_replace( get_replace_list(to_str( self.replace(xml.begnode.prop("replace")))) )
            self.global_conf = self.replace(xml.begnode.prop("config"))
            xml.begnode = xml.begnode.children
            self.begin_tests(xml)
         else:
            self.tsi.log(t_FAILED,"(TestSuiteXMLPlayer)","Can`t find begin node <TestList>",True)
    
    def initProcessMonitor(self,xml):

         if xml.getFileName() in self.pmonitor:
            return
         
         rlist = xml.findNode(xml.getDoc(),"RunList")[0]
         if rlist != None:
             t_mp = ProcessMonitor()
             mp = copy.deepcopy(t_mp)
             mp.after_run_pause = to_int(rlist.prop("after_run_pause")) / 1000.0
             node = xml.firstNode(rlist.children)
#             print "load RUNLIST from " + str(xml.getFileName())
             while node != None:
#                 print "ADD TO RUNLIST %s"%str(node)
                 c = ChildProcess(node)
                 mp.addChild(c)
                 node = xml.nextNode(node)

#             print "ADD list: %s"%(str(mp.plist))
             self.pmonitor[xml.getFileName()] = mp
    
    def get_pmonitor(self,xml):
        
        if self.global_ignore_runlist == True:
           return self.null_pm
        
        ignore_rlist = False
        try:
           ignore_rlist = self.ignore_rlist[xml.getFileName()]
        except KeyError, ValueError:
           pass
        
        if ignore_rlist == True:
           return self.null_pm
        
        try:
           return self.pmonitor[xml.getFileName()]
        except KeyError, ValueError:
           pass
        
        # чтобы везде в коде не проверять pm!=None
        # просто возвращаем null монитор, с пустым списком
        # соответственно он ничего запускатьне будет
        self.pmonitor[xml.getFileName()] = self.null_pm
        return self.null_pm
    
    def set_ignore_runlist(self,xml,ignore_flag):
        self.ignore_rlist[xml.getFileName()] = ignore_flag
    
    def add_to_global_replace(self,lst):

        if lst == None:
           return		

        try:
            for v in lst:
                if v[0] != '' and v[0] != v[1]:
                   self.replace_global_dict[v[0]] = v[1]
        except KeyError, ValueError:
            pass   

    def add_to_test_replace(self,lst):

        if lst == None:
           return

        try:
            for v in lst:
                if v[0] != '' and v[0] != v[1]:
                   self.replace_test_dict[v[0]] = v[1]
        except KeyError, ValueError:
            pass
    
    def del_from_test_replace(self,lst):

        if lst == None:
           return

        try:
            for v in lst:
                if v[0] != '':
                   self.replace_test_dict.pop(v[0])
        except KeyError, ValueError:
            pass    

    def add_to_replace(self,lst):

        if lst == None:
           return

#       print "(add_to_replace): " + str(lst)
        try:
            for v in lst:
                if v[0] != '':
                   self.replace_dict[v[0]] = v[1]
        except KeyError, ValueError:
            pass
        #print "GLOBAL REPLACE: " + str(self.replace_global_dict)
        #print "TEST REPLACE: " + str(self.replace_test_dict)
        #print "ITEM REPLACE: " + str(self.replace_dict)
    
    def del_from_replace(self,lst):

        if lst == None:
           return		

#        print "(del_from_replace): " + str(lst)
        try:
          for v in lst:
              if v[0] != '':
                 self.replace_dict.pop(v[0])
        except KeyError, ValueError:
          pass

    def str_to_idlist(self, str_val,ui):
        lst = get_str_list(str_val)
        lst = self.replace_list(lst)
        str1 = list_to_str(lst)
        return get_int_list(str1)
    
    def replace_list(self, slist):
        res = []
        for v in slist:
            if len(v) < 1 or v == None or v[0] == v[1]:
               continue

            res.append( [self.replace(v[0]),self.replace(v[1])] )
        
        return res
        
    def replace(self,name):
        ''' преобразование, если есть в словаре замена.. '''
        if name==None or name=="" or name.__class__.__name__ == "int":
           return name
        #print "** replace **"
        #print "GLOBAL REPLACE: " + str(self.replace_global_dict)
        #print "TEST REPLACE: " + str(self.replace_test_dict)
        #print "ITEM REPLACE: " + str(self.replace_dict)
        
        name = self.replace_in(name,self.replace_dict)
        name = self.replace_in(name,self.replace_test_dict)
        name = self.replace_in(name,self.replace_global_dict)

        return name

    def replace_in(self,name,r_dict):
        try:
           for k,v in r_dict.items():
#               print "(repl): name=%s k=%s  v=%s"%(name,k,v)
               name = name.replace(k,v)

           return name  

        except KeyError, ValueError:
           pass
        
        return None

    def get_current_ui(self, alias):
        ui = self.tsi.get_ui(alias)
        if ui != None:
           return ui
        
        ui = self.tsi.get_ui(self.test_conf)
        if ui != None:
           return ui
        
        ui = self.tsi.get_ui(self.global_conf)
        if ui != None:
           return ui
        
        return self.tsi.get_default_ui()

    def get_outlink_filename(self, node):
        r_list = get_replace_list( to_str(self.replace(node.prop("replace"))))
        r_list = self.replace_list(r_list)
        self.add_to_replace(r_list)
        t_file = to_str(self.replace(node.prop("file"))).strip()
        self.del_from_replace(r_list)
        return t_file

    def get_link_param(self, node):
        t_link = to_str(self.replace(node.prop("link")))
        l = t_link.split("=")
        t_field = l[0]
        t_name = ""
        if t_field == None or t_field == "":
            t_field = "name"
            t_name = l[0]
        elif len(t_link) > 1:
            t_name = l[1]

        return (t_name,t_field)

    def getValue( self, node, xml ):
        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        return self.tsi.getValue(self.replace(node.prop("id")),ui)
        
    def check_item(self, node, xml):
        test = to_str( self.replace(node.prop("test"))).upper()
        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        if ui == None:
           self.tsi.actlog( t_FAILED,test,"FAILED: Unknown CONFIG..", True )
           return t_FAILED

        t_out = to_int(self.replace(node.prop("timeout")))
        t_check = to_int(self.replace(node.prop("check_pause")))
        if t_check <= 0:
           t_check = 500

        if test == "FALSE":
           return ( t_PASSED if self.tsi.isFalse(self.replace(node.prop("id")),t_out,t_check,ui) else t_FAILED )
        
        if test == "TRUE":
           return ( t_PASSED if self.tsi.isTrue(self.replace(node.prop("id")),t_out,t_check,ui) else t_FAILED )
        
        if test == "EQUAL":
           return ( t_PASSED if self.tsi.isEqual(self.replace(node.prop("id")),to_int(self.replace(node.prop("val"))),t_out,t_check,ui) else t_FAILED )
        
        if test == "GREAT":
           return ( t_PASSED if self.tsi.isGreat(self.replace(node.prop("id")),to_int(self.replace(node.prop("val"))),t_out,t_check,ui) else t_FAILED )
        
        if test == "LESS":
           return ( t_PASSED if self.tsi.isLess(self.replace(node.prop("id")),to_int(self.replace(node.prop("val"))),t_out,t_check,ui) else t_FAILED)
        
        if test == "MULTICHECK":
           self.tsi.log(" ", "MULTICHECK","...",False)
           s_set = to_str(self.replace(node.prop("id")))
           if s_set == "":
              self.tsi.log(t_FAILED,"(TestSuiteXMLPlayer)","MULTICHECK: undefined ID list (id='...')",True)
              return t_FAILED
           
           # для реализации механизма шаблонов
           # сперва разбиваем список на эелементы, подменяем каждый из них
           # собираем обратно, и уже разбираем как полагается (с разбивкой на id и val)
           slist = self.str_to_idlist(s_set,ui)
           res = True
           for s in slist:
               res = self.tsi.isEqual(self.replace(s[0]), self.replace(s[1]), t_out, t_check, ui )
           return ( t_PASSED if res else t_FAILED )
  
        if test == "EVENT":
           s_val = to_int(self.replace(node.prop("val")))
           return ( t_PASSED if self.tsi.isEvent(self.replace(node.prop("id")),s_val,t_out,t_check,ui) else t_FAILED )
        
        if test == "LINK":
           t_name, t_field = self.get_link_param(node)

           r_list = get_replace_list( to_str(self.replace(node.prop("replace"))))
           r_list = self.replace_list(r_list)
           self.add_to_replace(r_list)
           
           t_node = self.find_test(xml,t_name,t_field)
           if t_node != None:
              logfile = self.tsi.get_logfile()
              self.tsi.log(" ","LINK","go to %s='%s'" % (t_field,t_name), False)
              res = self.play_test(xml,t_node,logfile);
              self.del_from_replace(r_list)
              return res[0]
           
           self.del_from_replace(r_list)
           self.tsi.log(t_FAILED,"LINK","Not found test (%s='%s')" % (t_field, t_name),True)
           return t_FAILED
         
        if test == "OUTLINK":

           t_file = self.get_outlink_filename(node)
           if t_file == "":
              self.tsi.log(t_FAILED,"OUTLINK","Unknown file. Use file=''",True)
              return t_FAILED

           r_list = get_replace_list( to_str(self.replace(node.prop("replace"))))
           r_list = self.replace_list(r_list)
           self.add_to_replace(r_list)          
              
           t_ignore_runlist = to_int(self.replace(node.prop("ignore_runlist")))
           t_xml = self.xmllist.get(t_file)
           if t_xml == None:
              # если в списке ещё нет, запоминаем..
              try:
                 t_xml = self.loadXML(t_file)
              except UException, e:
                 self.del_from_replace(r_list)
                 self.tsi.log(t_FAILED,"OUTLINK","Can`t open file='%s'."%(t_file),True)
                 return t_FAILED
           
           self.set_ignore_runlist(t_xml,t_ignore_runlist)
           t_link = to_str(self.replace(node.prop("link")))
 
           if t_link == "ALL":
              self.tsi.log(" ","OUTLINK","go to file='%s' play ALL" % (t_file), False)
              res = self.play_xml(t_xml)
              # возващаем обобщённый результат
              # см. play_xml
              self.del_from_replace(r_list)
              return res[0]
           
           else:
              t_name,t_field = self.get_link_param(node)
              t_node = self.find_test(t_xml,t_name,t_field)
              if t_node != None:
                 logfile = self.tsi.get_logfile()
                 self.tsi.log(" ","OUTLINK","go to file='%s' %s='%s'" % (t_file,t_field,t_name), False)
                 res = self.play_test(t_xml,t_node,logfile);
                 self.del_from_replace(r_list)
                 return res[0]
              else:
                 self.del_from_replace(r_list)
                 self.tsi.log(t_FAILED,"OUTLINK","Not found in file='%s' test (%s='%s')" % (t_file, t_field, t_name),True)
                 return t_FAILED

        self.tsi.log(t_FAILED,"TestSuiteXMLPlayer","(check_item): Unknown item type='%s'" % test,True)
        return t_FAILED      

    def check_thread_event(self, event):
        if sys.version_info[1] == 5:
           return event.isSet()

        # if sys.version_info[1] == 6:
        return event.is_set()

    def add_reset_thread(self, t_name, t):
        
        if self.check_thread_event(self.reset_thread_event):
           self.reset_thread_event.wait()
        self.reset_thread_event.clear()
        try:
            self.reset_thread_dict[t_name] = t
        finally:
            self.reset_thread_event.set()

    def del_reset_thread(self,t_name):
        
        if self.check_thread_event(self.reset_thread_event):
           self.reset_thread_event.wait()
        self.reset_thread_event.clear()
        try:
           self.reset_thread_dict.pop(t_name)
        except KeyError, ValueError:
           pass        
        finally:
           self.reset_thread_event.set()
           
    
    def wait_finish_reset_thread(self, timeout_sec=15):
        
        if self.check_thread_event(self.reset_thread_event):
           self.reset_thread_event.wait()
        self.reset_thread_event.clear()
        if len(self.reset_thread_dict) <= 0:
           self.reset_thread_event.set()
           return
        tout = timeout_sec
        while tout>0:
          break_flag = True
          if self.check_thread_event(self.reset_thread_event):
             self.reset_thread_event.wait()
          self.reset_thread_event.clear()
          try:
              for t,t in self.reset_thread_dict.items():
                  if t.isAlive():
                     break_flag = False
                     self.tsi.actlog(" ","WAIT","waiting for finish reset value thread '%s'" % (t.getName()),False)
                     #t.join() # join - опасен тем, что можно застрять навечно..
          finally:
              self.reset_thread_event.set()
          
          if break_flag:
             return
          
          time.sleep(2)
          tout -= 2

    def get_item_config(self, node):
        cfig =self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        return ui.getConfFileName()

    def get_config_name(self, node):
        return to_str( self.replace(node.prop("config")))
        
    def action_item(self, node):
        act = self.replace(node.prop("name")).upper()
        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)        
        if ui == None:
           self.tsi.actlog( t_FAILED,act,"FAILED: Unknown CONFIG..", True )
           return t_FAILED
           
        if act == "SET":
           reset_msec = to_int(self.replace(node.prop("reset_time")))
           s_id = self.replace(node.prop("id"))
           if reset_msec <= 0:
              return ( t_PASSED if self.tsi.setValue(s_id,to_int(self.replace(node.prop("val"))), ui) else t_FAILED )
           s_v2 = to_int( self.replace(node.prop("val2")) )
           
           res = self.tsi.setValue( s_id, to_int(self.replace(node.prop("val"))), ui )
           self.tsi.actlog(" "," ","set reset time %d msec for id=%s" % (reset_msec,s_id),False)
           t = threading.Timer( (reset_msec/1000.), self.on_reset_timer, [s_id,s_v2,reset_msec,ui])
           self.add_reset_thread(t.getName(),t)
           t.start()
           return ( t_PASSED if res == True else t_FAILED )
        
        if act == "MULTISET":
           self.tsi.actlog(" ","MULTISET","...",False)
           # для реализации механизма шаблонов
           # сперва разбиваем список на эелементы, подменяем каждый из них
           # собираем обратно, и уже разбираем как полагается (с разбивкой на id и val)
           slist = self.str_to_idlist(to_str(self.replace(node.prop("set"))),ui)
           for s in slist:
               if self.tsi.setValue(self.replace(s[0]),self.replace(s[1]), ui) == False and self.tsi.ignorefailed == False:
                  return t_FAILED
           return t_PASSED
        
        if act == "MSLEEP":
           self.tsi.msleep( to_int(self.replace(node.prop("msec"))) )
           return t_PASSED

        if act == "SCRIPT":
           silent = True
           
           if to_int(self.replace(node.prop("show_output"))):
              silent = False
        
           if self.tsi.runscript( to_str(self.replace(node.prop("script"))), silent ) == False and self.tsi.ignorefailed == False:
              return t_FAILED      
           return t_PASSED
        
        self.tsi.actlog(t_FAILED,"(TestSuiteXMLPlayer)", "(action_item): Unknown action command='%s'" % act,True)           
        return t_FAILED 
    
    def on_reset_timer(self, s_id, s_val, s_msec, ui ):
        self.tsi.actlog( "","RESET", str("%10s: msec=%d id=%s val=%d" % ("on_reset_timer:",s_msec,s_id,s_val)),False)
        try:
            self.tsi.setValue(s_id,s_val,ui)
        except TestSuiteException, e:
            self.tsi.actlog( t_FAILED,"RESET", "FAILED: %s"%e.getError(), False )
        finally:
            if sys.version_info[1] == 5:        
               self.del_reset_thread( threading.currentThread().getName() )
            else: # python 2.6
               self.del_reset_thread( threading.current_thread().getName() )
               
        return False
    
    def begin( self, tnode ):
        if tnode != None:
            return tnode.children
        
        self.tsi.log(t_FAILED,"(TestSuiteXMLPlayer)", "Can`t find children items for <test>",True)
        return None
    
    def begin_tests( self, xml ):
        testnode = xml.findNode(xml.begnode,"test")[0]
        if testnode != None:
            testnode = xml.firstNode(testnode)
            firstnode = testnode.children
            return [testnode,firstnode]
        
        self.tsi.log(t_FAILED,"(TestSuiteXMLPlayer)","Can`t find begin node <test>",True)
        return [None,None]
    
    def print_result_report(self,results):
        if self.show_result_report == True:
           print "RESULT REPORT:\n**************"
           i = 1
           ttime = 0
           for res in results:
#               cr = self.get_cumulative_result([[res[0],res[1],res[2]]])
               td = datetime.timedelta(0,res[2])
               print "%3d. [%6s] - %s /%s/" % (i,res[0],res[1],td)
               i = i+1
               ttime = ttime + res[2]
           
           td = datetime.timedelta(0,ttime)
           ts = str(td).split('.')[0]
           print "--------------\nTotal time: %s\n"%ts
    
    def play_all( self, xml = None ):
        if xml == None:
           xml = self.xml
        
        logfile = self.tsi.get_logfile()
        b = self.begin_tests(xml)
        testnode = b[0]
        results = []
        tm_start = 0
        
        pmonitor = self.get_pmonitor(xml)
        try:
            pmonitor.start()
            while testnode != None:
               tm_start = time.time()
               results.append( self.play_test(xml,testnode,logfile) )
               testnode = xml.nextNode(testnode)
        except TestSuiteException, e:
            ttime = e.getFinishTime() - tm_start
            results.append( [t_FAILED,to_str(self.replace(testnode.prop("name"))),ttime] )
            raise e   

        finally:
            self.print_result_report(results)
            pmonitor.stop()
    
    def play_xml( self, xml ):
        
        logfile = self.tsi.get_logfile()
        b = self.begin_tests(xml)
        testnode = b[0]
        results = []
        tm_start = 0
        tm_all_start = time.time()
        pmonitor = self.get_pmonitor(xml)
        try:
            pmonitor.start()
            while testnode != None:
               tm_start = time.time()
               res = self.play_test(xml,testnode,logfile)
               results.append(res)
               testnode = xml.nextNode(testnode)
        
        except TestSuiteException, e:
            tname = to_str(self.replace(testnode.prop("name")))
            ttime = e.getFinishTime() - tm_start
            results.append( [t_FAILED,tname,ttime] )
            res = self.get_cumulative_result(results)
            raise e
        
        finally:
            pmonitor.stop()
        
        res = self.get_cumulative_result(results)
        ttime = time.time() - tm_all_start
        return [res,results,ttime]
        
    
    def find_test( self, xml, tname, propname="name" ):
        if xml.begnode != None:
          tnode = xml.begnode
          while tnode != None:
              if to_str(tnode.prop(propname)).strip() == tname:
                 return tnode
              tnode = xml.nextNode(tnode)
        
        return None

    def play_by_name( self, xml, tname, propname="name" ):
        
        logfile = self.tsi.get_logfile()
        b = self.begin_tests(xml)
        testnode = b[0]
        results = []
        tnode = self.find_test(xml,tname,propname)
        if tnode == None:
           self.tsi.log(t_FAILED,"(TestSuiteXMLPlayer)","Can`t find test='%s'"%tname,True)
           return
        
        tm_start = time.time()
        pmonitor = self.get_pmonitor(xml)
        try:
            pmonitor.start()
            results.append(self.play_test(xml,tnode,logfile))
            pmonitor.stop()
        except TestSuiteException, e:
            ttime = e.getFinishTime() - tm_start
            results.append( [t_FAILED,to_str(self.replace(testnode.prop("name"))),ttime] )
            raise e
        
        finally:
            self.print_result_report(results)
            pmonitor.stop()

    def play_item( self, inode, xml ):
        if inode.name == "action":
           return self.action_item(inode)
        elif inode.name == "check":
           return self.check_item(inode,xml)
        
        return t_UNKNOWN

    def play_test( self, xml, testnode, logfile ):
        
        t_name = to_str(self.replace(testnode.prop("name")))
        
        t_ignore = to_int(self.replace(testnode.prop("ignore")))
        if t_ignore:
           self.tsi.log(t_IGNORE,t_IGNORE, "'%s'" % t_name ,False)
           return [t_IGNORE,t_name,0]

        curnode = self.begin(testnode)

        mylog = to_str(self.replace(testnode.prop("logfile")))
        mylog_trunc = to_int(self.replace(testnode.prop("logfile_trunc")))
        if  mylog != "":
            self.tsi.set_logfile(mylog,mylog_trunc)
        elif self.tsi.get_logfile() != logfile:
            self.tsi.set_logfile(logfile)
        
        r_list = get_replace_list(to_str(self.replace(testnode.prop("replace"))))
        r_list = self.replace_list(r_list)
        self.add_to_test_replace(r_list)
        
        self.tsi.set_ignorefailed( to_int(self.replace(testnode.prop("ignore_failed"))) )
        self.test_conf = self.replace(testnode.prop("config"))
        
        self.tsi.log( "","BEGIN", "'%s'" % t_name ,False)
        i_res = []
        tm_start = time.time()
        tm_finish = tm_start;
        try:
            while curnode != None:
               res = self.play_item(curnode,xml)
               if res != t_UNKNOWN:
                  i_res.append(res)
               curnode = xml.nextNode(curnode)
        except TestSuiteException, e:
            i_res.append(t_FAILED)
            tm_finish = e.getFinishTime()
            raise e
        else:
            tm_finish = time.time()
        finally:
            self.wait_finish_reset_thread()
            self.del_from_test_replace(r_list)
            self.test_conf = ""
            res = self.get_cumulative_result(i_res)    
            ttime = tm_finish - tm_start
            td = datetime.timedelta(0,ttime)
            self.tsi.log( res, "FINISH" ,"'%s' /%s/" % (t_name,td), False)

        return [res,t_name,ttime]

    def get_cumulative_result(self, results):
        i_res = 0
        f_res = 0
        p_res = 0
        w_res = 0
        u_res = 0
        c_res = ""
        for res in results:
            if res.__class__.__name__ == 'list':
               r = res[0]
            else:
               r = res

            if r == t_PASSED:
               p_res += 1
            elif r == t_FAILED:
               f_res += 1
            elif r == t_IGNORE:
               i_res += 1
            elif r == t_IGNORE:
               w_res += 1
            else:
               u_res += 1

        if w_res > 0:
           c_res = t_WARNING
        elif f_res>0 and p_res == 0 and i_res == 0:
           c_res=t_FAILED
        elif p_res>0 and f_res == 0 and i_res >= 0:
           c_res=t_PASSED
        elif i_res>0 and p_res == 0 and f_res == 0:
           c_res=t_IGNORE
        else:
           c_res = t_WARNING

        #print "cumulative: RES=%s (f_res=%d p_res=%d i_res=%d w_res=%d unknown=%d) for %s"%(c_res,f_res,p_res,i_res,w_res,u_res,str(results))
        return c_res



if __name__ == "__main__":

    from TestSuiteInterface import *
    
    ts = TestSuiteInterface()
    try:

        if ts.checkArgParam("--help",False) == True or ts.checkArgParam("-h",False) == True:
            print "Usage: %s [--confile [configure.xml|alias@conf1.xml,alias2@conf2.xml,..]  --testfile scenarion.xml" % sys.argv[0]
            print "\n"
            print "--confile [conf.xml,alias1@conf.xml,..]  - Configuration file."
            print "--testfile tests.xml      - Test scenarion file."
            print "--show-test-log           - Show test log"
            print "--show-action-log         - Show actions log"
            print "--show-result-report      - Show result report "
            print "--test-name TestName      - Run only 'TestName' test"
            print "--test-name-prop propname - Name of property for search test by name (for --test-name only)"
            print "--ignore-run-list         - Ignore <RunList>"
            print "--no-timestamp            - Does not display the time"
            print "--ignore-nodes            - Do not use '@node'"
            exit(0)

        testfile = ts.getArgParam("--testfile","")
        if testfile == "":
           print "(TestSuiteXMLPlayer): Unknown testfile. Use --testfile\n"
           exit(1)
        
            
        conflist = ts.getArgParam("--confile","")
        show_log = ts.checkArgParam("--show-test-log",False)
        show_actlog = ts.checkArgParam("--show-action-log",False)
        show_result = ts.checkArgParam("--show-result-report",False)
        testname = ts.getArgParam("--test-name","")
        testname_prop = ts.getArgParam("--test-name-prop","name")
        ignore_runlist = ts.checkArgParam("--ignore-run-list",False)
        notimestamp = ts.checkArgParam("--no-timestamp",False)
        ignore_nodes = ts.checkArgParam("--ignore-nodes",False)

        cf = conflist.split(',')
        ts.init_testsuite(cf,show_log,show_actlog)
        ts.set_notimestamp(notimestamp)
        ts.set_ignore_nodes(ignore_nodes)
        
        player = TestSuiteXMLPlayer(ts,testfile,ignore_runlist)
        player.show_result_report = show_result
        
        if testname != "":
           player.play_by_name(player.xml,testname,testname_prop)
        else:
           player.play_all()
        
        exit(0)
    
    except TestSuiteException, e:
        print "(TestSuiteXMLPlayer): catch exception: " + str(e.getError())
    except UException, e:
        print "(TestSuiteXMLPlayer): catch exception: " + str(e.getError())
    except KeyboardInterrupt:
        print "(TestSuiteXMLPlayer): catch keyboard interrupt.. "
    
    exit(1)