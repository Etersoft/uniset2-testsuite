#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import copy
import string
import os

from ProcessMonitor import *
import TestSuitePlayer
from TestSuiteInterface import *


class keys():
    pause = ' '  # break
    step = 's'  # on 'step by step' mode


class tt():  # test type
    Unknwn = 0
    Check = 1
    Action = 2
    Test = 3
    Outlink = 4
    Link = 5


# RESULT FORMAT:
# ------------------------------------------
class res():
    Result = 0
    Name = 1
    Time = 2
    Error = 3
    File = 4

class StackItem():

    def __init__(self,t_name, t_level, t_fname, t_comment, t_result=t_UNKNOWN, t_prev=None):
        self.t_level = t_level
        self.t_fname = t_fname
        self.t_name = t_name
        self.t_comment = t_comment
        self.t_result = t_result
        self.t_prev = t_prev

    def __repr__(self):
        return "[%d, '%s', '%s', '%s', '%s', %s]"%(self.t_level,self.t_fname,self.t_name,self.t_comment,self.t_result,str(self.t_prev))

# result[TEST RESULT, TEST NAME, TEST TIME, TEST ERR, TEST FILE]
# ------------------------------------------ 
# TEST RESULT: t_NONE, t_FAILED, .... view TestSuiteGlobal.py

class TestSuiteXMLPlayer(TestSuitePlayer.TestSuitePlayer):
    def __init__(self, testsuiteinterface, xmlfile, ignore_runlist=False):

        TestSuitePlayer.TestSuitePlayer.__init__(self, testsuiteinterface)

        self.rootworkdir = os.getcwd()
        # список мониторов (ключ в словаре - название xml-файла)
        self.pmonitor = dict()

        self.mcheck = re.compile(r"([\w@\ #$%_\]\[\{\}]{1,})=([-\d\ ]{1,})")
        self.rless = re.compile(r"test=\"([\w@\ #$%_\ :\]\[\{\}]{1,})(<{1,})([-\ \w:=@#$%_]{0,})\"")

        # список запущенных reset-потоков
        self.reset_thread_event = threading.Event()
        self.reset_thread_dict = dict()

        # словарь загруженных файлов
        # для реализации механизма ссылок на внешние файлы
        self.xmllist = dict()

        # спискок со списками замен (получаемых из replace="..") с учётом добавления (зоны видимости)
        self.replace_stack = list()

        # список пар [level,testname, xmlfile]
        # level - уровень вложенности вызова
        # testname - название теста (или файла если это outlink)
        # xmlfile - имя файла теста
        self.call_stack = list()

        # текущий уровень вложенности
        self.call_level = 0

        # загружаем основной файл
        self.global_ignore_runlist = ignore_runlist
        # словарь флагов игнорирование запуска <RunList>
        self.ignore_rlist = dict()
        # специальный Null process monitor
        self.null_pm = ProcessMonitor([])

        self.xml = self.loadXML(xmlfile)
        self.filename = xmlfile

        # воспользуемся свойством питон и добавим к классу нужное нам поле
        self.xml.begnode = None
        self.xml.global_replace_list = None
        self.test_conf = ""

        self.show_result_report = False
        self.initConfig(self.xml)
        self.initTestList(self.xml)
        self.add_to_global_replace(self.xml.global_replace_list)
        self.initProcessMonitor(self.xml)
        self.keyb_inttr_callback = None

        self.default_timeout = 5000
        self.default_check_pause = 300
        self.junit = ""

        # def __del__(self):
        # os.chdir(self.rootworkdir)

    def add_result(self, res):
        pass

    def build_failtrace(self, call_trace):

        if len(call_trace) == 0:
            return list()

        # идём в обратном порядке
        # от последнего вызова (это тот на котором вывалился тест) до первого
        # Смысл: построить дерево вызовов от провалившегося до первого уровня
        # пропуская успешные (т.е. строится дерево вызовов приведшее до провалившегося теста)
        # -----
        # т.к. у нас сохранены ссылки на предыдущие вызовы... то просто идём по ним
        failtrace = list()
        stackItem = call_trace[-1]
        failtrace.append(stackItem)
        curlevel = stackItem.t_level
        print "BEGIN LEVEL: %d "%curlevel

        while stackItem != None:

            stackItem = stackItem.t_prev

            if stackItem == None:
                break

            if stackItem.t_level < curlevel:
                failtrace.append(stackItem)
                curlevel = stackItem.t_level

            if stackItem.t_level == 0:
                break

        return failtrace[::-1]

    def print_calltrace(self, call_limit):

        # выводим только дерево вызовов до неуспешного теста
        # для этого надо построить дерево от последнего вызова до первого
        failtrace = self.build_failtrace(self.call_stack)

        tname_width = 40
        call_limit = abs(call_limit)
        ttab = "=== TESTFILE ==="

        print "%s| %s" % (
        self.tsi.colorize_test_begin(ttab.ljust(tname_width)), self.tsi.colorize_test_begin("=== TEST CALL TRACE (limit: %d) ==="%call_limit))

        for stackItem in failtrace[-call_limit::]:
            tab = ""
            for i in range(0, stackItem.t_level):
                tab = "%s.   " % (tab)

            t_comment = ""
            if self.tsi.log_show_test_comment:
                t_comment = " | %s " % self.tsi.format_comment(stackItem.t_comment)

            # if not self.show_xmlfile:
            #     t_fname = ""

            print "%s%s| %s%s" % (stackItem.t_fname.ljust(tname_width), t_comment, tab, stackItem.t_name)

        print ""

    def set_keyboard_interrupt(self, callback):
        self.keyb_inttr_callback = callback

    def check_keyboard_interrupt(self):
        if self.keyb_inttr_callback != None:
            self.keyb_inttr_callback()

    def get_begin_test_node(self, xml):
        return xml.begnode

    def getXML(self, fname):
        if fname in self.xmllist:
            return self.xmllist[fname]
        return None

    def loadXML(self, xmlfile):
        try:
            xml = None
            if not xmlfile in self.xmllist:
                fdoc = open(xmlfile, 'r')
                txt = fdoc.read()
                fdoc.close()
                # Заменяем символы '<', для создания и загрузки корректного xml
                txt = self.rless.sub(r'test="\1&lt;\3"', txt)
                xml = UniXML(txt, True)
                # если UniXML создан из текста, а не файла (см. выше)
                # тогда надо искуственно инициализировать fname, потому-что
                # он используется в качестве ключа..
                xml.fname = xmlfile
                self.xmllist[xmlfile] = xml
            else:
                xml = self.xmllist[xmlfile]

            self.initConfig(xml)
            self.initTestList(xml)
            self.initProcessMonitor(xml)
            return xml

        except UniXMLException, e:
            self.tsi.log(t_FAILED, "(TestSuiteXMLPlayer:loadXML)",
                         "FAILED load xmlfile=%s err='%s'" % (xmlfile, e.getError()), "", False)
            raise TestSuiteException(e.getError())

    def initConfig(self, xml):
        rnode = xml.findNode(xml.getDoc(), "TestList")[0]
        if rnode is None:
            self.tsi.log(t_FAILED, "(TestSuiteXMLPlayer)", "<TestList> not found?!", "", True)
            raise TestSuiteException("<TestList> not found?!")

        scenario_type = to_str(rnode.prop("type"))
        if scenario_type == "":
            scenario_type = "uniset"

        node = xml.findNode(xml.getDoc(), "Config")[0]
        if node is None:
            return

        node = xml.findNode(node, "aliases")[0]
        if node is None:
            return

        node = xml.firstNode(node.children)
        while node is not None:

            c_type = to_str(node.prop("type"))
            if c_type == "":
                c_type = scenario_type

            if c_type == "uniset":
                ui = self.tsi.add_uniset_config(node.prop("confile"), node.prop("alias"))
                if to_str(node.prop("default")) != "":
                    self.tsi.set_default_ui(ui)
            elif c_type == "modbus":
                ui = self.tsi.add_modbus_config(node.prop("mbslave"), node.prop("alias"))
                if to_str(node.prop("default")) != "":
                    self.tsi.set_default_ui(ui)
            else:
                self.tsi.log(t_FAILED, "(TestSuiteXMLPlayer:initConfig)",
                             "Unknown scenario type='%s' Must be 'uniset' or 'modbus'" % c_type, "", True)
                raise TestSuiteException(
                    "(TestSuiteXMLPlayer:initConfig): Unknown scenario type='%s' Must be 'uniset' or 'modbus'" % c_type)

            # print "add_config: " + str(node)
            node = xml.nextNode(node)

    def initTestList(self, xml):
        xml.begnode = xml.findNode(xml.getDoc(), "TestList")[0]
        if xml.begnode is not None:
            trunc = to_int(self.replace(xml.begnode.prop("logfile_trunc")))
            self.tsi.set_logfile(self.replace(xml.begnode.prop("logfile")), trunc)

            if xml.begnode.prop("notimestamp") != None:
                self.tsi.set_notimestamp(to_int(self.replace(xml.begnode.prop("notimestamp"))))

            if hasattr(xml, 'global_replace_list') == False:
                # WARNING!! Модифицируем класс, добавляем своё поле (не красиво наверно, но сам язык позволяет)
                xml.global_replace_list = None

            xml.global_replace_list = get_replace_list(to_str(xml.begnode.prop("replace")))
            self.global_conf = self.replace(xml.begnode.prop("config"))
            # WARNING!! Модифицируем класс, добавляем своё поле (не красиво наверно, но сам язык позволяет)
            xml.begnode = xml.begnode.children
            self.begin_tests(xml)
        else:
            self.tsi.log(t_FAILED, "(TestSuiteXMLPlayer)", "Can`t find begin node <TestList>", "", True)

    def initProcessMonitor(self, xml):

        if xml.getFileName() in self.pmonitor:
            return

        rlist = xml.findNode(xml.getDoc(), "RunList")[0]
        if rlist is not None:
            t_mp = ProcessMonitor()
            mp = copy.deepcopy(t_mp)
            mp.after_run_pause = to_int(rlist.prop("after_run_pause")) / 1000.0
            node = xml.firstNode(rlist.children)
            # print "load RUNLIST from " + str(xml.getFileName())
            while node is not None:
                #                 print "ADD TO RUNLIST %s"%str(node)
                c = ChildProcess(node)
                mp.addChild(c)
                node = xml.nextNode(node)

            # print "ADD list: %s"%(str(mp.plist))
            self.pmonitor[xml.getFileName()] = mp

        else:
            self.pmonitor[xml.getFileName()] = self.null_pm

    def get_pmonitor(self, xml):

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

    def set_ignore_runlist(self, xml, ignore_flag):
        self.ignore_rlist[xml.getFileName()] = ignore_flag

    def add_to_global_replace(self, lst):

        if lst is None or len(lst) == 0:
            return

        self.replace_stack.append(lst)

    def del_from_global_replace(self, lst):

        if lst is None or len(lst) == 0:
            return

        try:
            self.replace_stack.remove(lst)
        except ValueError:
            pass

    def add_to_test_replace(self, lst):

        if lst == None or len(lst) == 0:
            return

        self.replace_stack.append(lst)

    def del_from_test_replace(self, lst):

        if lst is None or len(lst) == 0:
            return

        try:
            self.replace_stack.remove(lst)
        except ValueError:
            pass

    def add_to_replace(self, lst):

        if lst is None or len(lst) == 0:
            return

        self.replace_stack.append(lst)

    def del_from_replace(self, lst):

        if lst is None or len(lst) == 0:
            return

        try:
            self.replace_stack.remove(lst)
        except ValueError:
            pass

    def str_to_idlist(self, str_val, ui):
        lst = get_str_list(str_val)
        lst = self.replace_list(lst)
        str1 = list_to_str(lst)
        return get_int_list(str1)

    def str_to_strlist(self, str_val, ui):
        lst = get_str_list(str_val)
        lst = self.replace_list(lst)
        str1 = list_to_str(lst)
        return get_str_list(str1)

    def replace_list(self, slist):
        res = []
        for v in slist:
            if v is None or len(v) < 1 or v[0] == v[1]:
                continue

            res.append([self.replace(v[0]), self.replace(v[1])])

        return res

    def replace(self, name):
        ''' преобразование, если есть в словаре замена.. '''
        if name is None or name == "" or name.__class__.__name__ == "int":
            return name

        if len(self.replace_stack) == 0:
            return name

        for v in reversed(self.replace_stack):
            if v is None or len(v) == 0:
                continue

            name = self.replace_in(name, v)

        return name

    def replace_in(self, name, r_dict):
        try:
            for k, v in r_dict:
                name = name.replace(k, v)

            return name

        except KeyError, ValueError:
            pass

        return None

    def get_current_ui(self, alias):
        ui = self.tsi.get_ui(alias)
        if ui is not None:
            return ui

        ui = self.tsi.get_ui(self.test_conf)
        if ui is not None:
            return ui

        ui = self.tsi.get_ui(self.global_conf)
        if ui is not None:
            return ui

        return self.tsi.get_default_ui()

    def get_outlink_filename(self, node):
        r_list = get_replace_list(to_str(node.prop("replace")))
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
        if t_field is None or t_field == "":
            t_field = "name"
            t_name = l[0]
        elif len(l) > 1:
            t_name = l[1]

        return (t_name, t_field)

    def getValue(self, node, xml):
        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        return self.tsi.getValue(self.replace(node.prop("id")), ui)

    def compare_item(self, node, xml):

        tname = self.replace(node.prop('test'))
        t_comment = self.replace(node.prop('comment'))

        if tname is None:
            self.tsi.log(t_FAILED, "<check..>", "FAILED: BAD STRUCTUTE! NOT FOUND test=''..", "", True)
            return t_FAILED

        t_ignore = to_int(self.replace(node.prop('ignore')))
        if t_ignore:
            self.tsi.log(t_IGNORE, 'IGNORE', "%s" % str(node), t_comment, False)
            return t_IGNORE

        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        if ui is None:
            self.tsi.log(t_FAILED, tname, "FAILED: Unknown CONFIG..", t_comment, True)
            return t_FAILED

        s_id = []

        test = tname.upper()
        clist = self.tsi.rcompare.findall(tname)
        if len(clist) == 0:
            self.tsi.log(t_FAILED, "?????", "FAILED: Unknown test='%s'.." % tname, "", True)
            return t_FAILED

        if len(clist) == 1:
            test = clist[0][1].upper()
            s_id.append(self.replace(clist[0][0]))
            s_id.append(self.replace(clist[0][2]))
        elif len(clist) > 1:
            test = 'MULTICHECK'

        t_out = to_int(self.replace(node.prop("timeout")))
        if t_out <= 0:
            t_out = self.default_timeout

        t_check = to_int(self.replace(node.prop("check_pause")))
        if t_check <= 0:
            t_check = self.default_check_pause

        t_hold = to_int(self.replace(node.prop("holdtime")))
        if test == "=":
            if t_hold > 0:
                return (t_PASSED if self.tsi.holdEqual(s_id, None, t_hold, t_check, t_comment, ui) else t_FAILED)
            else:
                return (t_PASSED if self.tsi.isEqual(s_id, None, t_out, t_check, t_comment, ui) else t_FAILED)

        if test == "!=":
            if t_hold > 0:
                return (t_PASSED if self.tsi.holdNotEqual(s_id, None, t_hold, t_check, t_comment, ui) else t_FAILED)
            else:
                return (t_PASSED if self.tsi.isNotEqual(s_id, None, t_out, t_check, t_comment, ui) else t_FAILED)

        if test == ">=" or test == ">":
            if t_hold > 0:
                return (t_PASSED if self.tsi.holdGreat(s_id, None, t_hold, t_check, t_comment, ui, test) else t_FAILED)
            else:
                return (t_PASSED if self.tsi.isGreat(s_id, None, t_out, t_check, t_comment, ui, test) else t_FAILED)

        if test == "<=" or test == "<":
            if t_hold > 0:
                return (t_PASSED if self.tsi.holdLess(s_id, None, t_hold, t_check, t_comment, ui, test) else t_FAILED)
            else:
                return (t_PASSED if self.tsi.isLess(s_id, None, t_out, t_check, t_comment, ui, test) else t_FAILED)

        if test == "MULTICHECK":
            self.tsi.log(" ", "MULTICHECK", "...", False)
            s_set = to_str(self.replace(node.prop("test")))
            if s_set == "":
                self.tsi.log(t_FAILED, "(TestSuiteXMLPlayer)", "MULTICHECK: undefined ID list (id='...')", t_comment,
                             True)
                return t_FAILED

            # для реализации механизма шаблонов
            # сперва разбиваем список на эелементы, подменяем каждый из них
            # собираем обратно, и уже разбираем как полагается (с разбивкой на id и val)
            slist = self.str_to_strlist(s_set, ui)
            res = True
            for s in slist:
                s_id.append(self.replace(s[0]))
                s_id.append(self.replace(s[1]))
                if t_hold > 0:
                    res = self.tsi.holdEqual(s_id, None, t_hold, t_check, t_comment, ui)
                else:
                    res = self.tsi.isEqual(s_id, None, t_out, t_check, t_comment, ui)
            return (t_PASSED if res else t_FAILED)

        self.tsi.log(t_FAILED, "TestSuiteXMLPlayer", "(compare_item): Unknown item type='%s'" % str(node), t_comment,
                     True)
        return t_FAILED

    def check_item(self, node, xml):

        tname = self.replace(node.prop('test'))
        t_comment = self.replace(node.prop('comment'))

        if tname is None:
            self.tsi.log(t_FAILED, "<check..>", "FAILED: BAD STRUCTUTE! NOT FOUND test=''..", "", True)
            return t_FAILED

        t_ignore = to_int(self.replace(node.prop('ignore')))
        if t_ignore:
            self.tsi.log(t_IGNORE, 'IGNORE', "%s" % str(node), t_comment, False)
            return t_IGNORE

        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        if ui is None:
            self.tsi.log(t_FAILED, tname, "FAILED: Unknown CONFIG..", t_comment, True)
            return t_FAILED

        s_id = None
        s_val = None

        test = tname.upper()

        if test != 'LINK' and test != 'OUTLINK':
            clist = self.tsi.rcheck.findall(tname)
            if len(clist) == 0:
                self.tsi.log(t_FAILED, "?????", "FAILED: Unknown test='%s'.." % tname, "", True)
                return t_FAILED

            if len(clist) == 1:
                test = clist[0][1].upper()
                s_id = self.replace(clist[0][0])
                s_val = to_int(self.replace(clist[0][2]))
            elif len(clist) > 1:
                test = 'MULTICHECK'

        t_out = to_int(self.replace(node.prop("timeout")))
        if t_out <= 0:
            t_out = self.default_timeout

        t_check = to_int(self.replace(node.prop("check_pause")))
        if t_check <= 0:
            t_check = self.default_check_pause

        t_hold = to_int(self.replace(node.prop("holdtime")))

        if test == "=":
            if t_hold > 0:
                return (t_PASSED if self.tsi.holdEqual(s_id, s_val, t_hold, t_check, t_comment, ui) else t_FAILED)
            else:
                return (t_PASSED if self.tsi.isEqual(s_id, s_val, t_out, t_check, t_comment, ui) else t_FAILED)

        if test == "!=":
            if t_hold > 0:
                return (t_PASSED if self.tsi.holdNotEqual(s_id, s_val, t_hold, t_check, t_comment, ui) else t_FAILED)
            else:
                return (t_PASSED if self.tsi.isNotEqual(s_id, s_val, t_out, t_check, t_comment, ui) else t_FAILED)

        if test == ">=" or test == ">":
            if t_hold > 0:
                return (t_PASSED if self.tsi.holdGreat(s_id, s_val, t_hold, t_check, t_comment, ui, test) else t_FAILED)
            else:
                return (t_PASSED if self.tsi.isGreat(s_id, s_val, t_out, t_check, t_comment, ui, test) else t_FAILED)

        if test == "<=" or test == "<":
            if t_hold > 0:
                return (t_PASSED if self.tsi.holdLess(s_id, s_val, t_hold, t_check, t_comment, ui, test) else t_FAILED)
            else:
                return (t_PASSED if self.tsi.isLess(s_id, s_val, t_out, t_check, t_comment, ui, test) else t_FAILED)

        if test == "MULTICHECK":
            self.tsi.log(" ", "MULTICHECK", "...", False)
            s_set = to_str(self.replace(node.prop("test")))
            if s_set == "":
                self.tsi.log(t_FAILED, "(TestSuiteXMLPlayer)", "MULTICHECK: undefined ID list (id='...')", t_comment,
                             True)
                return t_FAILED

            # для реализации механизма шаблонов
            # сперва разбиваем список на эелементы, подменяем каждый из них
            # собираем обратно, и уже разбираем как полагается (с разбивкой на id и val)
            slist = self.str_to_idlist(s_set, ui)
            res = True
            for s in slist:
                if t_hold > 0:
                    res = self.tsi.holdEqual(self.replace(s[0]), self.replace(s[1]), t_hold, t_check, t_comment, ui)
                else:
                    res = self.tsi.isEqual(self.replace(s[0]), self.replace(s[1]), t_out, t_check, t_comment, ui)
            return (t_PASSED if res else t_FAILED)

        if test == "LINK":
            t_name, t_field = self.get_link_param(node)

            r_list = get_replace_list(to_str(node.prop("replace")))
            r_list = self.replace_list(r_list)
            # self.add_to_replace(r_list)

            t_node = self.find_test(xml, t_name, t_field)

            if t_node is not None:
                logfile = self.tsi.get_logfile()
                self.tsi.log(" ", "LINK", "go to %s='%s'" % (t_field, t_name), t_comment, False)
                res = self.play_test(xml, t_node, logfile, r_list)
                self.del_from_replace(r_list)
                return res[0]

            # self.del_from_replace(r_list)
            self.tsi.log(t_FAILED, "LINK", "Not found test (%s='%s')" % (t_field, t_name), t_comment, True)
            return t_FAILED

        if test == "OUTLINK":

            t_file = self.get_outlink_filename(node)
            if t_file == "":
                self.tsi.log(t_FAILED, "OUTLINK", "Unknown file. Use file=''", t_comment, True)
                return t_FAILED

            t_link = to_str(self.replace(node.prop("link")))
            t_name, t_field = self.get_link_param(node)

            # replace должен действовать только после "получения" t_link
            r_list = get_replace_list(to_str(node.prop("replace")))
            r_list = self.replace_list(r_list)

            t_ignore_runlist = to_int(self.replace(node.prop("ignore_runlist")))
            t_xml = self.xmllist.get(t_file)
            t_dir = os.getcwd()
            t_prevdir = os.getcwd()
            if t_xml is None:
                # если в списке ещё нет, запоминаем..
                try:
                    t_xml = self.loadXML(t_file)
                    t_dir = os.path.dirname(os.path.realpath(t_file))
                except UException, e:
                    self.tsi.log(t_FAILED, "OUTLINK", "Can`t open file='%s'." % (t_file), t_comment, True)
                    return t_FAILED

            self.set_ignore_runlist(t_xml, t_ignore_runlist)

            try:
                self.call_level += 1
                os.chdir(t_dir)
                if t_link == "ALL":
                    self.tsi.log(" ", "OUTLINK", "go to file='%s' play ALL" % (t_file), t_comment, False)
                    self.tsi.nrecur += 1
                    res = self.play_xml(t_xml, r_list)
                    self.tsi.nrecur -= 1
                    self.call_level -= 1
                    # возвращаем обобщённый результат
                    # см. play_xml
                    return res[0]

                else:
                    t_node = self.find_test(t_xml, t_name, t_field)
                    if t_node is not None:
                        logfile = self.tsi.get_logfile()
                        self.tsi.log(" ", "OUTLINK", "go to file='%s' %s='%s'" % (t_file, t_field, t_name), t_comment,
                                     False)
                        self.tsi.nrecur += 1
                        # т.к. вызываем только один тест из всего xml, приходиться самостоятельно добавлять global_replace
                        self.add_to_global_replace(t_xml.global_replace_list)
                        res = self.play_test(t_xml, t_node, logfile, r_list)
                        self.tsi.nrecur -= 1
                        self.call_level -= 1
                        self.del_from_global_replace(t_xml.global_replace_list)
                        return res[0]
                    else:
                        self.del_from_replace(r_list)
                        self.tsi.log(t_FAILED, "OUTLINK",
                                     "Not found in file='%s' test (%s='%s')" % (t_file, t_field, t_name), t_comment,
                                     True)
                        return t_FAILED

            finally:
                os.chdir(t_prevdir)

        self.tsi.log(t_FAILED, "TestSuiteXMLPlayer", "(check_item): Unknown item type='%s'" % test, t_comment, True)
        return t_FAILED

    @staticmethod
    def check_thread_event(event):
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

    def del_reset_thread(self, t_name):

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
        while tout > 0:
            break_flag = True
            if self.check_thread_event(self.reset_thread_event):
                self.reset_thread_event.wait()
            self.reset_thread_event.clear()
            try:
                for t, t in self.reset_thread_dict.items():
                    if t.isAlive():
                        break_flag = False
                        self.tsi.actlog(" ", "WAIT", "waiting for finish reset value thread '%s'" % (t.getName()), "",
                                        False)
                        # t.join() # join - опасен тем, что можно застрять навечно..
            finally:
                self.reset_thread_event.set()

            if break_flag:
                return

            time.sleep(2)
            tout -= 2

    def get_item_config(self, node):
        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        return ui.getConfFileName()

    def get_config_name(self, node):
        return to_str(self.replace(node.prop("config")))

    def action_item(self, node):
        act = 'SET'

        t_comment = to_str(self.replace(node.prop("comment")))

        # act = self.replace(node.prop("name")).upper()
        if to_str(node.prop("msleep")) != '':
            act = 'MSLEEP'
        elif to_str(node.prop("script")) != '':
            act = 'SCRIPT'

        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        if ui is None:
            self.tsi.actlog(t_FAILED, act, "FAILED: Unknown CONFIG..", t_comment, True)
            return t_FAILED

        s_id = None
        s_val = None

        t_ignore = to_int(self.replace(node.prop('ignore')))
        if t_ignore:
            self.tsi.actlog(t_IGNORE, act, "%s" % str(node), t_comment, False)
            return t_IGNORE

        if act == 'SET':
            tname = to_str(self.replace(node.prop("set")))
            clist = self.tsi.rcheck.findall(tname)
            if len(clist) == 0:
                self.tsi.actlog(t_FAILED, tname, "FAILED: Unknown set='%s'.." % tname, t_comment, True)
                return t_FAILED

            if len(clist) == 1:
                s_id = self.replace(clist[0][0])
                s_val = to_int(self.replace(clist[0][2]))
            elif len(clist) > 1:
                act = 'MULTISET'

        if act == "SET":
            reset_msec = to_int(self.replace(node.prop("reset_time")))

            if reset_msec <= 0:
                return (t_PASSED if self.tsi.setValue(s_id, s_val, t_comment, ui) else t_FAILED)

            s_v2 = to_int(self.replace(node.prop("rval")))

            res = self.tsi.setValue(s_id, s_val, t_comment, ui)
            # self.tsi.actlog(" ", "RESET", "set reset time %d msec for id=%s" % (reset_msec, s_id), "", False)
            t = threading.Timer((reset_msec / 1000.), self.on_reset_timer, [s_id, s_v2, reset_msec, ui])
            self.add_reset_thread(t.getName(), t)
            t.start()
            return (t_PASSED if res == True else t_FAILED)

        if act == "MULTISET":
            self.tsi.actlog(" ", "MULTISET", "...", t_comment, False)
            # для реализации механизма шаблонов
            # сперва разбиваем список на эелементы, подменяем каждый из них
            # собираем обратно, и уже разбираем как полагается (с разбивкой на id и val)
            slist = self.str_to_idlist(to_str(self.replace(node.prop("set"))), ui)
            for s in slist:
                if self.tsi.setValue(self.replace(s[0]), self.replace(s[1]), t_comment,
                                     ui) == False and self.tsi.ignorefailed == False:
                    return t_FAILED
            return t_PASSED

        if act == "MSLEEP":
            self.tsi.msleep(to_int(self.replace(node.prop("msleep"))))
            return t_PASSED

        if act == "SCRIPT":
            silent = True

            if to_int(self.replace(node.prop('show_output'))):
                silent = False

            if self.tsi.runscript(to_str(self.replace(node.prop("script"))),
                                  silent) == False and self.tsi.ignorefailed == False:
                return t_FAILED
            return t_PASSED

        self.tsi.actlog(t_FAILED, '(TestSuiteXMLPlayer)', '(action_item): Unknown action command=\'%s\'' % act,
                        t_comment, True)
        return t_FAILED

    def on_reset_timer(self, s_id, s_val, s_msec, ui):
        self.tsi.actlog("", 'RESET', str('%10s: msec=%d id=%s val=%d' % ("on_reset_timer:", s_msec, s_id, s_val)), "",
                        False)
        try:
            self.tsi.setValue(s_id, s_val, "", ui)
        except TestSuiteException, e:
            self.tsi.actlog(t_FAILED, "RESET", "FAILED: %s" % e.getError, "", False)
        finally:
            if sys.version_info[1] == 5:
                self.del_reset_thread(threading.currentThread().getName())
            else:  # python 2.6
                self.del_reset_thread(threading.current_thread().getName())

        return False

    def begin(self, tnode):
        if tnode is not None:
            return tnode.children

        self.tsi.log(t_FAILED, "(TestSuiteXMLPlayer)", 'Can`t find children items for <test>', "", True)
        return None

    def begin_tests(self, xml):
        testnode = xml.findNode(xml.begnode, "test")[0]
        if testnode is not None:
            testnode = xml.firstNode(testnode)
            firstnode = testnode.children
            return [testnode, firstnode]

        self.tsi.log(t_FAILED, '(TestSuiteXMLPlayer)', 'Can`t find begin node <test>', "", True)
        return [None, None]

    def print_result_report(self, results):

        if self.junit != "":
            self.print_result_report_junit(self.junit)

        if self.show_result_report == True:
            head = "\nRESULT REPORT: '%s'" % (self.filename)
            head2 = ""
            foot2 = ""
            for i in range(0, len(head)):
                head2 += '*'
                foot2 += "-"

            print "%s\n%s" % (head, head2)
            i = 1
            ttime = 0
            for r in results:
                td = datetime.timedelta(0, r[res.Time])
                print '%s. [%s] - %s /%s/' % (
                string.rjust(str(i), 3), self.tsi.colorize_result(r[res.Result]), r[res.Name], td)
                i = i + 1
                ttime = ttime + r[res.Time]

            td = datetime.timedelta(0, ttime)
            ts = str(td).split('.')[0]
            print foot2
            print 'Total time: %s\n' % self.tsi.elapsed_time_str()

    def print_result_report_junit(self, repfilename):
        try:

            beg = False
            t_stack = []
            testlist = []
            t_name = ""
            for l in self.tsi.log_list:
                i = self.tsi.re_log.findall(l)

                if len(i) == 0 or len(i[0]) < logid.Num:
                    print 'UNKNOWN LOG FORMAT: %s' % str(l)
                    continue

                r = i[0]
                if r[logid.TestType] == 'BEGIN':
                    beg = True
                    t_name = r[logid.Txt]
                    t_stack = []
                elif r[logid.TestType] == 'FINISH' and beg == True:
                    t_info = self.tsi.re_tinfo.findall(r[logid.Txt])
                    t_r = t_info[0]
                    t_sec = int(t_r[1]) * 60 * 60 + int(t_r[1]) * 60 + int(t_r[3])
                    t_time = "%d.%s" % (t_sec, t_r[4])

                    testlist.append([t_name, r[logid.Result], t_time, r[logid.Txt], t_stack, l])
                    beg = False
                    t_stack = []
                elif beg == True:
                    t_stack.append([r, l])

            repfile = open(repfilename, "w")
            repfile.writelines('<?xml version="1.0" encoding="UTF-8"?>\n')
            repfile.writelines('<testsuite name="%s" tests="%d">\n' % (self.filename, len(testlist)))

            tnum = 1
            for r in testlist:
                if r[1] == t_PASSED:
                    repfile.writelines('  <testcase name="%s" time="%s" id="%d"/>\n' % (r[0], r[2], tnum))
                else:
                    repfile.writelines('  <testcase name="%s" time="%s" id="%d">\n' % (r[0], r[2], tnum))
                    if r[1] == t_IGNORE:
                        repfile.writelines('    </skipped>\n')
                    elif r[1] != t_PASSED:
                        repfile.writelines('    <failure>%s</failure>\n' % (r[3]))
                        repfile.writelines('    <system-err>\n')
                        for l in r[4]:
                            if l[0][logid.Result] == 'FAILED':
                                repfile.writelines('%s\n' % str(l[1]))
                        repfile.writelines('    </system-err>\n')

                        repfile.writelines('    <system-out>\n')
                        for l in r[4]:
                            repfile.writelines('%s\n' % str(l[1]))
                        repfile.writelines('    </system-out>\n')

                    repfile.writelines('  </testcase>\n')

                tnum += 1

            repfile.writelines('</testsuite>\n')
            repfile.close()
        except IOError:
            pass

    def fini_success(self):
        self.run_fini_scripts("Success")

    def fini_failure(self):
        self.run_fini_scripts("Failure")

    def run_fini_scripts(self, section):

        snode = self.xml.findNode(self.xml.getDoc(), section)[0]
        if snode is None:
            return

        node = self.xml.firstNode(snode.children)
        while node is not None:
            try:
                # cp = ChildProcess(node)
                # cp.run(True)
                self.tsi.runscript(node.prop("script"))
            except (OSError, KeyboardInterrupt), e:
                # print 'run \'%s\' failed.(cmd=\'%s\' error: (%d)%s).' % (cp.name, cp.cmd, e.errno, e.strerror)
                pass

            node = self.xml.nextNode(node)

    def play_all(self, xml=None):
        if xml is None:
            xml = self.xml

        logfile = self.tsi.get_logfile()
        b = self.begin_tests(xml)
        testnode = b[0]
        results = []
        tm_start = 0

        pmonitor = self.get_pmonitor(xml)
        resOK = False
        try:
            pmonitor.start()
            while testnode is not None:
                tm_start = time.time()
                results.append(self.play_test(xml, testnode, logfile))
                testnode = xml.nextNode(testnode)

            resOK = True
        except TestSuiteException, e:
            ttime = e.getFinishTime - tm_start
            results.append(
                [t_FAILED, to_str(self.replace(testnode.prop('name'))), ttime, e.getError, xml.getFileName()])
            resOK = False
            raise e

        finally:
            if resOK == True:
                self.fini_success()
            else:
                self.fini_failure()

            self.print_result_report(results)
            pmonitor.stop()

        return resOK

    def play_xml(self, xml, spec_replace_list=[]):

        logfile = self.tsi.get_logfile()
        b = self.begin_tests(xml)
        testnode = b[0]
        results = []
        tm_start = 0
        tm_all_start = time.time()
        pmonitor = self.get_pmonitor(xml)
        self.add_to_global_replace(xml.global_replace_list)
        self.add_to_test_replace(spec_replace_list)

        try:
            pmonitor.start()
            while testnode is not None:
                tm_start = time.time()
                results.append(self.play_test(xml, testnode, logfile))
                testnode = xml.nextNode(testnode)

        except TestSuiteException, e:
            tname = to_str(self.replace(testnode.prop('name')))
            ttime = e.getFinishTime - tm_start
            results.append([t_FAILED, tname, ttime, e.getError, testnode, xml.getFileName()])
            r = self.get_cumulative_result(results)
            raise e

        finally:
            pmonitor.stop()

        self.del_from_test_replace(spec_replace_list)
        self.del_from_global_replace(xml.global_replace_list)
        r = self.get_cumulative_result(results)
        ttime = time.time() - tm_all_start
        return [r[res.Result], results, ttime, r[res.Error], None]

    @staticmethod
    def find_test(xml, tname, propname='name'):
        if xml.begnode is not None:
            tnode = xml.begnode
            while tnode is not None:
                if to_str(tnode.prop(propname)).strip() == tname:
                    return tnode
                tnode = xml.nextNode(tnode)

        return None

    def play_by_name(self, xml, tlist):

        logfile = self.tsi.get_logfile()
        b = self.begin_tests(xml)
        testnode = b[0]
        results = []

        # Сперва проверим что все тесты существуют..
        for tprop,tname in tlist:
            tnode = self.find_test(xml, tname, tprop)
            if tnode is None:
                self.tsi.log(t_FAILED, '(TestSuiteXMLPlayer)', 'Can`t find test %s=\'%s\'' % (tprop,tname), "", True)
                return

        pmonitor = self.get_pmonitor(xml)
        resOK = False
        try:
            pmonitor.start()
            for tprop,tname in tlist:
                tm_start = time.time()
                tnode = self.find_test(xml, tname, tprop)
                results.append(self.play_test(xml, tnode, logfile))

            pmonitor.stop()
            resOK = True
        except TestSuiteException, ex:
            ttime = ex.getFinishTime - tm_start
            results.append(
                [t_FAILED, to_str(self.replace(testnode.prop('name'))), ttime, ex.getError, xml.getFileName()])
            raise ex

        finally:
            if resOK == True:
                self.fini_success()
            else:
                self.fini_failure()

            self.print_result_report(results)
            pmonitor.stop()

        return resOK

    def play_item(self, inode, xml):
        self.check_keyboard_interrupt()
        if inode.name == "action":
            return self.action_item(inode)
        elif inode.name == "check":
            return self.check_item(inode, xml)
        elif inode.name == "compare":
            return self.compare_item(inode, xml)

        return t_UNKNOWN

    def play_test(self, xml, testnode, logfile, spec_replace_list=[]):

        self.add_to_test_replace(spec_replace_list)

        t_name = to_str(self.replace(testnode.prop('name')))
        t_comment = to_str(self.replace(testnode.prop('comment')))

        self.call_stack.append(StackItem(t_name, self.call_level, xml.getFileName(), t_comment))
        # сохраняем ссылку на свой тест и предыдущий
        lastStackItem = self.call_stack[-1]
        prevStackItem = None
        if len(self.call_stack) > 1:
            prevStackItem= self.call_stack[-2]

        t_ignore = to_int(self.replace(testnode.prop('ignore')))
        if t_ignore:
            self.tsi.log(t_IGNORE, t_IGNORE, "'%s'" % t_name, t_comment, False)
            ret = [t_IGNORE, t_name, 0, "", xml.getFileName()]
            self.del_from_test_replace(spec_replace_list)
            # сохраняем ещё ссылку на предыдущий элемент
            lastStackItem.t_result = t_IGNORE
            lastStackItem.t_prev = prevStackItem
            return ret

        curnode = self.begin(testnode)

        mylog = to_str(self.replace(testnode.prop('logfile')))
        mylog_trunc = to_int(self.replace(testnode.prop('logfile_trunc')))
        if mylog != "":
            self.tsi.set_logfile(mylog, mylog_trunc)
        elif self.tsi.get_logfile() != logfile:
            self.tsi.set_logfile(logfile)

        r_list = get_replace_list(to_str(self.replace(testnode.prop('replace'))))
        r_list = self.replace_list(r_list)
        self.add_to_test_replace(r_list)

        self.tsi.set_ignorefailed(to_int(self.replace(testnode.prop('ignore_failed'))))
        self.test_conf = self.replace(testnode.prop('config'))

        # чисто визуальное отделение нового теста
        #        if self.tsi.printlog == True and self.tsi.nrecur<=0:
        #           print "---------------------------------------------------------------------------------------------------------------------"

        self.tsi.ntab = False
        self.tsi.log("", 'BEGIN', "'%s'" % t_name, t_comment, False)
        i_res = []
        tm_start = time.time()
        tm_finish = tm_start
        try:
            while curnode is not None:
                self.tsi.ntab = True
                ret = self.play_item(curnode, xml)
                if ret != t_UNKNOWN:
                    i_res.append(ret)
                curnode = xml.nextNode(curnode)
        except TestSuiteException, e:
            i_res.append(t_FAILED)
            tm_finish = e.getFinishTime
            # ttime = tm_finish - tm_start
            raise e
        else:
            tm_finish = time.time()
        finally:
            self.wait_finish_reset_thread()
            self.del_from_test_replace(spec_replace_list)
            self.del_from_test_replace(r_list)
            self.test_conf = ""
            tres = self.get_cumulative_result(i_res)
            ttime = tm_finish - tm_start
            td = datetime.timedelta(0, ttime)
            self.tsi.ntab = False
            self.tsi.log(tres[res.Result], 'FINISH', "'%s' /%s/" % (t_name, td), "", False)

            lastStackItem.t_result = tres[res.Result]
            lastStackItem.t_prev = prevStackItem
            # чисто визуальное отделение нового теста
            if self.tsi.printlog == True and self.tsi.nrecur <= 0:
                print "---------------------------------------------------------------------------------------------------------------------"

        return [tres[res.Result], t_name, ttime, tres[res.Error], xml.getFileName()]

    def get_cumulative_result(self, results):
        i_res = 0
        f_res = 0
        p_res = 0
        w_res = 0
        u_res = 0
        l_err = ""
        c_res = ""
        t_res = 0
        for tres in results:
            if tres.__class__.__name__ == 'list':
                r = tres[res.Result]
            else:
                r = tres

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

            if tres.__class__.__name__ == 'list':
                l_err = tres[res.Error]  # просто фиксируем последнюю ошибку (пока-что)
                t_res += tres[res.Time]

        if w_res > 0:
            c_res = t_WARNING
        elif f_res > 0 and p_res == 0 and i_res == 0:
            c_res = t_FAILED
        elif p_res > 0 and f_res == 0 and i_res >= 0:
            c_res = t_PASSED
        elif i_res > 0 and p_res == 0 and f_res == 0:
            c_res = t_IGNORE
        else:
            c_res = t_WARNING

        # print "cumulative: RES=%s (f_res=%d p_res=%d i_res=%d w_res=%d unknown=%d) for %s"%(c_res,f_res,p_res,i_res,w_res,u_res,str(results))
        return [c_res, "", t_res, l_err, ""]

    def on_key_press(self, c):
        # k = ord(c)
        if c == keys.pause:
            print '** PAUSE *** [..press again for continue..]\n'
            while True:

                try:
                    if sys.stdin.read(1) == keys.pause:
                        break
                except:
                    pass

                time.sleep(0.5)

    @staticmethod
    def get_tests_list(tname):
        '''
        :param tname: строка в виде prop=test1,prop2=test2,...
        :return: список пар [prop,testname]
        '''

        retlist = list()

        tlist = tname.strip().split(',')
        if len(tlist) == 0:
            return retlist

        for t in tlist:
            p = t.strip().split('=')
            if len(p) > 1:
                retlist.append(p)
            else:
                retlist.append(["name",p[0]])

        return retlist

if __name__ == "__main__":

    #    import os
    #    import termios

    #    old_settings = termios.tcgetattr(sys.stdin)

    ts = TestSuiteInterface()
    global_player = None
    print_calltrace = False
    global_result = None
    try:

        if ts.checkArgParam('--help', False) == True or ts.checkArgParam('-h', False) == True:
            print 'Usage: %s [--confile [configure.xml|alias@conf1.xml,alias2@conf2.xml,..]  --testfile scenario.xml' % \
                  sys.argv[0]
            print '\n'
            print '--confile [conf.xml,alias1@conf.xml,..]  - Configuration file.'
            print '--testfile tests.xml      - Test scenarion file.'
            print '--show-test-log           - Show test log'
            print '--show-action-log         - Show actions log'
            print '--show-result-report      - Show result report '
            print '--show-result-only        - Show only result report (ignore --show-action-log, --show-test-log)'
            print ''
            print '--show-commets            - Display all comments (test,check,action)'
            print '--show-numline            - Display line numbers'
            print '--show-timestamp          - Display the time'
            print '--show-test-comment       - Display test comment'
            print '--show-test-type          - Display the test type'
            print '--hide-time               - Hide elasped time'
            print ''
            print '--col-comment-width val   - Width for column "comment"'
            print ''
            print '--test-name test1,prop2=test2,prop3=test3,...- Run tests from list. By default prop=name'
            print '--ignore-run-list         - Ignore <RunList>'
            print '--ignore-nodes            - Do not use \'@node\''
            print '--default-timeout msec        - Default <check timeout=\'..\' ../>.\''
            print '--default-check-pause msec    - Default <check check_pause=\'..\' ../>.\''
            print '--junit filename          - Save report file. JUnit format.'
            print '--no-coloring-output      - Disable colorization output'
            print '--print-calltrace         - Display test call trace with test file name. If test-suite FAILED.'
            print '--print-calltrace-limit N - How many recent calls to print. Default: 20.'
            exit(0)

        testfile = ts.getArgParam('--testfile', "")
        if testfile == "":
            print '(TestSuiteXMLPlayer): Unknown testfile. Use --testfile\n'
            exit(1)

        conflist = ts.getArgParam('--confile', "")
        show_log = ts.checkArgParam('--show-test-log', False)
        show_actlog = ts.checkArgParam('--show-action-log', False)
        show_result = ts.checkArgParam('--show-result-report', False)
        show_comments = ts.checkArgParam('--show-comments', False)
        show_numstr = ts.checkArgParam('--show-numline', False)
        hide_time = ts.checkArgParam('--hide-time', False)
        show_test_type = ts.checkArgParam('--show-test-type', False)
        show_test_comment = ts.checkArgParam('--show-test-comment', False)
        show_result_only = ts.checkArgParam('--show-result-only', False)
        if show_result_only == True:
            show_actlog = False
            show_log = False

        testname = ts.getArgParam("--test-name", "")

        ignore_runlist = ts.checkArgParam("--ignore-run-list", False)
        showtimestamp = ts.checkArgParam("--show-timestamp", False)
        ignore_nodes = ts.checkArgParam("--ignore-nodes", False)
        tout = ts.getArgInt("--default-timeout", 5000)
        check_pause = ts.getArgInt("--default-check-pause", 500)
        col_comment_width = ts.getArgInt("--col-comment-width", 50)
        junit = ts.getArgParam("--junit", "")
        coloring_out = ts.checkArgParam('--no-coloring-output', False)
        print_calltrace = ts.checkArgParam('--print-calltrace', False)
        print_calltrace_limit = ts.getArgInt('--print-calltrace-limit', 20)

        cf = conflist.split(',')
        ts.init_testsuite(cf, show_log, show_actlog)
        ts.set_notimestamp(showtimestamp == False)
        ts.set_ignore_nodes(ignore_nodes)
        ts.set_show_comments(show_comments)
        ts.set_show_numline(show_numstr)
        ts.set_hide_time(hide_time)
        ts.set_show_test_type(show_test_type)
        ts.set_col_comment_width(col_comment_width)
        ts.set_show_test_comment(show_test_comment)
        ts.no_coloring_output = coloring_out

        player = TestSuiteXMLPlayer(ts, testfile, ignore_runlist)
        player.show_result_report = show_result
        player.default_timeout = tout
        player.default_check_pause = check_pause
        player.junit = junit

        testlist = player.get_tests_list(testname)

        global_player = player

        #       poller = select.poll()
        #       poller.register(sys.stdin, select.POLLIN)
        #       tty.setcbreak(sys.stdin)
        #       fcntl.fcntl(sys.stdin.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

        #       def check_key_press():
        #           global player
        #           try:
        #               events = poller.poll(30)
        #               if events:
        #                  for c in sys.stdin.read(1):
        #                      player.on_key_press(c)
        #           except:
        #               pass

        #       player.set_keyboard_interrupt( check_key_press )
        if len(testlist) > 0:
            global_result = player.play_by_name(player.xml, testlist)
        else:
            global_result = player.play_all()

        # if print_calltrace:
        #     player.print_calltrace()

        exit(0)

    except TestSuiteException, e:
        print "(TestSuiteXMLPlayer): catch exception: " + str(e.getError)
    except UException, e:
        print "(TestSuiteXMLPlayer): catch exception: " + str(e.getError())
    except KeyboardInterrupt:
        print "(TestSuiteXMLPlayer): catch keyboard interrupt.. "

    finally:
        #         sys.stdin = sys.__stdin__
        if global_player is not None and print_calltrace and global_result != True:
            global_player.print_calltrace(print_calltrace_limit)
    # if sys.stdin.closed == False:
    #       termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    exit(1)
