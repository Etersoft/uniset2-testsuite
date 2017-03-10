#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
import string
from TestSuiteGlobal import *
from uniset2.UGlobal import *
from uniset2.pyUExceptions import UException
from TestSuiteReporter import *


class TestSuiteConsoleReporter(TestSuiteReporter):
    '''
    Класс реализующий вывод лога на экран. Управляется аргументами командной строки
    начинающимися с префикса --log-xxxx.
    '''

    def __init__(self, arg_prefix='log', **kwargs):
        TestSuiteReporter.__init__(self, **kwargs)

        self.colsep = ":"  # символ разделитель столбцов (по умолчанию)
        self.log_col_comment_width = 50
        self.log_col_tree_width = 45
        self.numstr = 0
        self.log_show_numline = False
        self.log_show_tests = False
        self.log_show_actions = False
        self.log_show_timestamp = False
        self.log_show_test_type = False
        self.log_show_comments = False
        self.log_show_test_comment = False
        self.log_hide_time = False
        self.log_hide_msec = False
        self.log_show_test_type = False
        self.log_no_coloring_output = False
        self.log_calltrace_disable_extended_info = False
        self.log_show_test_filename = False

        TestSuiteReporter.commandline_to_attr(self, arg_prefix, 'log')

        if checkArgParam('--' + arg_prefix + '-show-result-only', False):
            self.log_show_actions = False
            self.log_show_tests = False

    @staticmethod
    def print_help(prefix='log'):

        print 'TestSuiteConsoleReporter (--' + prefix +')'
        print '--------------------------------------------'
        print '--' + prefix + '-show-tests              - Show tests log'
        print '--' + prefix + '-show-actions            - Show actions log'
        print '--' + prefix + '-show-result-only        - Show only result report (Ignore [show-actions,show-tests])'
        print '--' + prefix + '-show-comments           - Display all comments (test,check,action)'
        print '--' + prefix + '-show-numline            - Display line numbers'
        print '--' + prefix + '-show-timestamp          - Display the time'
        print '--' + prefix + '-show-test-filename      - Display test filename in test tree'
        print '--' + prefix + '-show-test-comment       - Display test comment'
        print '--' + prefix + '-show-test-type          - Display the test type'
        print '--' + prefix + '-hide-time               - Hide elasped time'
        print '--' + prefix + '-hide-msec               - Hide milliseconds'
        print '--' + prefix + '-col-comment-width val   - Width for column "comment"'
        print '--' + prefix + '-no-coloring-output      - Disable colorization output'
        print '--' + prefix + '-calltrace-disable-extended-info - Disable show calltrace extended information'

    def is_enabled(self):
        return True

    def finish_test_event(self):

        if self.log_show_tests:
            print "---------------------------------------------------------------------------------------------------------------------"

    def print_log(self, item):

        txt = self.make_log(item)

        if self.show_test_tree:
            if item['item_type'] == 'test' and item['type'] != 'FINISH':
                print txt
            return

        if self.log_show_tests:
            print txt

    def make_log(self, item):

        t_comment = item['comment']
        t_test = item['type']
        txt = item['text']
        t_result = item['result']
        try:
            if t_comment is not None and len(t_comment) > 0:
                t_comment = unicode(t_comment, "UTF-8", errors='replace')
        except UnicodeDecodeError:
            pass
        except TypeError:
            pass

        t_tm = str(time.strftime('%Y-%m-%d %H:%M:%S'))

        ntab = False
        if item['item_type'] == 'check' or item['item_type'] == 'action':
            ntab = True

        txt2 = self.set_tab_space(txt, item['nrecur'], ntab)

        if self.show_test_tree:
            if item['item_type'] == 'test' and item['type'] != 'FINISH':
                self.numstr += 1

            if self.log_show_numline:
                txt2 = '%4s %s' % (self.numstr, txt2)

            # if self.log_show_comments or self.log_show_test_comment:
            txt2 = "%s %s" % (txt2.ljust(self.log_col_tree_width), t_comment)

            if self.log_show_test_filename:
                txt2 = "[%35s]   %s" % (item['filename'], txt2)

            return txt2

        self.numstr += 1

        txt = str('[%s] %s%8s%s %s' % (
            self.colorize_result(t_result), self.colsep, t_test, self.colsep,
            self.colorize_text(t_result, t_test, txt2)))

        if not self.log_show_test_type:
            txt = str('[%s] %s %s' % (
                self.colorize_result(t_result), self.colsep, self.colorize_text(t_result, t_test, txt2)))

        if self.log_show_comments or self.log_show_test_comment:
            if not t_comment or (self.log_show_test_comment and not self.log_show_comments and t_test != 'BEGIN'):
                t_comment = ""

            try:
                txt = '%s %s %s' % (
                    self.colorize_text(t_result, t_test,
                                       t_comment.ljust(self.log_col_comment_width)[0:self.log_col_comment_width]),
                    self.colsep, txt)
            except UnicodeDecodeError:
                pass
            except TypeError:
                pass

        etm = self.elapsed_time_str()

        if not self.log_hide_time:
            txt = '%s %s %s' % (etm, self.colsep, txt)

        if self.log_show_test_type:
            txt = '%6s %s %s' % ("CHECK", self.colsep, txt)

        if self.log_show_timestamp:
            txt = "%s %s%s" % (t_tm, self.colsep, txt)

        if self.log_show_numline:
            txt = '%4s %s %s' % (self.numstr, self.colsep, txt)

        return txt

    def print_actlog(self, act):

        txt = self.make_actlog(act)

        if self.show_test_tree:
            if act['item_type'] == 'test' and act['type'] != 'FINISH':
                print txt
            return

        if self.log_show_actions:
            print txt

    def make_actlog(self, act):

        t_comment = act['comment']
        t_act = act['type']
        txt = act['text']
        t_result = act['result']

        try:
            if t_comment is not None and len(t_comment) > 0:
                t_comment = unicode(t_comment, "UTF-8", errors='replace')
        except UnicodeDecodeError:
            pass
        except TypeError:
            pass

        t_tm = str(time.strftime('%Y-%m-%d %H:%M:%S'))

        ntab = False
        if act['item_type'] == 'action' or act['item_type'] == 'check':
            ntab = True

        txt2 = self.set_tab_space(txt, act['nrecur'], ntab)

        if self.show_test_tree:
            if act['item_type'] == 'test' and act['type'] != 'FINISH':
                self.numstr += 1

            if self.log_show_numline:
                txt2 = '%4s %s' % (self.numstr, txt2)

            # if self.log_show_comments or self.log_show_test_comment:
            txt2 = "%s\t\t%s" % (txt2, t_comment)

            if self.log_show_test_filename:
                txt2 = "[%35s]   %s" % (act['filename'], txt2)

            return txt2

        self.numstr += 1

        txt = str('[%7s] %s%8s%s %s' % (
            self.colorize_result(t_result), self.colsep, t_act, self.colsep, self.colorize_text(t_result, t_act, txt2)))

        if not self.log_show_test_type:
            txt = str('[%7s] %s %s' % (
                self.colorize_result(t_result), self.colsep, self.colorize_text(t_result, t_act, txt2)))

        if self.log_show_comments or self.log_show_test_comment:
            if not t_comment or (self.log_show_test_comment and not self.log_show_comments and t_act != 'BEGIN'):
                t_comment = ""

            try:
                txt = '%s %s %s' % (
                    self.colorize_text(t_result, t_act,
                                       t_comment.ljust(self.log_col_comment_width)[0:self.log_col_comment_width]),
                    self.colsep, txt)
            except UnicodeDecodeError:
                pass
            except TypeError:
                pass

        etm = self.elapsed_time_str()

        if not self.log_hide_time:
            txt = '%s %s %s' % (etm, self.colsep, txt)

        if self.log_show_test_type:
            txt = '%6s %s %s' % ('ACTION', self.colsep, txt)

        if self.log_show_timestamp:
            txt = '%s %s%s' % (t_tm, self.colsep, txt)

        if self.log_show_numline:
            txt = '%4s %s %s' % (self.numstr, self.colsep, txt)

        return txt

    def make_report(self, results, check_scenario_mode=False):

        if self.show_test_tree:
            return

        filename = ''
        if len(results) > 0:
            filename = results[0]['filename']

        csm = ""
        if check_scenario_mode is True:
            csm = "   !!! [CHECK SCENARIO MODE] !!!"

        head = "\nRESULT REPORT: '%s' %s" % (filename, csm)
        head2 = ""
        foot2 = ""
        for i in range(0, len(head)):
            head2 += '*'
            foot2 += "-"

        print "%s\n%s" % (head, head2)
        i = 1
        ttime = 0
        for res in results:
            td = datetime.timedelta(0, res['time'])
            print '%s. [%s] - %40s |%s|' % (
                string.rjust(str(i), 3), self.colorize_result(res['result']), string.ljust(res['name'], 45),
                td)
            i = i + 1
            ttime = ttime + res['time']

        # td = datetime.timedelta(0, ttime)
        # ts = str(td).split('.')[0]
        print foot2
        print 'Total time: %s\n' % self.elapsed_time_str()

    def colorize(self, t_result, txt):

        if self.log_no_coloring_output:
            return txt

        if t_result == t_PASSED:
            return "\033[1;32m%s\033[1;m" % txt
        if t_result == t_WARNING or t_result == t_UNKNOWN:
            return "\033[1;33m%s\033[1;m" % txt
        if t_result == t_FAILED:
            return "\033[1;31m%s\033[1;m" % txt
        if t_result == t_IGNORE:
            return "\033[1;34m%s\033[1;m" % txt

        return txt

    def colorize_test_begin(self, txt):
        if self.log_no_coloring_output:
            return txt

        return "\033[1;37m%s\033[1;m" % txt

    def colorize_test_finish(self, txt):

        # пока не будем расскрашивать "finish"
        return txt
        # return self.colorize_test_name(txt)

    def colorize_test_outlink(self, txt):
        if self.log_no_coloring_output:
            return txt

        return "\033[1;36m%s\033[1;m" % txt

    def colorize_text(self, t_result, t_test, txt):

        # раскрашиваем только t_FAILED
        if t_result == t_FAILED:
            return self.colorize(t_result, txt)

        if t_test == 'BEGIN':
            return self.colorize_test_begin(txt)

        if t_test == 'FINISH':
            return self.colorize_test_finish(txt)

        if t_test == 'OUTLINK':
            return self.colorize_test_outlink(txt)

        return txt

    def colorize_result(self, t_result):
        return self.colorize(t_result, "%7s" % t_result)

    def elapsed_time(self, t=None):
        if t is None:
            t = time.time() - self.start_time

        h = int(t / 3600.0)
        t -= 3600 * h
        m = int(t / 60)
        s = int(t - m * 60)
        t -= s
        return [h, m, s, t]

    def elapsed_time_str(self, t=None):
        h, m, s, t = self.elapsed_time(t)
        if self.log_hide_msec:
            return '%02d:%02d:%02d' % (h, m, s)

        return '%02d:%02d:%02d [%7.3f]' % (h, m, s, t)

    def format_comment(self, txt):
        t_comment = txt
        try:
            t_comment = unicode(txt, "UTF-8", errors='replace')
        except UnicodeDecodeError:
            pass
        except TypeError:
            pass

        try:
            t_comment = '%s' % t_comment.ljust(self.log_col_comment_width)[0:self.log_col_comment_width]
        except UnicodeDecodeError:
            pass
        except TypeError:
            pass

        return t_comment

    @staticmethod
    def set_tab_space(txt, nrecur, ntab):
        # сдвиг "уровня" в зависимости от рекурсии
        s_tab = ""
        if nrecur > 0:
            for i in range(0, nrecur):
                s_tab = '%s.   ' % s_tab
        txt = '%s%s' % (s_tab, txt)

        if ntab:
            txt = '.   %s' % txt

        return txt

    @staticmethod
    def build_fail_trace(call_trace):

        if len(call_trace) == 0:
            return list()

        # идём в обратном порядке
        # от последнего вызова (это тот на котором вывалился тест) до первого
        # Смысл: построить дерево вызовов от провалившегося до первого уровня
        # пропуская успешные (т.е. строится дерево вызовов приведшее до провалившегося теста)
        # -----
        # т.к. у нас сохранены ссылки на предыдущие вызовы... то просто идём по ним

        failtrace = list()
        stack_item = call_trace[-1]
        failtrace.append(stack_item)
        curlevel = stack_item['call_level']

        while stack_item is not None:

            stack_item = stack_item['prev']

            if stack_item is None:
                break

            if stack_item['call_level'] < curlevel:
                failtrace.append(stack_item)
                curlevel = stack_item['call_level']

            if stack_item['call_level'] == 0:
                break

        return failtrace[::-1]

    def make_call_trace(self, results, call_limit):
        # выводим только дерево вызовов до неуспешного теста
        # для этого надо построить дерево от последнего вызова до первого
        failtrace = self.build_fail_trace(results)

        tname_width = 40
        call_limit = abs(call_limit)
        ttab = "=== TESTFILE ==="

        print "%s| %s" % (
            self.colorize_test_begin(ttab.ljust(tname_width)),
            self.colorize_test_begin("=== TEST CALL TRACE (limit: %d) ===" % call_limit))

        fail_test = failtrace[-0]  # это просто последний тест с конца
        for stackItem in failtrace[-call_limit::]:
            tab = ""
            for i in range(0, stackItem['call_level']):
                tab = "%s.   " % tab

            t_comment = ''
            if self.log_show_test_comment:
                t_comment = " | %s " % self.format_comment(stackItem['comment'])

            # if not self.show_xmlfile:
            #     t_fname = ""

            print "%s%s| %s%s" % (stackItem['filename'].ljust(tname_width), t_comment, tab, stackItem['name'])

        print ""

        # ищем тест на котором произошёл вылет
        # это последний item в "сбойном тесте"
        if fail_test is not None and len(fail_test['items']) > 0:
            fail_item = fail_test['items'][-1]
            self.show_extended_information(fail_item)

    def show_extended_information(self, fail_item):

        if self.log_calltrace_disable_extended_info == True:
            return

        print "\n================================= EXTENDED INFORMATION =================================\n"

        ui = fail_item['ui']
        if ui is None:
            print "Extended information is not available. Error: UI is None\n"
            return

        try:
            faultySensor = to_sid(fail_item['faulty_sensor'], ui)

            if faultySensor[0] == DefaultID:
                print "Extended information is not available. Error: Unknown faulty sensor.\n"
                return

            # Получаем информацию кто и когда менял последний раз датчик
            sensorChangeInfo = ui.getTimeChange(fail_item['faulty_sensor'])

            stime = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(sensorChangeInfo.tv_sec))
            # При выводе делаем nanosec --> millisec
            print "(%d)'%s' ==> last update %s.%d value=%d owner=%d\n" % (
            faultySensor[0], fail_item['faulty_sensor'], stime, sensorChangeInfo.tv_nsec / 1000000,
            sensorChangeInfo.value, sensorChangeInfo.supplier)

            # Получаем информацию о том кто заказывал этот датчик
            # возврщется массив запрошенных датчиков с кратким описанием и списоком заказчиков по каждому датчику
            jsonConsumers = json.loads(ui.apiRequest(fail_item['faulty_sensor'], "/consumers?%s" % faultySensor[0]))
            listSensors = jsonConsumers['sensors']

            if len(listSensors) == 0:
                print "..no consumers.."
                return

            # т.к. мы запрашивали информацию об одно датчике, то в ответе (по идее) только один элемент
            sensorInfo = listSensors[0]
            if len(sensorInfo['consumers']) == 0:
                print "..no consumers for sensor '%s'..\n" % fail_item['faulty_sensor']
                return

            addon = ""
            for n in range(0, len(faultySensor[2])):
                addon = "%s=" % addon

            print "CONSUMERS INFORMATION ('%s'):" % faultySensor[2]
            print "========================%s===\n" % addon

            # Вывод информации по каждому заказчикам датчика
            for c in sensorInfo['consumers']:
                o_name = "%d@%d" % (c['id'], c['node'])
                try:
                    print "%s\n" % str(ui.getObjectInfo(o_name))
                except UException, e:
                    print "Get information for '%s' error: %s\n" % (o_name, e.getError())

            ownerID = sensorChangeInfo.supplier
            if ownerID == DefaultID:
                print "Extended information 'OWNER' is not available. Error:  Unknown owner ID for sensor %s\n" % \
                      fail_item['faulty_sensor']
                return

            if ownerID == DefaultSupplerID:
                print "Extended information 'OWNER' is not available. Perhaps the update was done with 'uniset-admin'\n"
                return

            # Получаем информацию о том кто поменял датчик
            o_name = "%d@%d" % (ownerID, faultySensor[1])

            addon = ""
            for n in range(0, len(o_name)):
                addon = "%s=" % addon

            print "OWNER INFORMATION (%s):" % o_name
            print "==================%s===\n" % addon
            print "%s\n" % str(ui.getObjectInfo(o_name))

        except UException, e:
            print "Get extended information error: %s\n" % e.getError()
