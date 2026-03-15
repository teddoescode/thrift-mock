# thrift-mock

Dynamically spin up mock Apache Thrift servers from `.thrift` IDL files. No codegen, no real backend — just point it at an IDL file and get a working server that returns sensible defaults for every method.

## Installation

```bash
pip install thrift-mock
```

## Quick Start

```bash
thrift-mock --thrift path/to/service.thrift --port 9090
```

This parses the `.thrift` file, generates default responses for every method, and starts a mock server on the specified port. Press Ctrl+C to stop.

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
thrift-mock --thrift path/to/service.thrift --port 9090 --overrides overrides.yaml
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

Any method not listed falls back to its default value.

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
thrift-mock --thrift service.thrift --port 9090 --transport framed --protocol compact
```

Options:
- `--transport`: `buffered` (default), `framed`
- `--protocol`: `binary` (default), `compact`

## Testing It Yourself

The repo includes a ready-made fixture you can use to try every feature.

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
thrift-mock --thrift tests/fixtures/test_service.thrift --port 9090
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
thrift-mock --thrift tests/fixtures/test_service.thrift --port 9090 --overrides my_overrides.yaml
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

## Run the Test Suite

```bash
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
