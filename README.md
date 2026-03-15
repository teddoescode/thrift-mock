# thrift-mock

Dynamically spin up mock Apache Thrift servers from `.thrift` IDL files. No codegen, no real backend — just point it at an IDL file and get a working server that returns sensible defaults for every method.

## Installation

```bash
pip install thrift-mock
```

## Quick Start

### Single server

```bash
thrift-mock serve --thrift path/to/service.thrift --port 9090
```

Parses the `.thrift` file, generates default responses for every method, and starts a mock server on the specified port. Press Ctrl+C to stop.

### Multiple servers from a manifest

```bash
thrift-mock manifest --file manifest.yaml
```

Starts all servers defined in the manifest concurrently. If one fails to start (bad IDL, port conflict), it is skipped and the rest continue.

**`manifest.yaml`:**

```yaml
servers:
  - thrift: path/to/user_service.thrift
    port: 9091

  - thrift: path/to/order_service.thrift
    port: 9092
    transport: framed
    protocol: compact
    overrides: order_overrides.yaml
```

All paths are resolved relative to the manifest file, so the manifest is portable.

## Default Responses

Every method returns a zero-value based on its return type:

| Type | Default |
|------|---------|
| `void` | no return |
| `bool` | `False` |
| `i16/i32/i64` | `0` |
| `double` | `0.0` |
| `string` | `""` |
| `binary` | `b""` |
| `list<T>/set<T>` | empty collection |
| `map<K,V>` | `{}` |
| Structs | all fields set to their type defaults |
| Enums | first defined value |

## Response Overrides

Pass a YAML config with `--overrides` to return custom values for specific methods:

```bash
thrift-mock serve --thrift path/to/service.thrift --port 9090 --overrides overrides.yaml
```

**`overrides.yaml`:**

```yaml
services:
  MyService:
    getUser:
      return:
        id: 42
        name: "alice"
        active: true
    getCount:
      return: 99
    getName:
      return: "mock-name"
```

Any method not listed falls back to its default value. Overrides can also be specified per-server inside a manifest (see above).

## Exception Simulation

Use `throw` instead of `return` to make a method raise a declared Thrift exception:

```yaml
services:
  MyService:
    getUser:
      throw: UserNotFoundException
    createUser:
      throw: ServiceUnavailableException
```

The exception must be declared in the `.thrift` file. The mock raises it exactly as the real service would.

## Transport & Protocol

Match the transport and protocol your client uses (defaults: `buffered` + `binary`):

```bash
thrift-mock serve --thrift service.thrift --port 9090 --transport framed --protocol compact
```

Options:
- `--transport`: `buffered` (default), `framed`
- `--protocol`: `binary` (default), `compact`

The same options are available per-server in a manifest.

## Compatibility

thrift-mock speaks standard Thrift wire protocol. Any existing Thrift client — regardless of language or generator — will work as long as transport and protocol match. No client-side changes required.

## Testing It Yourself

**1. Install from source:**

macOS / Linux:
```bash
git clone https://github.com/your-org/thrift-mock.git
cd thrift-mock
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Windows (Command Prompt):
```bat
git clone https://github.com/your-org/thrift-mock.git
cd thrift-mock
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e ".[dev]"
```

Windows (PowerShell):
```powershell
git clone https://github.com/your-org/thrift-mock.git
cd thrift-mock
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

**2. Start the mock server (defaults only):**

```bash
thrift-mock serve --thrift tests/fixtures/test_service.thrift --port 9090
```

**3. In a second terminal, run the test client:**

macOS / Linux:
```bash
source .venv/bin/activate
python tests/client.py 9090
```

Windows:
```bat
.venv\Scripts\activate.bat
python tests\client.py 9090
```

You should see default values printed for every method.

**4. Try overrides — create `my_overrides.yaml`:**

```yaml
services:
  TestService:
    getCount:
      return: 42
    getName:
      return: "hello from mock"
    getUser:
      return:
        id: 7
        name: "override user"
        email: "override@example.com"
```

Restart the server with overrides:

```bash
thrift-mock serve --thrift tests/fixtures/test_service.thrift --port 9090 --overrides my_overrides.yaml
```

Run the client again — `getCount`, `getName`, and `getUser` will return your configured values.

**5. Try exception simulation:**

```yaml
services:
  TestService:
    getUser:
      throw: UserNotFoundException
```

Restart with this config and run the client — `getUser` will now raise `UserNotFoundException`.

**6. Try a multi-server manifest:**

```bash
thrift-mock manifest --file tests/fixtures/manifest.yaml
```

Both mock servers start concurrently. Connect a client to either port independently.

## Run the Test Suite

macOS / Linux:
```bash
pytest
```

Windows:
```bat
pytest
```

## Development

macOS / Linux:
```bash
git clone https://github.com/your-org/thrift-mock.git
cd thrift-mock
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Windows:
```bat
git clone https://github.com/your-org/thrift-mock.git
cd thrift-mock
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e ".[dev]"
pytest
```
