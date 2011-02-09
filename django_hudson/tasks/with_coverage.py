# -*- coding: utf-8 -*-
# pylint: disable=W0201
import os, sys
from coverage.control import coverage
from django.conf import settings
from django_hudson.tasks import BaseTask

class Task(BaseTask):
    def add_options(self, group):
        group.add_option("--coverage-rcfile",
                         dest="coverage_rcfile",
                         default="",
                         help="coverage configuration file.")
        group.add_option("--coverage-html-report",
                         dest="coverage_html_report_dir",
                         default="",
                         help="Directory to which HTML coverage report should be written. If not specified, no report is generated.")
        group.add_option("--coverage-no-branch-measure",
                         action="store_false", default=True,
                         dest="coverage_measure_branch",
                         help="Don't measure branch coverage.")

    def configure(self, test_labels, options):
        self.test_labels = test_labels
        self.output_dir = options['output_dir']
        self.html_dir = options['coverage_html_report_dir']
        self.coverage = coverage(branch = options['coverage_measure_branch'],
                                 source = test_labels or None,
                                 config_file = options.get('coverage_rcfile', Task.default_config_path))
        self.coverage.start()

    def after_tasks_run(self):
        self.coverage.stop()

        modules = [ module for name, module in sys.modules.items() \
                        if self.want_module(name, module)]
        morfs = [ self.src(m.__file__) for m in modules if self.src(m.__file__).endswith(".py")]

        self.coverage.xml_report(morfs, outfile=os.path.join(self.output_dir, 'coverage.xml'))

        if self.html_dir:
            self.coverage.html_report(morfs, directory=self.html_dir)
    
    def want_module(self, modname, mod):
        """
        Predicate for covered modules
        """
        #No cover if it ain't got a file
        if not hasattr(mod, "__file__"): 
            return False

        if self.test_labels:
            #If it's one of the explicit test labels called for
            for label in self.test_labels:
                if label and label in modname:
                    return True
            return False
        return True

    @staticmethod
    def src(filename):
        """
        Find the python source file for a .pyc, .pyo or $py.class file on
        jython. Returns the filename provided if it is not a python source
        file. Cribbed from nose.util
        """
        if filename is None:
            return filename
        if sys.platform.startswith('java') and filename.endswith('$py.class'):
            return '.'.join((filename[:-9], 'py'))
        base, ext = os.path.splitext(filename)
        if ext in ('.pyc', '.pyo', '.py'):
            return '.'.join((base, 'py'))
        return filename

    @staticmethod
    def default_config_path():
        rcfile = getattr(settings, 'COVERAGE_RCFILE', 'coverage.rc')
        if os.path.exists(rcfile):
            return rcfile
        return None

