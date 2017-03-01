#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import copy
import string

from ProcessMonitor import *
from uniset2.pyUExceptions import UException
from uniset2.UniXML import *

import TestSuitePlayer
from TestSuiteInterface import *
from TestSuiteConsoleReporter import *
from TestSuiteLogFileReporter import *
from TestSuiteJUnitReporter import *
from TestSuiteGlobal import *

class keys():
    pause = ' '  # break
    step = 's'  # on 'step by step' mode


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

        # дерево тестов
        self.results = []
        self.call_stack = list()

        # текущий уровень вложенности
        self.call_level = 0

        # загружаем основной файл
        self.global_ignore_runlist = ignore_runlist
        # словарь флагов игнорирование запуска <RunList>
        self.ignore_rlist = dict()
        # специальный Null process monitor
        self.null_pm = ProcessMonitor([])

        self.xml = self.load_xml(xmlfile)
        self.filename = xmlfile

        # воспользуемся свойством питон и добавим к классу нужное нам поле
        self.xml.begnode = None
        self.xml.global_replace_list = None
        self.test_conf = ""

        self.show_result_report = False
        self.init_config(self.xml)
        self.init_testList(self.xml)
        self.add_to_global_replace(self.xml.global_replace_list)
        self.initProcessMonitor(self.xml)
        self.keyb_inttr_callback = None

        self.default_timeout = 5000
        self.default_check_pause = 300

        # список разрешающих запуск теста тегов
        self.tags = list()

        # список отключённых для проверки тегов
        self.disable_tags = list()

        # def __del__(self):
        # os.chdir(self.rootworkdir)

    def add_result(self, res):
        pass

    def set_keyboard_interrupt(self, callback):
        self.keyb_inttr_callback = callback

    def check_keyboard_interrupt(self):
        if self.keyb_inttr_callback != None:
            self.keyb_inttr_callback()

    def show_call_trace(self, call_limits):
        self.tsi.print_call_trace(self.call_stack, call_limits)

    @staticmethod
    def get_begin_test_node(xml):
        return xml.begnode

    def set_supplier_name(self, supName):
        ui = self.tsi.get_default_ui()
        supID = ui.getObjectID(supName)
        if supID == DefaultID:
            raise SystemError("Not found Object ID for '%s'" % supName)
        self.tsi.set_supplier_id(supID)

    def get_xml(self, fname):
        if fname in self.xmllist:
            return self.xmllist[fname]
        return None

    def load_xml(self, xmlfile):
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

            self.init_config(xml)
            self.init_testList(xml)
            self.initProcessMonitor(xml)
            return xml

        except IOError, ex:
            err = "IOError: %s" % str(ex)
            self.tsi.set_result(
                make_fail_result("FAILED load xmlfile '%s' err: '%s'" % (xmlfile, err), "(TestSuiteXMLPlayer:loadXML)"),
                False)
            raise TestSuiteException(err)
        except UniXMLException, ex:
            self.tsi.set_result(make_fail_result("FAILED load xmlfile '%s' err: '%s'" % (xmlfile, ex.getError()),
                                                "(TestSuiteXMLPlayer:loadXML)"), False)
            raise TestSuiteException(ex.getError())

    def init_config(self, xml):
        rnode = xml.findNode(xml.getDoc(), "TestList")[0]
        if rnode is None:
            self.tsi.set_result(make_fail_result("<TestList> not found?!", "(TestSuiteXMLPlayer)"), True)
            raise TestSuiteException("<TestList> not found?!")

        scenario_type = to_str(rnode.prop("type"))
        if scenario_type == "":
            scenario_type = "uniset"

        node = xml.findNode(xml.getDoc(), "Config")[0]
        if node is None:
            return

        self.init_environment_variables(xml, node)

        node = xml.findNode(node, "aliases")[0]
        if node is None:
            return

        node = xml.firstNode(node.children)
        while node is not None:

            c_type = to_str(node.prop("type"))
            if c_type == '':
                c_type = scenario_type

            if not self.tsi.is_iterface_exist(c_type):
                self.tsi.set_result(
                    make_fail_result("Unknown scenario type='%s' Must be '%s'" % (c_type, self.tsi.iterfaces_as_str()),
                                     "(TestSuiteXMLPlayer:initConfig)"), True)
                raise TestSuiteException(
                    "(TestSuiteXMLPlayer:initConfig): Unknown scenario type='%s' Must be 'uniset' or 'modbus' or 'snmp'" % c_type)

            ui = self.tsi.add_interface(node)
            node = xml.nextNode(node)

    def init_environment_variables(self, xml, confNode):

        node = xml.findNode(confNode, "environment")[0]
        if not node:
            return

        env = dict()

        node = xml.firstNode(node.children)
        while node is not None:
            env[to_str(node.prop("name"))] = to_str(node.prop("value"))
            node = xml.nextNode(node)

        self.tsi.set_user_envirion_variables(env)

    def init_testList(self, xml):
        xml.begnode = xml.findNode(xml.getDoc(), "TestList")[0]
        if xml.begnode is not None:
            trunc = to_int(self.replace(xml.begnode.prop("logfile_trunc")))
            logfile = self.replace(xml.begnode.prop("logfile"))
            # FIXME: Временно ведение лог файл отключено
            # if len(logfile)>0:
            #     logRepoter = TestSuiteLogFileReporter()
            #     logRepoter.set_logfile(logfile,trunc)
            #     self.tsi.add_repoter(logRepoter)

            if xml.begnode.prop("notimestamp") is not None:
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
            self.tsi.set_result(make_fail_result("Can`t find begin node <TestList> in %s" % xml.getFileName()), True)

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
                mp.add_child(c)
                node = xml.nextNode(node)

            # print "ADD list: %s"%(str(mp.plist))
            self.pmonitor[xml.getFileName()] = mp

        else:
            self.pmonitor[xml.getFileName()] = self.null_pm

    def get_pmonitor(self, xml):

        if self.global_ignore_runlist:
            return self.null_pm

        ignore_rlist = False
        try:
            ignore_rlist = self.ignore_rlist[xml.getFileName()]
        except (KeyError, ValueError):
            pass

        if ignore_rlist:
            return self.null_pm

        try:
            return self.pmonitor[xml.getFileName()]
        except (KeyError, ValueError):
            pass

        # чтобы везде в коде не проверять pm!=None
        # просто возвращаем null монитор, с пустым списком
        # соответственно он ничего запускатьне будет
        self.pmonitor[xml.getFileName()] = self.null_pm
        return self.null_pm

    def set_ignore_runlist(self, xml, ignore_flag):
        self.ignore_rlist[xml.getFileName()] = ignore_flag

    def set_tags(self, tags_str):

        if len(tags_str) == 0:
            return

        self.tags = self.get_tags(tags_str)

    def add_disable_tags(self, tags_str):

        if len(tags_str) == 0:
            return

        self.disable_tags.extend(self.get_tags(tags_str))

    def del_disable_tags(self, tags_str):

        if len(tags_str) == 0:
            return

        check_list = self.get_tags(tags_str)

        if len(check_list) == 0:
            return

        for t in check_list:
            if t in self.disable_tags:
                self.disable_tags.remove(t)

    def get_tags(self, tags_str):

        if len(tags_str) == 0:
            return list()

        taglist = tags_str.split('#')
        if len(taglist) == 1:
            return taglist

        return taglist[1:]

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

            #res.append([self.replace(v[0]), self.replace(v[1])])
            res.append([v[0], v[1]])

        return res

    def replace(self, name):
        """
        преобразование, если есть в словаре замена..
        :param name: строка которая заменяется если будет найдена
        :return: возвращется заменённая строка или таже самая
        """
        if name is None or name == "" or name.__class__.__name__ == "int":
            return name

        if len(self.replace_stack) == 0:
            return name

        for v in reversed(self.replace_stack):
            if v is None or len(v) == 0:
                continue

            name = self.replace_in(name, v)

        return name

    @staticmethod
    def replace_in(name, r_dict):
        try:
            for k, v in r_dict:
                name = name.replace(k, v)

            return name

        except KeyError:
            pass
        except ValueError:
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

        return t_name, t_field

    # пока функцию закоментировал, возможно она использовалась в GUI-плээре
    # def getValue(self, node, xml):
    #     cfig = self.get_config_name(node)
    #     ui = self.get_current_ui(cfig)
    #     return self.tsi.getValue(self.replace(node.prop("id")), ui)

    def compare_item(self, node, xml):

        self.tsi.add_testsuite_environ_variable('CONFILE', '')
        ret = make_default_item()

        tname = self.replace(node.prop('test'))
        t_comment = self.replace(node.prop('comment'))

        ret['name'] = tname
        ret['comment'] = t_comment
        ret['item_type'] = 'check'
        ret['nrecur'] = self.tsi.nrecur

        if tname is None:
            self.tsi.set_result(make_fail_result("FAILED: BAD TEST STRUCTURE! NOT FOUND test=''.."), True)
            return ret

        t_ignore = to_int(self.replace(node.prop('ignore')))
        if t_ignore:
            ret['result'] = t_IGNORE
            ret['text'] = "%s" % str(node)
            ret['type'] = 'IGNORE'
            self.tsi.set_result(ret, False)
            return ret

        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        if ui is None:
            ret['result'] = t_FAILED
            ret['text'] = "FAILED: Unknown CONFIG.."
            ret['type'] = tname
            self.tsi.set_result(ret, True)
            return ret

        s_id = []
        self.tsi.add_testsuite_environ_variable('CONFILE', ui.get_conf_filename())

        test = tname.upper()
        clist = self.tsi.rcompare.findall(tname)
        if len(clist) == 0:
            ret['result'] = t_FAILED
            ret['text'] = "FAILED: Unknown test='%s'.." % tname
            self.tsi.set_result(ret, True)
            return ret

        if len(clist) == 1:
            test = clist[0][1].upper()
            s_id.append(clist[0][0])
            s_id.append(clist[0][2])
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
                self.tsi.holdEqual(s_id, None, t_hold, t_check, ret, ui)
            else:
                self.tsi.isEqual(s_id, None, t_out, t_check, ret, ui)
            return ret

        if test == "!=":
            if t_hold > 0:
                self.tsi.holdNotEqual(s_id, None, t_hold, t_check, ret, ui)
            else:
                self.tsi.isNotEqual(s_id, None, t_out, t_check, ret, ui)
            return ret

        if test == ">=" or test == ">":
            if t_hold > 0:
                self.tsi.holdGreat(s_id, None, t_hold, t_check, ret, ui, test)
            else:
                self.tsi.isGreat(s_id, None, t_out, t_check, ret, ui, test)
            return ret

        if test == "<=" or test == "<":
            if t_hold > 0:
                self.tsi.holdLess(s_id, None, t_hold, t_check, ret, ui, test)
            else:
                self.tsi.isLess(s_id, None, t_out, t_check, ret, ui, test)
            return ret

        if test == "MULTICHECK":
            self.tsi.set_result(" ", "MULTICHECK", "...", False)
            s_set = to_str(self.replace(node.prop("test")))
            if s_set == "":
                ret['result'] = t_FAILED
                ret['text'] = "MULTICHECK: undefined ID list (id='...')"
                self.tsi.set_result(ret, True)
                return ret

            # для реализации механизма шаблонов
            # сперва разбиваем список на эелементы, подменяем каждый из них
            # собираем обратно, и уже разбираем как полагается (с разбивкой на id и val)
            slist = self.str_to_strlist(s_set, ui)
            for s in slist:
                s_id.append(self.replace(s[0]))
                s_id.append(self.replace(s[1]))
                if t_hold > 0:
                    self.tsi.holdEqual(s_id, None, t_hold, t_check, ret, ui)
                else:
                    self.tsi.isEqual(s_id, None, t_out, t_check, ret, ui)
                return ret

        ret['result'] = t_FAILED
        ret['text'] = "(compare_item): Unknown item type='%s'" % str(node)
        self.tsi.set_result(ret, True)
        return ret

    def check_item(self, node, xml):

        self.tsi.add_testsuite_environ_variable('CONFILE', '')
        result = make_default_item()
        tname = self.replace(node.prop('test'))
        t_comment = self.replace(node.prop('comment'))

        result['item_type'] = 'check'
        result['type'] = tname.upper()
        result['comment'] = t_comment
        result['xmlnode'] = node
        result['filename'] = xml.getFileName()
        result['nrecur'] = self.tsi.nrecur

        if tname is None:
            result['text'] = "FAILED: BAD TEST STRUCTURE! NOT FOUND test=''.."
            result['result'] = t_FAILED
            self.tsi.set_result(result, True)
            return result

        t_ignore = to_int(self.replace(node.prop('ignore')))
        if t_ignore:
            result['text'] = 'IGNORE', "%s" % str(node)
            result['result'] = t_IGNORE
            self.tsi.set_result(result, False)
            return result

        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        if ui is None:
            result['text'] = "FAILED: Unknown CONFIG.."
            result['result'] = t_FAILED
            self.tsi.set_result(result, True)
            return result

        self.tsi.add_testsuite_environ_variable('CONFILE', ui.get_conf_filename())
        s_id = None
        s_val = None

        test = tname.upper()

        if test != 'LINK' and test != 'OUTLINK':
            clist = self.tsi.rcheck.findall(tname)
            if len(clist) == 0:
                result['result'] = t_FAILED
                result['text'] = "FAILED: Unknown test='%s'.." % tname
                self.tsi.set_result(result, True)
                return result

            if len(clist) == 1:
                test = clist[0][1].upper()
                s_id = clist[0][0]
                s_val = to_int(clist[0][2])
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
                self.tsi.holdEqual(s_id, s_val, t_hold, t_check, result, ui)
            else:
                self.tsi.isEqual(s_id, s_val, t_out, t_check, result, ui)
            return result

        if test == "!=":
            if t_hold > 0:
                self.tsi.holdNotEqual(s_id, s_val, t_hold, t_check, result, ui)
            else:
                self.tsi.isNotEqual(s_id, s_val, t_out, t_check, result, ui)
            return result

        if test == ">=" or test == ">":
            if t_hold > 0:
                self.tsi.holdGreat(s_id, s_val, t_hold, t_check, result, ui, test)
            else:
                self.tsi.isGreat(s_id, s_val, t_out, t_check, result, ui, test)
            return result

        if test == "<=" or test == "<":
            if t_hold > 0:
                self.tsi.holdLess(s_id, s_val, t_hold, t_check, result, ui, test)
            else:
                self.tsi.isLess(s_id, s_val, t_out, t_check, result, ui, test)
            return result

        if test == "MULTICHECK":
            info = make_info_item("...", 'MULTICHECK', result)
            info['item_type'] = result['item_type']
            info['nrecur'] = self.tsi.nrecur
            self.tsi.set_result(info, False)
            s_set = to_str(self.replace(node.prop("test")))
            if s_set == "":
                result['text'] = "MULTICHECK: undefined ID list (id='...')"
                result['result'] = t_FAILED
                self.tsi.set_result(result, True)
                return result

            # для реализации механизма шаблонов
            # сперва разбиваем список на эелементы, подменяем каждый из них
            # собираем обратно, и уже разбираем как полагается (с разбивкой на id и val)
            slist = self.str_to_idlist(s_set, ui)
            for s in slist:
                if t_hold > 0:
                    self.tsi.holdEqual(self.replace(s[0]), self.replace(s[1]), t_hold, t_check, result, ui)
                else:
                    self.tsi.isEqual(self.replace(s[0]), self.replace(s[1]), t_out, t_check, result, ui)

            return result

        if test == "LINK":
            t_name, t_field = self.get_link_param(node)

            r_list = get_replace_list(to_str(node.prop("replace")))
            r_list = self.replace_list(r_list)
            # self.add_to_replace(r_list)

            t_node = self.find_test(xml, t_name, t_field)

            if t_node is not None:
                # FIXME: Временно ведение лог файл отключено
                # logfile = self.tsi.get_logfile()
                logfile = ""
                info = make_info_item("go to %s='%s'" % (t_field, t_name), 'LINK', result)
                info['comment'] = t_comment
                info['item_type'] = result['item_type']
                info['nrecur'] = self.tsi.nrecur
                self.tsi.set_result(info, False)
                res = self.play_test(xml, t_node, logfile, r_list)
                self.del_from_replace(r_list)
                return res

            result['result'] = t_FAILED
            result['text'] = "Not found test (%s='%s')" % (t_field, t_name)
            self.tsi.set_result(result, True)
            return result

        if test == "OUTLINK":

            t_file = self.get_outlink_filename(node)
            if t_file == "":
                result['result'] = t_FAILED
                result['text'] = "Unknown file. Use file=''"
                self.tsi.set_result(result, True)
                return result

            t_link = to_str(self.replace(node.prop("link")))
            t_name, t_field = self.get_link_param(node)

            # replace должен действовать только после "получения" t_link
            r_list = get_replace_list(to_str(node.prop("replace")))
            r_list = self.replace_list(r_list)

            t_ignore_runlist = to_int(self.replace(node.prop("ignore_runlist")))
            t_xml = self.xmllist.get(t_file)
            t_dir = os.getcwd()
            t_prevdir = t_dir

            if t_xml is None:
                # если в списке ещё нет, запоминаем..
                try:
                    t_xml = self.load_xml(t_file)
                except UException, ex:
                    result['result'] = t_FAILED
                    result['text'] = "Can`t open file='%s' ERR: %s." % (t_file, ex.getError())
                    self.tsi.set_result(result, True)
                    return result
                except TestSuiteException, ex:
                    result['result'] = t_FAILED
                    result['text'] = "Can`t open file='%s' ERR: %s" % (t_file, ex.getError())
                    self.tsi.set_result(result, True)
                    return result

            t_dir = os.path.dirname(os.path.realpath(t_file))
            self.set_ignore_runlist(t_xml, t_ignore_runlist)

            try:
                self.call_level += 1
                os.chdir(t_dir)
                if t_link == "ALL":
                    info = make_default_item()
                    info['text'] = "go to file='%s' play ALL" % t_file
                    info['comment'] = t_comment
                    info['type'] = 'OUTLINK'
                    info['nrecur'] = self.tsi.nrecur
                    info['item_type'] = result['item_type']
                    self.tsi.set_result(info, False)
                    self.tsi.nrecur += 1
                    res = self.play_xml(t_xml, r_list)
                    self.tsi.nrecur -= 1
                    self.call_level -= 1
                    return res

                else:
                    t_node = self.find_test(t_xml, t_name, t_field)
                    if t_node is not None:
                        # FIXME: Временно ведение лог файл отключено
                        # logfile = self.tsi.get_logfile()
                        logfile = ""

                        info = make_default_item()
                        info['text'] = "go to file='%s' %s='%s'" % (t_file, t_field, t_name)
                        info['comment'] = t_comment
                        info['type'] = 'OUTLINK'
                        info['nrecur'] = self.tsi.nrecur
                        info['item_type'] = result['item_type']
                        self.tsi.set_result(info, False)
                        self.tsi.nrecur += 1
                        # т.к. вызываем только один тест из всего xml, приходиться
                        # самостоятельно добавлять global_replace
                        self.add_to_global_replace(t_xml.global_replace_list)
                        res = self.play_test(t_xml, t_node, logfile, r_list)
                        self.tsi.nrecur -= 1
                        self.call_level -= 1
                        self.del_from_global_replace(t_xml.global_replace_list)
                        return res
                    else:
                        result['result'] = t_FAILED
                        result['text'] = "Not found in file='%s' test (%s='%s')" % (t_file, t_field, t_name)
                        self.del_from_replace(r_list)
                        self.tsi.set_result(result, True)
                        return result

            finally:
                os.chdir(t_prevdir)

        result['result'] = t_FAILED
        result['text'] = "(check_item): Unknown item type='%s'" % test
        self.tsi.set_result(result, True)
        return result

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
        except KeyError:
            pass
        except ValueError:
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
                        alog = make_default_item()
                        alog['comment'] = ''
                        alog['text'] = "waiting for finish reset value thread '%s'" % (t.getName())
                        alog['type'] = 'WAIT'
                        alog['nrecur'] = self.tsi.nrecur
                        self.tsi.set_action_result(alog, False)
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
        return ui.get_conf_filename()

    def get_config_name(self, node):
        return to_str(self.replace(node.prop("config")))

    def check_tag(self, tag):

        # если нет тегов, то значит все TRUE
        if len(self.tags) == 0:
            return True

        # Проверять надо по списку представляющему собой то, что есть в tags но нет в disable_tags
        check_list = [i for i in self.tags if i not in self.disable_tags]

        if len(check_list) == 0:
            return True

        taglist = tag.split('#')
        for t in taglist:
            if t in check_list:
                return True

        return False

    def first_tag(self, tag):
        """
        Поиск тега среди списка тегов
        :param tag: искомый тэг
        :return: возвращает первый тег который прошёл проверку
        """

        if len(self.tags) == 0:
            return ''

        taglist = tag.split('#')
        for t in taglist:
            if t in self.tags:
                return '#' + t

        return ''

    def action_item(self, node):
        """
        processing 'action'
        :param node: xmlnode of current item of test
        :return: result [t_XXXX]
        """

        self.tsi.add_testsuite_environ_variable('CONFILE', '')
        result = make_default_item()

        result['item_type'] = 'action'
        result['type'] = 'SET'
        result['comment'] = to_str(self.replace(node.prop("comment")))
        result['xmlnode'] = node
        result['name'] = to_str(self.replace(node.prop("name")))
        result['nrecur'] = self.tsi.nrecur

        # act = self.replace(node.prop("name")).upper()
        if to_str(node.prop("msleep")) != '':
            result['type'] = 'MSLEEP'
        elif to_str(node.prop("script")) != '':
            result['type'] = 'SCRIPT'

        cfig = self.get_config_name(node)
        ui = self.get_current_ui(cfig)
        if ui is None:
            result['text'] = 'FAILED: Unknown CONFIG..'
            result['result'] = t_FAILED
            self.tsi.set_action_result(result, True)
            return result

        self.tsi.add_testsuite_environ_variable('CONFILE', ui.get_conf_filename())

        s_id = None
        s_val = None

        t_ignore = to_int(self.replace(node.prop('ignore')))
        if t_ignore:
            result['text'] = '%s' % str(node)
            result['result'] = t_IGNORE
            self.tsi.set_action_result(result, False)
            return result

        if result['type'] == 'SET':
            tname = to_str(self.replace(node.prop("set")))
            clist = self.tsi.rcheck.findall(tname)
            if len(clist) == 0:
                result['text'] = "FAILED: Unknown set='%s'.." % tname
                result['result'] = t_FAILED
                self.tsi.set_action_result(result, True)
                return result

            if len(clist) == 1:
                s_id = self.replace(clist[0][0])
                s_val = to_int(self.replace(clist[0][2]))
            elif len(clist) > 1:
                result['type'] = 'MULTISET'

        if result['type'] == "SET":
            reset_msec = to_int(self.replace(node.prop("reset_time")))

            if reset_msec <= 0:
                self.tsi.set_value(s_id, s_val, result, ui)
                return result

            s_v2 = to_int(self.replace(node.prop("rval")))

            self.tsi.set_value(s_id, s_val, result, ui)

            if self.tsi.is_check_scenario_mode():
                return result

            t = threading.Timer((reset_msec / 1000.), self.on_reset_timer, [s_id, s_v2, reset_msec, ui])
            self.add_reset_thread(t.getName(), t)
            t.start()
            return result

        if result['type'] == "MULTISET":
            result['text'] = to_str(self.replace(node.prop("set")))  # '...'
            info = make_info_item(result['text'], 'MULTISET', result)
            info['item_type'] = result['item_type']
            self.tsi.set_result(info, False)

            # для реализации механизма шаблонов
            # сперва разбиваем список на эелементы, подменяем каждый из них
            # собираем обратно, и уже разбираем как полагается (с разбивкой на id и val)
            slist = self.str_to_idlist(to_str(self.replace(node.prop("set"))), ui)
            for s in slist:
                res = self.tsi.set_value(self.replace(s[0]), self.replace(s[1]), result, ui)
                if res == False and self.tsi.ignorefailed == False:
                    return result

            return result

        if result['type'] == "MSLEEP":
            self.tsi.msleep(to_int(self.replace(node.prop("msleep"))), result)
            return result

        if result['type'] == "SCRIPT":
            silent = True

            if to_int(self.replace(node.prop('show_output'))):
                silent = False

            script = to_str(self.replace(node.prop("script")))
            result['script'] = script
            self.tsi.runscript(script, result, silent, (self.tsi.ignorefailed == False))
            return result

        result['result'] = t_FAILED
        result['text'] = '(action_item): Unknown action command=\'%s\'' % result['type']
        result['type'] = 'UNKNOWN'
        self.tsi.set_action_result(result, True)
        return result

    def on_reset_timer(self, s_id, s_val, s_msec, ui):

        act = make_default_item()
        act['type'] = 'RESET'
        act['text'] = str('%10s: msec=%d id=%s val=%d' % ("on_reset_timer:", s_msec, s_id, s_val))
        act['nrecur'] = self.tsi.nrecur
        act['item_type'] = 'action'
        self.tsi.set_action_result(act, False)
        try:
            self.tsi.set_value(s_id, s_val, act, ui)
            act['result'] = t_PASSED
        except TestSuiteException, e:
            act['result'] = t_FAILED
            act['text'] = "FAILED: %s" % e.getError()
            self.tsi.set_action_result(act, False)
        finally:
            if sys.version_info[1] == 5:
                self.del_reset_thread(threading.currentThread().getName())
            else:  # python 2.6
                self.del_reset_thread(threading.current_thread().getName())

        return False

    def begin(self, tnode):
        if tnode is not None:
            return tnode.children

        fail = make_default_item()
        fail['text'] = 'Can`t find children items for <test>'
        fail['type'] = '(TestSuiteXMLPlayer)'
        fail['result'] = t_FAILED
        fail['nrecur'] = self.tsi.nrecur
        fail['item_type'] = 'test'
        self.tsi.set_result(fail, True)
        return None

    def begin_tests(self, xml):
        testnode = xml.findNode(xml.begnode, "test")[0]
        if testnode is not None:
            testnode = xml.firstNode(testnode)
            firstnode = testnode.children
            return [testnode, firstnode]

        fail = make_default_item()
        fail['text'] = "Can`t find begin node <test> in %s" % xml.getFileName()
        fail['type'] = '(TestSuiteXMLPlayer)'
        fail['result'] = t_FAILED
        fail['nrecur'] = self.tsi.nrecur
        fail['item_type'] = 'test'
        self.tsi.set_result(fail, True)
        return [None, None]

    def fini_success(self):
        self.run_fini_scripts("Success")

    def fini_failure(self):
        self.run_fini_scripts("Failure")

    def run_fini_scripts(self, section):

        snode = self.xml.findNode(self.xml.getDoc(), section)[0]
        if snode is None:
            # print "<%s> section not found in '%s'"%(section,self.xml.getFileName())
            return

        node = self.xml.firstNode(snode.children)

        result = make_default_item()
        result['nrecur'] = self.tsi.nrecur
        result['filename'] = self.xml.getFileName()

        if self.tsi.is_check_scenario_mode():
            inf = make_info_item("CHECK '%s' scripts" % section, result)
            self.tsi.set_result(inf, False)

        while node is not None:
            try:
                self.tsi.runscript(node.prop("script"), result, True, False)
            except (OSError, KeyboardInterrupt, Exception):
                pass

            node = self.xml.nextNode(node)

    def print_call_trace(self, call_limits):
        self.tsi.print_call_trace(self.results, call_limits)

    def play_all(self, xml=None):

        if xml is None:
            xml = self.xml
            self.tsi.add_testsuite_environ_variable('ROOTDIR', os.getcwd())
            self.tsi.add_testsuite_environ_variable('ROOT_FILENAME', xml.getFileName())

        # FIXME: Временно ведение лог файл отключено
        # logfile = self.tsi.get_logfile()
        logfile = ""
        b = self.begin_tests(xml)
        testnode = b[0]
        self.results = []
        tm_start = 0

        pmonitor = self.get_pmonitor(xml)
        res_ok = False
        try:
            if self.tsi.is_check_scenario_mode():
                pmonitor.check()
            else:
                pmonitor.start()

            if self.tsi.is_check_scenario_mode():
                info = make_info_item('CHECK CONF...', 'BEGIN')
                self.tsi.set_result(info, False)

                ok, err = self.tsi.validate_configuration()
                if not ok:
                    info['result'] = t_FAILED
                    info['text'] = err
                else:
                    info['result'] = t_PASSED
                    info['text'] = 'CHECK CONF'

                info['type'] = 'FINISH'
                self.tsi.set_result(info, False)

            self.tsi.start_tests()
            while testnode is not None:
                tm_start = time.time()
                res = self.play_test(xml, testnode, logfile)
                if res['result'] != t_NONE:
                    self.results.append(res)

                testnode = xml.nextNode(testnode)

            res_ok = True
        except TestSuiteException, ex:
            ttime = ex.getFinishTime() - tm_start
            res = make_default_item()
            res['xmlnode'] = testnode
            res['result'] = t_FAILED
            res['name'] = to_str(self.replace(testnode.prop('name')))
            res['time'] = ttime
            res['text'] = ex.getError()
            res['filename'] = xml.getFileName()
            res['nrecur'] = self.tsi.nrecur
            res['item_type'] = 'test'
            self.results.append(res)
            res_ok = False
            raise ex

        finally:
            if self.tsi.is_check_scenario_mode():
                self.fini_success()
                self.fini_failure()
            else:
                if res_ok == True:
                    self.fini_success()
                else:
                    self.fini_failure()

            self.tsi.finish_tests()
            self.tsi.print_result_report(self.results)
            if not self.tsi.is_check_scenario_mode():
                pmonitor.stop()

        return res_ok

    def play_xml(self, xml, spec_replace_list=list()):

        # FIXME: Временно ведение лог файл отключено
        # logfile = self.tsi.get_logfile()
        logfile = ""
        b = self.begin_tests(xml)
        testnode = b[0]
        tm_start = 0
        tm_all_start = time.time()
        pmonitor = self.get_pmonitor(xml)
        self.add_to_global_replace(xml.global_replace_list)
        self.add_to_test_replace(spec_replace_list)

        item = make_default_item()
        item['name'] = to_str(self.replace(testnode.prop('name')))
        item['nrecur'] = self.tsi.nrecur
        item['item_type'] = 'test'
        item['filename'] = xml.getFileName()

        try:
            if self.tsi.is_check_scenario_mode():
                pmonitor.check()
            else:
                pmonitor.start()

            while testnode is not None:
                tm_start = time.time()
                res = self.play_test(xml, testnode, logfile)
                if res['result'] != t_NONE:
                    item['items'].append(res)

                testnode = xml.nextNode(testnode)

        except (TestSuiteException, TestSuiteValidateError), ex:
            item['time'] = ex.getFinishTime() - tm_start
            item['text'] = ex.getError()
            item['xmlnode'] = testnode
            if ex.failed_item:
                item['items'].append(ex.failed_item)

            ret = self.get_cumulative_result(item['items'])
            item['result'] = ret['result']
            raise ex

        finally:
            if not self.tsi.is_check_scenario_mode():
                pmonitor.stop()

        self.del_from_test_replace(spec_replace_list)
        self.del_from_global_replace(xml.global_replace_list)
        ret = self.get_cumulative_result(item['items'])
        item['time'] = time.time() - tm_all_start
        item['result'] = ret['result']
        item['text'] = ret['text']
        item['xmlnode'] = None
        item['filename'] = xml.getFileName()
        return item

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

        # FIXME: Временно ведение лог файл отключено
        # logfile = self.tsi.get_logfile()
        logfile = ""
        b = self.begin_tests(xml)
        testnode = b[0]
        self.results = []

        # Сперва проверим что все тесты существуют..
        for tprop, tname in tlist:
            tnode = self.find_test(xml, tname, tprop)
            if tnode is None:
                fail = make_default_item()
                fail['text'] = 'Can`t find test %s=\'%s\'' % (tprop, tname)
                fail['type'] = '(TestSuiteXMLPlayer)'
                fail['result'] = t_FAILED
                fail['nrecur'] = self.tsi.nrecur
                fail['item_type'] = 'test'
                self.tsi.set_result(fail, True)
                return

        pmonitor = self.get_pmonitor(xml)
        res_ok = False
        tm_start = time.time()
        try:
            if self.tsi.is_check_scenario_mode():
                pmonitor.check()
            else:
                pmonitor.start()

            self.tsi.start_tests()
            for tprop, tname in tlist:
                tm_start = time.time()
                tnode = self.find_test(xml, tname, tprop)
                res = self.play_test(xml, tnode, logfile)
                if res['result'] != t_NONE:
                    self.results.append(res)

            res_ok = True
        except TestSuiteException, ex:
            item = make_default_item()
            item['name'] = to_str(self.replace(testnode.prop('name')))
            item['time'] = ex.getFinishTime() - tm_start
            item['result'] = t_FAILED
            item['text'] = ex.getError()
            item['xmlnode'] = testnode
            item['filename'] = xml.getFileName()
            item['nrecur'] = self.tsi.nrecur
            item['item_type'] = 'test'
            self.results.append(item)
            raise ex

        finally:
            if res_ok:
                self.fini_success()
            else:
                self.fini_failure()

            self.tsi.finish_tests()
            self.tsi.print_result_report(self.results)
            if not self.tsi.is_check_scenario_mode():
                pmonitor.stop()

        return res_ok

    def play_item(self, inode, xml):
        self.check_keyboard_interrupt()
        if inode.name == "action":
            return self.action_item(inode)
        elif inode.name == "check":
            return self.check_item(inode, xml)
        elif inode.name == "compare":
            return self.compare_item(inode, xml)

        ret = make_default_item()
        ret['result'] = t_UNKNOWN
        ret['text'] = "UNKNOWN ACTION TYPE"
        ret['nrecur'] = self.tsi.nrecur
        ret['item_type'] = 'check'
        return ret

    def play_test(self, xml, testnode, logfile, spec_replace_list=list()):

        self.add_to_test_replace(spec_replace_list)

        result = make_default_item()
        result['name'] = to_str(self.replace(testnode.prop('name')))
        result['comment'] = to_str(self.replace(testnode.prop('comment')))
        result['filename'] = xml.getFileName()
        result['call_level'] = self.call_level
        result['xmlnode'] = testnode
        result['tags'] = to_str(self.replace(testnode.prop('tags')))
        result['disable_tags'] = to_str(self.replace(testnode.prop('disable_tags')))
        result['tag'] = self.first_tag(result['tags'])
        result['nrecur'] = self.tsi.nrecur
        result['item_type'] = 'test'

        self.add_disable_tags(result['disable_tags'])

        testname = "'%s'" % result['name']

        if len(result['tags']) > 0 and len(result['tag']) > 0:
            testname = '%s [%s]' % (testname, result['tag'])

        # выставляем переменные окружения
        self.tsi.add_testsuite_environ_variable('TESTNAME', testname)
        self.tsi.add_testsuite_environ_variable('TESTFILE', xml.getFileName())
        self.tsi.add_testsuite_environ_variable('CURDIR', os.getcwd())

        # если заданы теги то игнорируем тесты не проходящие проверку
        if len(self.tags) > 0 and not self.check_tag(result['tags']):
            result['result'] = t_NONE
            result['time'] = 0
            result['text'] = testname
            result['type'] = t_NONE
            self.del_from_test_replace(spec_replace_list)
            self.del_disable_tags(result['disable_tags'])
            return result

        self.call_stack.append(result)

        # сохраняем ссылку на свой тест и предыдущий
        result = self.call_stack[-1]
        prevStackItem = None
        if len(self.call_stack) > 1:
            prevStackItem = self.call_stack[-2]

        # if prevStackItem is not None:
        #     print "PREV CALL STACK: [%d] %s  " % (prevStackItem['call_level'],str(prevStackItem['name']))

        t_ignore = to_int(self.replace(testnode.prop('ignore')))

        if t_ignore:
            result['result'] = t_IGNORE
            result['time'] = 0
            result['text'] = testname
            result['type'] = t_IGNORE
            self.tsi.set_result(result, False)
            self.del_from_test_replace(spec_replace_list)
            self.del_disable_tags(result['disable_tags'])
            # сохраняем ещё ссылку на предыдущий элемент
            result['prev'] = prevStackItem
            return result

        curnode = self.begin(testnode)

        # FIXME: Временно ведение лог файл отключено
        # mylog = to_str(self.replace(testnode.prop('logfile')))
        # mylog_trunc = to_int(self.replace(testnode.prop('logfile_trunc')))
        # if mylog != "":
        #     self.tsi.set_logfile(mylog, mylog_trunc)
        # elif self.tsi.get_logfile() != logfile:
        #     self.tsi.set_logfile(logfile)

        r_list = get_replace_list(to_str(self.replace(testnode.prop('replace'))))
        r_list = self.replace_list(r_list)
        self.add_to_test_replace(r_list)

        self.tsi.set_ignorefailed(to_int(self.replace(testnode.prop('ignore_failed'))))
        self.test_conf = self.replace(testnode.prop('config'))

        # чисто визуальное отделение нового теста
        #        if self.tsi.printlog == True and self.tsi.nrecur<=0:
        #           print "---------------------------------------------------------------------------------------------------------------------"

        info = make_info_item(testname, 'BEGIN', result)
        info['nrecur'] = self.tsi.nrecur
        info['item_type'] = result['item_type']
        self.tsi.set_result(info, False)
        tm_start = time.time()
        tm_finish = tm_start
        try:
            while curnode is not None:
                ret = self.play_item(curnode, xml)
                if ret['result'] != t_UNKNOWN:
                    result['items'].append(ret)
                    result['time'] = time.time() - tm_start

                curnode = xml.nextNode(curnode)

        except (TestSuiteException, TestSuiteValidateError), e:
            result['result'] = t_FAILED
            result['items'].append(e.failed_item)
            tm_finish = e.getFinishTime()
            # ttime = tm_finish - tm_start
            raise e
        else:
            tm_finish = time.time()
        finally:
            self.wait_finish_reset_thread()
            self.del_from_test_replace(spec_replace_list)
            self.del_from_test_replace(r_list)
            self.del_disable_tags(result['disable_tags'])
            self.test_conf = ""
            tres = self.get_cumulative_result(result['items'])
            ttime = tm_finish - tm_start
            td = datetime.timedelta(0, ttime)
            result['time'] = ttime
            result['result'] = tres['result']
            result['text'] = tres['text']
            result['prev'] = prevStackItem
            # result['prev'] = prevStackItem
            info = make_default_item()
            info['type'] = 'FINISH'
            info['text'] = "'%s' /%s/" % (result['name'], td)
            info['result'] = result['result']
            info['nrecur'] = self.tsi.nrecur
            info['item_type'] = result['item_type']
            self.tsi.set_result(info, False)
            self.tsi.finish_test_event()

        return result

    def get_cumulative_result(self, items):
        i_res = 0
        f_res = 0
        p_res = 0
        w_res = 0
        u_res = 0
        l_err = ''
        c_res = t_UNKNOWN
        t_res = 0

        for tres in items:

            if 'result' not in tres:
                continue

            r = tres['result']
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
        elif f_res > 0 and p_res == 0 and i_res == 0:
            c_res = t_FAILED
        elif p_res > 0 and f_res == 0 and i_res >= 0:
            c_res = t_PASSED
        elif i_res > 0 and p_res == 0 and f_res == 0:
            c_res = t_IGNORE
        elif f_res > 0:
            c_res = t_WARNING

        # print "cumulative: RES=%s (f_res=%d p_res=%d i_res=%d w_res=%d unknown=%d) for %s"%(c_res,f_res,p_res,i_res,w_res,u_res,str(tres))
        ret = make_default_item()
        ret['result'] = c_res
        ret['text'] = l_err
        ret['time'] = t_res
        ret['file'] = ''
        ret['name'] = ''
        ret['nrecur'] = self.tsi.nrecur
        return ret

    @staticmethod
    def on_key_press(c):
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
        """
        :param tname: строка в виде prop=test1,prop2=test2,...
        :return: список пар [prop,testname]
        """

        retlist = list()
        if len(tname) == 0:
            return retlist

        tlist = tname.strip().split(',')
        if len(tlist) == 0:
            return retlist

        for t in tlist:
            p = t.strip().split('=')
            if len(p) > 1:
                retlist.append(p)
            else:
                retlist.append(["name", p[0]])

        return retlist


if __name__ == "__main__":

    #    import os
    #    import termios
    #    old_settings = termios.tcgetattr(sys.stdin)

    global_player = None
    print_calltrace = False
    print_calltrace_limit = 20
    global_result = None

    try:
        ts = TestSuiteInterface()

        plugDirs = ['./plugins.d', ts.get_plugins_dir()]
        for d in plugDirs:
            try:
                if d:
                    ts.load_plugins(d)
            except TestSuiteException, e:
                pass

        if ts.plugins_count() == 0:
            print "TestSuiteInterface: ERROR: not found testsuite plugins.. :( "
            print "check directory: %s" % ' '.join(plugDirs)
            exit(1)

        if ts.checkArgParam('--help', False) == True or ts.checkArgParam('-h', False) == True:
            print 'Usage: %s [--confile [configure.xml|alias@conf1.xml,alias2@conf2.xml,..]  --testfile scenario.xml' % \
                  sys.argv[0]
            print '\n'
            print '--confile [conf.xml,alias1@conf.xml,..]  - Configuration file for uniset test scenario.'
            print '--testfile tests.xml      - Test scenarion file.'
            print '--show-test-log           - Show test log'
            print '--show-action-log         - Show actions log'
            print '--show-result-report      - Show result report '
            print '--show-result-only        - Show only result report (ignore --show-action-log, --show-test-log)'
            print '--show-filename-in-report - Show filename in result report'
            print ''
            print '--show-comments           - Display all comments (test,check,action)'
            print '--show-numline            - Display line numbers'
            print '--show-timestamp          - Display the time'
            print '--show-test-comment       - Display test comment'
            print '--show-test-type          - Display the test type'
            print '--hide-time               - Hide elasped time'
            print '--col-comment-width val   - Width for column "comment"'
            print ''
            print '--test-name test1,prop2=test2,prop3=test3,...  - Run tests from list. By default prop=name'
            print '--ignore-run-list                - Ignore <RunList>'
            print '--ignore-nodes                   - Do not use \'@node\' or do not check node available for check scenario mode'
            print '--default-timeout msec           - Default <check timeout=\'..\' ../>.\''
            print '--default-check-pause msec       - Default <check check_pause=\'..\' ../>.\''
            print '--junit filename                 - Disable colorization output'
            print '--print-calltrace                - Display test call trace with test file name. If test-suite FAILED.'
            print '--print-calltrace-limit N        - How many recent calls to print. Default: 20.'
            print '--supplier-name name             - ObjectName for testsuite under which the value is stored in the SM. Default: AdminID.'
            print ''
            print "--check-scenario                 - Enable 'check scenario mode'. Ignore for all tests result. Only check parameters"
            print "--check-scenario-ignore-failed   - Enable 'check scenario mode'. Ignore for all tests result and checks"
            print "--play-tags '#tag1#tag2#tag3..'  - Play tests only with the specified tag"
            print "--show-test-tree                 - Show tree of tests"
            print "--show-test-filename             - Show test filename"
            print ''
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
        if show_result_only:
            show_actlog = False
            show_log = False

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
        calltrace_disable_extinfo = ts.checkArgParam('--calltrace-disable-extended-info', False)
        supplier_name = ts.getArgParam("--supplier-name", "")
        check_scenario = ts.checkArgParam("--check-scenario", False)
        check_scenario_ignorefailed = ts.checkArgParam("--check-scenario-ignore-failed", False)
        tags = ts.getArgParam("--play-tags", "")
        show_test_tree = ts.checkArgParam("--show-test-tree", False)
        show_test_filename = ts.checkArgParam("--show-test-filename", False)
        if show_test_tree:
            check_scenario = True
            # check_scenario_ignorefailed = True
            show_result = False

        cf = conflist.split(',')
        ts.init_uniset_interfaces(cf)

        ts.set_ignore_nodes(ignore_nodes)
        ts.set_show_test_tree_mode(show_test_tree)

        consoleRepoter = TestSuiteConsoleReporter()
        consoleRepoter.set_notimestamp(showtimestamp == False)
        consoleRepoter.set_show_comments(show_comments)
        consoleRepoter.set_show_numline(show_numstr)
        consoleRepoter.set_hide_time(hide_time)
        consoleRepoter.set_show_test_type(show_test_type)
        consoleRepoter.set_col_comment_width(col_comment_width)
        consoleRepoter.set_show_test_comment(show_test_comment)
        consoleRepoter.no_coloring_output = coloring_out
        consoleRepoter.printlog = show_log
        consoleRepoter.printactlog = show_actlog
        consoleRepoter.calltrace_disable_extinfo = calltrace_disable_extinfo
        consoleRepoter.setShowTestTreeMode(show_test_tree)
        consoleRepoter.show_test_filename = show_test_filename
        # consoleRepoter.printresult = show_result
        ts.add_repoter(consoleRepoter)

        if len(junit) > 0:
            junitRepoter = TestSuiteJUnitReporter()
            junitRepoter.set_logfile(junit)
            ts.add_repoter(junitRepoter)

        ts.set_check_scenario_mode(check_scenario)
        if check_scenario_ignorefailed:
            ts.set_check_scenario_mode(True)
            ts.set_check_scenario_mode_ignore_failed(True)

        if check_scenario or check_scenario_ignorefailed:
            ignore_runlist = True

        player = TestSuiteXMLPlayer(ts, testfile, ignore_runlist)
        player.show_result_report = show_result
        player.default_timeout = tout
        player.default_check_pause = check_pause
        player.junit = junit
        player.set_tags(tags)
        if len(supplier_name) > 0:
            player.set_supplier_name(supplier_name)

        testname = ts.getArgParam("--test-name", "")
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
        print "(TestSuiteXMLPlayer): catch exception: " + str(e.getError())
    except UException, e:
        print "(TestSuiteXMLPlayer): catch exception: " + str(e.getError())
    except KeyboardInterrupt:
        print "(TestSuiteXMLPlayer): catch keyboard interrupt.. "
    # except Exception, e:
    #        print "(TestSuiteXMLPlayer): catch basic python exception..."

    finally:
        #         sys.stdin = sys.__stdin__
        if global_player is not None and print_calltrace and global_result != True:
            global_player.show_call_trace(print_calltrace_limit)
    # if sys.stdin.closed == False:
    #       termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    exit(1)
