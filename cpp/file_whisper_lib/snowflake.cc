#include "snowflake.hpp"

// 静态成员初始化
SnowFlake* SnowFlake::instance = nullptr;
std::mutex SnowFlake::instance_mutex_;

SnowFlake::SnowFlake(int datacenter_Id, int machine_Id) {
    if ((uint64_t)datacenter_Id > max_datacenter_num_ || datacenter_Id < 0) {
        throw std::runtime_error("datacenterId can't be greater than max_datacenter_num_ or less than 0");
    }
    if ((uint64_t)machine_Id > max_machine_num_ || machine_Id < 0) {
        throw std::runtime_error("machineId can't be greater than max_machine_num_or less than 0");
    }
    datacenterId = datacenter_Id;
    machineId = machine_Id;
    sequence = 0L;
    lastStmp = 0L;
}

uint64_t SnowFlake::getNextMill() {
    uint64_t mill = getNewstmp();
    while (mill <= lastStmp) {
        mill = getNewstmp();
    }
    return mill;
}

uint64_t SnowFlake::getNewstmp() {
    struct timeval tv;
    gettimeofday(&tv, NULL);

    uint64_t time = tv.tv_usec;
    time /= 1000;
    time += (tv.tv_sec * 1000);
    return time;
}

SnowFlake* SnowFlake::getInstance(int datacenter_Id, int machine_Id) {
    if (instance == nullptr) {
        std::lock_guard<std::mutex> lock(instance_mutex_);
        if (instance == nullptr) {
            instance = new SnowFlake(datacenter_Id, machine_Id);
        }
    }
    return instance;
}

void SnowFlake::destroyInstance() {
    std::lock_guard<std::mutex> lock(instance_mutex_);
    if (instance != nullptr) {
        delete instance;
        instance = nullptr;
    }
}

uint64_t SnowFlake::nextId() {
    std::unique_lock<std::mutex> lock(mutex_);
    uint64_t currStmp = getNewstmp();
    if (currStmp < lastStmp) {
        throw std::runtime_error("Clock moved backwards. Refusing to generate id");
    }

    if (currStmp == lastStmp) {
        sequence = (sequence + 1) & max_sequence_num_;
        if (sequence == 0) {
            currStmp = getNextMill();
        }
    } else {
        sequence = 0;
    }
    lastStmp = currStmp;
    return (currStmp - start_stmp_) << timestmp_left
            | datacenterId << datacenter_left
            | machineId << machine_left
            | sequence;
}