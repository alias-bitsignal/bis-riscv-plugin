Below is a structured, technical overview of a Bismuth RISC-V VM (plugin-based execution).

### Potential Advantages of a Bismuth RISC-V VM
**RISC-V**
- Register-based
- Clean, minimal ISA
- Well-defined hardware spec
- Real CPU architecture
- Easier to reason about
- Easier to formally verify
- Closer to real hardware
- Supported by real toolchains

### Deterministic Minimalism

A Bismuth plugin VM:

- Can be extremely small
- No gas accounting required (unless you add it)
- No storage trie
- No global state
- No reentrancy complexity
- No precompiles

Execution can be:
`Input → Deterministic compute → Output`
That simplicity reduces attack surface.


## RISC-V On-Chain Execution Flow

This plugin demonstrates how Bismuth abstract transactions can trigger deterministic computation.

The full execution pipeline is:
Transaction → Plugin Trigger → Decode JSON → Base64 → VM Execution → Store Result


### 1. Transaction Layer

A standard Bismuth transaction is sent with:
`operation = "riscv:run"`
`openfield = JSON payload`

Example
{"code_b64":"EwWgApMIEABzAAAAkwigAHMAAAA=","max_steps":1000}

`operation` acts as the protocol selector.
`openfield` contains structured JSON data.
`code_b64` holds raw RISC-V machine code encoded in base64.
`max_steps` limits execution deterministically.

### 2. Plugin Trigger

When a block is digested, the plugin:

- Scans all transactions in `action_fullblock`
- Matches transactions where:
`tx[10] == "riscv:run"`

### 3. JSON Decoding

The plugin parses:
`payload = json.loads(openfield)`

If valid, it extracts:
`code_b64`
optional parameters (e.g. `max_steps`)
Invalid JSON results in ignoring the transaction.

### 4. Base64 Decoding

Machine code is reconstructed:
`code = base64.b64decode(payload["code_b64"])`

This produces raw little-endian RV32 bytecode.


### 5. RISC-V VM Execution

The bytecode is executed inside a deterministic interpreter:

- Fixed memory size
- Fixed instruction subset (RV32I subset)
- Deterministic instruction limit (`max_steps`)
- Deterministic syscall handling

The VM returns the value of register `a0` (`x10`) as the result.


### 6. Result Storage

Execution results are persisted in:
`plugins/410_riscv/data/riscv.db`

SQLite schema:
```
executions(
    signature TEXT PRIMARY KEY,
    block_height INTEGER,
    timestamp NUMERIC,
    sender TEXT,
    recipient TEXT,
    result INTEGER
)
```

Each execution is:

* Deterministic
* Indexed by transaction signature
* Automatically removed on rollback
* Reloaded from ledger on node startup

### Deterministic Properties

The system guarantees deterministic behavior because:

- Code bytes are stored on-chain
- Execution limits are fixed
- No external I/O is allowed
- Results are stored per block height
- Rollbacks are handled via action_rollback

### Summary

This architecture turns Bismuth transactions into executable computation:

```
Blockchain as transport layer
openfield as program container
operation as protocol selector
plugin as execution engine
SQLite as deterministic state
```

It is a minimal example of how Bismuth can support protocol-style on-chain computation without modifying core consensus code.
