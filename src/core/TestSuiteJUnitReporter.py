#!/usr/bin/env python
# -*- coding: utf-8 -*-

from TestSuiteGlobal import *


class TestSuiteJUnitReporter(TestSuiteReporter):
    '''
    Класс реализующий вывод отчёта в формате junit
    '''

    def __init__(self, arg_prefix='junit', **kwargs):
        TestSuiteReporter.__init__(self, **kwargs)

        self.junit_filename = ""

        TestSuiteReporter.commandline_to_attr(self, arg_prefix, 'junit')

    def is_enabled(self):
        return (len(self.junit_filename) > 0)

    @staticmethod
    def print_help(prefix='junit'):
        print 'TestSuiteJUnitReporter (--' + prefix + ')'
        print '--------------------------------------------'
        print '--' + prefix + '-filename name  - Save junit report to file'

    def print_log(self, item):
        pass

    def print_actlog(self, act):
        pass

    def make_report(self, results, checkScenarioMode=False):

        if self.show_test_tree or checkScenarioMode:
            return

        try:
            repfile = open(self.junit_filename, "w")
            repfile.writelines('<?xml version="1.0" encoding="UTF-8"?>\n')

            t_stat = self.get_statistics(results)

            repfile.writelines('<testsuite name="%s" tests="%d" failures="%d" skipped="%d">\n' % (
            self.junit_filename, t_stat['all_num'],t_stat['fail_num'], t_stat['skip_num']))

            self.write_results(repfile, results, 1)

            repfile.writelines('</testsuite>\n')
            repfile.close()

        except IOError, e:
            print "(TestSuiteJUnitReporter): error: %s" % e.message

    def write_results(self, repfile, results, tnum):

        for res in results:

            if res['item_type'] != 'test':
                continue

            tnum = self.write_item(repfile, res, tnum)

        return tnum

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
                repfile.writelines('    <failure>%s</failure>\n' % (res['text']))
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
        # надо пройтись по items.. и собрать все FAILED (по идее он будет один)
        if len(res['items']) == 0:
            return res['text']

        err_text = ''
        for i in res['items']:
            if i['result'] == t_FAILED:
                if len(err_text) > 0:
                    err_text = '%s\n%s' % (err_text, i['text'])
                else:  # добавление первого элемента
                    err_text = '%s' % i['text']

        return err_text

    def get_statistics(self, results):
        t_stat = dict()
        t_stat['all_num'] = len(results)
        t_stat['pass_num'] = 0
        t_stat['fail_num'] = 0
        t_stat['skip_num'] = 0

        for t in results:
            if t['result'] == t_PASSED:
                t_stat['pass_num'] += 1
            elif t['result'] == t_FAILED:
                t_stat['fail_num'] += 1
            elif t['result'] == t_IGNORE:
                t_stat['skip_num'] += 1

        return t_stat
