/**
 * Test fixture for thrift-mock.
 * Covers every return type in the default-value table:
 *   void, bool, i16, i32, i64, double, string, binary,
 *   list<T>, set<T>, map<K,V>, struct, enum, oneway
 */

namespace py test_service

enum UserStatus {
    ACTIVE = 1,
    INACTIVE = 2,
    SUSPENDED = 3,
}

struct Address {
    1: string street,
    2: string city,
    3: string country,
    4: i32 zip_code,
}

struct User {
    1: i32 id,
    2: string name,
    3: string email,
    4: UserStatus status,
    5: Address address,
}

exception UserNotFoundException {
    1: string message,
    2: i32 error_code,
}

exception ServiceUnavailableException {
    1: string reason,
}

service TestService {

    // void
    void ping(),

    // bool
    bool isAlive(),

    // i16
    i16 getSmallNumber(),

    // i32
    i32 getCount(),

    // i64
    i64 getTimestamp(),

    // double
    double getTemperature(),

    // string
    string getName(),

    // binary
    binary getRawData(),

    // list<T>
    list<string> getTags(),

    // set<T>
    set<i32> getUniqueIds(),

    // map<K,V>
    map<string, i32> getScores(),

    // struct
    User getUser(1: i32 id) throws (1: UserNotFoundException not_found),

    // nested collections
    list<User> listUsers(),
    map<string, list<i32>> getGroupedIds(),

    // enum return
    UserStatus getUserStatus(1: i32 user_id),

    // multiple args
    bool updateUser(1: i32 id, 2: string name, 3: UserStatus status),

    // multiple exceptions
    User createUser(1: string name, 2: string email) throws (
        1: UserNotFoundException not_found,
        2: ServiceUnavailableException unavailable,
    ),

    // oneway
    oneway void logEvent(1: string event_name, 2: map<string, string> metadata),
}
