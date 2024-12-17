// https://github.com/Shenggan/SnowFlake/blob/master/SnowFlake.h
#ifndef SNOWFLAKE_H
#define SNOWFLAKE_H

#include <stdint.h>
#include <sys/time.h>
#include <stdexcept>
#include <mutex>

class SnowFlake {
private:
    static const uint64_t start_stmp_ = 1480166465631;
    static const uint64_t sequence_bit_ = 12;
    static const uint64_t machine_bit_ = 5;
    static const uint64_t datacenter_bit_ = 5;

    static const uint64_t max_datacenter_num_ = -1 ^ (uint64_t(-1) << datacenter_bit_);
    static const uint64_t max_machine_num_ = -1 ^ (uint64_t(-1) << machine_bit_);
    static const uint64_t max_sequence_num_ = -1 ^ (uint64_t(-1) << sequence_bit_);

    static const uint64_t machine_left = sequence_bit_;
    static const uint64_t datacenter_left = sequence_bit_ + machine_bit_;
    static const uint64_t timestmp_left = sequence_bit_ + machine_bit_ + datacenter_bit_;

    uint64_t datacenterId;
    uint64_t machineId;
    uint64_t sequence;
    uint64_t lastStmp;

    std::mutex mutex_;
    
    static SnowFlake* instance;
    static std::mutex instance_mutex_;

    SnowFlake(int datacenter_Id, int machine_Id);
    uint64_t getNextMill();
    uint64_t getNewstmp();

    SnowFlake(const SnowFlake&) = delete;
    SnowFlake& operator=(const SnowFlake&) = delete;

public:
    static SnowFlake* getInstance(int datacenter_Id, int machine_Id);
    static void destroyInstance();
    uint64_t nextId();
};

#endif