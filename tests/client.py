"""Test client for manually verifying the mock server against test_service.thrift.

Usage:
    1. Start the mock server:
       thrift-mock --thrift tests/fixtures/test_service.thrift --port 9090

    2. Run this client:
       python tests/client.py
"""

import sys
from pathlib import Path

import thriftpy2
from thriftpy2.rpc import make_client

THRIFT_FILE = Path(__file__).parent / "fixtures" / "test_service.thrift"

test_service_thrift = thriftpy2.load(str(THRIFT_FILE))
TestService = test_service_thrift.TestService


def main():
    host = "127.0.0.1"
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9090

    print(f"Connecting to mock server at {host}:{port}...\n")
    client = make_client(TestService, host, port)

    # void
    print("--- void ---")
    result = client.ping()
    print(f"  ping() = {result!r}")

    # bool
    print("\n--- bool ---")
    result = client.isAlive()
    print(f"  isAlive() = {result!r}")

    # i16
    print("\n--- i16 ---")
    result = client.getSmallNumber()
    print(f"  getSmallNumber() = {result!r}")

    # i32
    print("\n--- i32 ---")
    result = client.getCount()
    print(f"  getCount() = {result!r}")

    # i64
    print("\n--- i64 ---")
    result = client.getTimestamp()
    print(f"  getTimestamp() = {result!r}")

    # double
    print("\n--- double ---")
    result = client.getTemperature()
    print(f"  getTemperature() = {result!r}")

    # string
    print("\n--- string ---")
    result = client.getName()
    print(f"  getName() = {result!r}")

    # binary
    print("\n--- binary ---")
    result = client.getRawData()
    print(f"  getRawData() = {result!r}")

    # list<string>
    print("\n--- list<string> ---")
    result = client.getTags()
    print(f"  getTags() = {result!r}")

    # set<i32>
    print("\n--- set<i32> ---")
    result = client.getUniqueIds()
    print(f"  getUniqueIds() = {result!r}")

    # map<string, i32>
    print("\n--- map<string, i32> ---")
    result = client.getScores()
    print(f"  getScores() = {result!r}")

    # struct (with throws)
    print("\n--- struct ---")
    result = client.getUser(1)
    print(f"  getUser(1) = {result!r}")
    print(f"    .id = {result.id!r}")
    print(f"    .name = {result.name!r}")
    print(f"    .email = {result.email!r}")
    print(f"    .status = {result.status!r}")
    print(f"    .address = {result.address!r}")

    # list<struct>
    print("\n--- list<User> ---")
    result = client.listUsers()
    print(f"  listUsers() = {result!r}")

    # map<string, list<i32>>
    print("\n--- map<string, list<i32>> ---")
    result = client.getGroupedIds()
    print(f"  getGroupedIds() = {result!r}")

    # enum return
    print("\n--- enum ---")
    result = client.getUserStatus(1)
    print(f"  getUserStatus(1) = {result!r}")

    # multiple args
    print("\n--- multiple args ---")
    result = client.updateUser(1, "test_name", 1)
    print(f"  updateUser(1, 'test_name', 1) = {result!r}")

    # struct with multiple exceptions
    print("\n--- struct (multiple throws) ---")
    result = client.createUser("test", "test@test.com")
    print(f"  createUser('test', 'test@test.com') = {result!r}")

    # oneway (fire-and-forget, no response)
    print("\n--- oneway ---")
    client.logEvent("test_event", {"key": "value"})
    print("  logEvent('test_event', {{'key': 'value'}}) = (oneway, no response)")

    print("\n--- All calls completed successfully! ---")


if __name__ == "__main__":
    main()
