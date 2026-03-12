namespace py simple

struct User {
    1: i32 id,
    2: string name,
    3: bool active,
}

enum Status {
    UNKNOWN = 0,
    ACTIVE = 1,
    INACTIVE = 2,
}

service SimpleService {
    i32 getAge(),
    string getName(),
    bool isActive(),
    double getScore(),
    User getUser(),
    Status getStatus(),
    list<string> getTags(),
    map<string, i32> getCounts(),
    void ping(),
}
