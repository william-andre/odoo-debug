import os
from time import perf_counter
from contextlib import contextmanager

import icecream

import odoo
try:
    from odoo.addons.base.models.ir_cron import IrCron
except ImportError:
    # before 18.1
    from odoo.addons.base.models.ir_cron import ir_cron as IrCron

try:
    builtins = __import__('__builtin__')
except ImportError:
    builtins = __import__('builtins')


##################################################################################################
# Allow to use `ic()` everywhere without importing
setattr(builtins, 'ic', icecream.ic)


##################################################################################################
# Timer util
@contextmanager
def catchtime() -> float:
    t1 = t2 = perf_counter()
    yield lambda: t2 - t1
    t2 = perf_counter()
    print(f"Time elapsed: {t2 - t1:.6f}s")
setattr(builtins, 'catchtime', catchtime)


##################################################################################################
# Disable cron jobs completely as it is annoying for devs in logs and debuggers
def _process_jobs(db_name):
    pass
IrCron._process_jobs = _process_jobs


##################################################################################################
# Update VSCode launch.json with the current database and test tags
if (
    'TERM_PROGRAM' not in os.environ.keys()
    or os.environ['TERM_PROGRAM'] != 'vscode'
):
    odoo_root_path = '/'.join(odoo.__file__.split('/')[:-2])
    vscode_config_path = odoo_root_path + '/.vscode/launch.json'

    init = odoo.tools.config['init'] and f""""--init={",".join(odoo.tools.config['init'])}",""" or ""

    with open(vscode_config_path, 'w') as f:
        f.write(f"""\
{{
    "version": "0.2.0",
    "configurations": [
        {{
            "name": "Python: Odoo",
            "type": "debugpy",
            "request": "launch",
            "program": "odoo-bin",
            "console": "integratedTerminal",
            "args": [
                "--log-level={odoo.tools.config['log_level']}",
                "--test-tags={odoo.tools.config['test_tags'] or ""}",
                "--database={odoo.tools.config['db_name']}",
                "--addons-path={odoo.tools.config['addons_path']}",
                {init}
                "--limit-time-cpu=99999999",
                "--limit-time-real=99999999",
                "--limit-memory-soft=17179869184",
                "--limit-memory-hard=17179869184",
                {odoo.tools.config['stop_after_init'] and '"--stop-after-init",' or ''}
            ],
        }}
    ]
}}
""")
