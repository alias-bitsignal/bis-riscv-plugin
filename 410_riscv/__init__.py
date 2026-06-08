import sys
import os.path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from riscv_app import riscv_app

MANAGER = None

def action_init(params):
    global MANAGER
    try:
        MANAGER = params['manager']
        riscv_app.load_from_ledger(ledger_path=MANAGER.config.ledger_path)
    except Exception as e:
        print(e)

def action_fullblock(full_block):
    for tx in full_block['transactions']:
        if tx[10] == "riscv:run":
            riscv_app.new_bismuth_tx((
                tx[10],     # operation
                tx[11],     # openfield
                int(tx[0]), # block height
                float(tx[1]),
                tx[2],      # sender
                tx[3],      # recipient
                tx[5]       # signature
            ))

def action_rollback(info):
    riscv_app.remove_since(int(info["height"]))
