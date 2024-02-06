from ast import Import
import json
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
    from odoo.orm.registry import TriggerTree
except ImportError:
    # before 18.1
    from odoo.modules.registry import TriggerTree


try:
    builtins = __import__('__builtin__')
except ImportError:
    builtins = __import__('builtins')

IN_VS_CODE = 'TERM_PROGRAM' in os.environ.keys() and os.environ['TERM_PROGRAM'] == 'vscode'


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
# Pretty print TriggerTree

def TriggerTree_as_dict(self):
    return {'root': [str(r) for r in self.root], **{
        str(k): v.as_dict()
        for k, v in self.items()
    }}
TriggerTree.as_dict = TriggerTree_as_dict

def TriggerTree__repr__(self):
    return json.dumps(self.as_dict(), indent=4)
TriggerTree.__repr__ = TriggerTree__repr__


##################################################################################################
# Update VSCode launch.json with the current database and test tags
if not IN_VS_CODE:
    odoo_root_path = '/'.join((odoo.__file__ or odoo.init.__file__).split('/')[:-2])
    vscode_config_path = odoo_root_path + '/.vscode/launch.json'

    init = odoo.tools.config['init'] and f""""--init={",".join(odoo.tools.config['init'])}",""" or ""
    db = odoo.tools.config['db_name']
    if isinstance(db, list):
        db = db[0]
    addons = odoo.tools.config['addons_path']
    if isinstance(addons, list):
        addons = ','.join(addons)
    upgrade = odoo.tools.config['upgrade_path']
    if isinstance(upgrade, list):
        upgrade = ','.join(upgrade)

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
                "--database={db}",
                "--addons-path={addons}",
                "--upgrade-path={upgrade}",
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
