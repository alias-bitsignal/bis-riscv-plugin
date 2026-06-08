import sqlite3
import os
import json
import base64
import struct

WORKING_DIR = os.path.dirname(os.path.abspath(__file__)) + "/"

class RiscvApp:

    def __init__(self):
        if not os.path.isdir(WORKING_DIR + "data/"):
            os.mkdir(WORKING_DIR + "data/")

        self.db = sqlite3.connect(WORKING_DIR + "data/riscv.db", check_same_thread=False)
        c = self.db.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS executions(
                signature TEXT PRIMARY KEY,
                block_height INTEGER,
                timestamp NUMERIC,
                sender TEXT,
                recipient TEXT,
                result INTEGER
            )
        """)
        self.db.commit()

    # --- VM (very small demo version) ---
    def run_vm(self, code_bytes):
        regs = [0] * 32
        pc = 0

        def u32(x): return x & 0xFFFFFFFF
        def sext(x, bits):
            sign = 1 << (bits - 1)
            x &= (1 << bits) - 1
            return x - (1 << bits) if (x & sign) else x

        while True:
            if pc + 4 > len(code_bytes):
                break

            instr = struct.unpack_from("<I", code_bytes, pc)[0]
            opcode = instr & 0x7F

            if opcode == 0x13:  # ADDI only
                rd = (instr >> 7) & 0x1F
                funct3 = (instr >> 12) & 0x07
                rs1 = (instr >> 15) & 0x1F
                imm_i = sext(instr >> 20, 12)

                if funct3 == 0x0:
                    regs[rd] = u32(regs[rs1] + imm_i)
                pc += 4

            elif opcode == 0x73 and instr == 0x00000073:
                if regs[17] == 10:  # exit
                    break
                pc += 4
            else:
                break

            regs[0] = 0

        return regs[10]  # return a0

    # --- Blockchain integration ---
    def new_bismuth_tx(self, transaction):
        operation, openfield, block_height, timestamp, sender, recipient, signature = transaction

        try:
            payload = json.loads(openfield)
        except:
            return

        if "code_b64" not in payload:
            return

        try:
            code = base64.b64decode(payload["code_b64"], validate=True)
        except:
            return

        result = self.run_vm(code)

        c = self.db.cursor()
        try:
            c.execute("""
                INSERT INTO executions(signature, block_height, timestamp, sender, recipient, result)
                VALUES(?, ?, ?, ?, ?, ?)
            """, (signature, block_height, timestamp, sender, recipient, result))
            self.db.commit()
        except:
            pass  # already exists

    def remove_since(self, height):
        c = self.db.cursor()
        c.execute("DELETE FROM executions WHERE block_height >= ?", (height,))
        self.db.commit()

    def load_from_ledger(self, ledger_path=""):
        ledger = sqlite3.connect(ledger_path, check_same_thread=False)
        c = ledger.cursor()

        c.execute("""
            SELECT operation, openfield, block_height, timestamp, address, recipient, signature
            FROM transactions
            WHERE operation='riscv:run'
            ORDER BY block_height ASC, timestamp ASC
        """)

        for tx in c.fetchall():
            self.new_bismuth_tx(tx)

riscv_app = RiscvApp()

