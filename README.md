# thrift-mock

Dynamically spin up mock Apache Thrift servers from `.thrift` IDL files.

## Installation

```bash
pip install thrift-mock
```

## Quick Start

```bash
thrift-mock --thrift path/to/service.thrift --port 9001
```

This parses the `.thrift` file, generates default responses for every method, and starts a mock server on the specified port.

## Default Responses

Every method returns a sensible zero-value based on its return type:

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

## Development

```bash
git clone https://github.com/<your-fork>/thrift-mock.git
cd thrift-mock
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
