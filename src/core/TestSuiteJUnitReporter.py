#!/usr/bin/env python
# -*- coding: utf-8 -*-

from TestSuiteGlobal import *
from TestSuiteReporter import *


class TestSuiteJUnitReporter(TestSuiteReporter):
    '''
    Класс реализующий вывод отчёта в формате junit
    '''

    def __init__(self, arg_prefix='junit', **kwargs):
        TestSuiteReporter.__init__(self, **kwargs)

        self.junit_filename = ""
        self.junit_deep = -1

        TestSuiteReporter.commandline_to_attr(self, arg_prefix, 'junit')
        self.junit_deep = int(self.junit_deep)

    def is_enabled(self):
        return (len(self.junit_filename) > 0)

    @staticmethod
    def print_help(prefix='junit'):
        print 'TestSuiteJUnitReporter (--' + prefix + ')'
        print '--------------------------------------------'
        print '--' + prefix + '-filename name  - Save junit report to file'
        print '--' + prefix + "-deep val       - Deep tree of test for report. '-1' - all tests"

    def print_log(self, item):
        pass

    def print_actlog(self, act):
        pass

    def make_report(self, tree_tests, check_scenario_mode=False):

        if self.show_test_tree or check_scenario_mode:
            return

        # print "RESULT TREE:"
        # for res in tree_tests:
        #     print "%d (%s)| [%s] %s  (%d) %s" % (
        #     res['level'], res['test_type'], res['item_type'], res['name'], len(res['items']), res['text'])

        junit_tests = self.build_junit_test_list(tree_tests, self.junit_deep)

        # print "JUNIT TREE (deep_level=%d):" % self.junit_deep
        # for res in junit_tests:
        #     print "%d (%s)| [%s] %s  (%d) %s result: [%s]" % (
        #     res['level'], res['test_type'], res['item_type'], res['name'], len(res['items']), res['text'], res['result'])
        # return

        try:
            repfile = open(self.junit_filename, "w")
            repfile.writelines('<?xml version="1.0" encoding="UTF-8"?>\n')

            t_stat = self.get_statistics(junit_tests)

            repfile.writelines('<testsuite name="%s" tests="%d" failures="%d" skipped="%d">\n' % (
            self.junit_filename, t_stat['all_num'],t_stat['fail_num'], t_stat['skip_num']))

            tnum = 1
            for res in junit_tests:
                tnum = self.write_item(repfile, res, tnum)

            repfile.writelines('</testsuite>\n')
            repfile.close()

        except IOError, e:
            print "(TestSuiteJUnitReporter): error: %s" % e.message

    def build_junit_test_list(self, tree_tests, deep_level):
        '''
        Построение дерева тестов для отчёта с учётом "глубины"
        :param tree_tests: исходное дерево тестов
        :param deep_level: глубина вложенности тестов до которой включаем тесты в список
        :return: список тестов для отчёта
        '''

        junit_test_list = list()
        for t in tree_tests:
            if self.check_test(t, deep_level):
                junit_test_list.append(t)

        return junit_test_list

    def check_test(self, test, deep_level):
        '''
        Проверка должен ли входить указанный тест в отчёт.
        Если тест содержит только один item и этот item OUTLINK или LINK, значит это "сквозной тест" и мы его не считаем.
        :param test: проверяемый тест
        :param deep_level: уровень ниже которого не опускаемся
        :return: True - если тест не содержит других тестов, False - если содержит или больше заданной глубины
        '''

        try:

            if len(test['items']) == 1:

                ttype = test['items'][0]['test_type'].upper()

                if ttype == 'OUTLINK' or ttype == 'LINK' or ttype == 'TEST':

                    # если мы дальше уже всё-равно не пойдём, то надо учитывать этот тест
                    if deep_level >= 0 and test['level'] == deep_level:
                        return True

                    return False

            if deep_level >= 0 and test['level'] > deep_level:
                return False

            for i in test['items']:
                if i['test_type'] == 'TEST':
                   return False

            return True

        except KeyError, e:
            print "KEY ERROR err: %s for %s" % ( e.message, str(test) )
        except Exception, e:
            print "EXCEPTION: %s " % e.message

        return False

    def write_item(self, repfile, res, tnum):

        if res['result'] == t_PASSED:
            repfile.writelines('  <testcase name="%s" time="%s" id="%d"/>\n' % (res['name'], res['time'], tnum))
        else:
            repfile.writelines('  <testcase name="%s" time="%s" id="%d">\n' % (res['name'], res['time'], tnum))
            if res['result'] == t_IGNORE:
                repfile.writelines('    </skipped>\n')
            elif res['result'] == t_FAILED:
                repfile.writelines('    <failure>%s</failure>\n' % self.get_test_error(res))
                # repfile.writelines('    <system-err>\n')
                # repfile.writelines('    </system-err>\n')
                # repfile.writelines('    <system-out>\n')
                # repfile.writelines('    </system-out>\n')
            elif res['result'] != t_PASSED:
                repfile.writelines('    <failure>%s</failure>\n' % self.get_test_error(res))
                # repfile.writelines('    <system-err>\n')
                # for l in r[4]:
                #     if l[0][logid.Result] == 'FAILED':
                #         repfile.writelines('%s\n' % str(l[1]))
                # repfile.writelines('    </system-err>\n')
                #
                # repfile.writelines('    <system-out>\n')
                # for l in r[4]:
                #     repfile.writelines('%s\n' % str(l[1]))
                # repfile.writelines('    </system-out>\n')

            repfile.writelines('  </testcase>\n')

        tnum += 1
        return tnum

    def get_test_error(self, res):

        if len(res['items']) == 0:
            return res['text']

        # надо пройтись по items.. и собрать все FAILED (по идее он будет один)
        err_text = ''
        for i in res['items']:
            if i['result'] == t_FAILED:
                if len(err_text) > 0:
                    err_text = '%s\n%s' % (err_text, i['text'])
                else:  # добавление первого элемента
                    err_text = '%s' % i['text']

        return err_text

    def get_statistics(self, tree_tests):
        t_stat = dict()
        t_stat['all_num'] = 0
        t_stat['pass_num'] = 0
        t_stat['fail_num'] = 0
        t_stat['skip_num'] = 0

        for t in tree_tests:
            t_stat['all_num'] += 1
            if t['result'] == t_PASSED:
               t_stat['pass_num'] += 1
            elif t['result'] == t_FAILED:
                 t_stat['fail_num'] += 1
            elif t['result'] == t_IGNORE:
                 t_stat['skip_num'] += 1

        return t_stat
