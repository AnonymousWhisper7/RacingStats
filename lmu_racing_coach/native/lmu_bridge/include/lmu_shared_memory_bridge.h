#ifndef LMU_SHARED_MEMORY_BRIDGE_H
#define LMU_SHARED_MEMORY_BRIDGE_H

#ifdef __cplusplus
extern "C" {
#endif

typedef struct LMUBridgeSample {
    double session_time_s;
    double lap_distance_fraction;
    double speed_kph;
    double throttle;
    double brake;
    double steer;
    int gear;
    int lap_number;
    double best_lap_s;
    double last_lap_s;
} LMUBridgeSample;

int lmu_bridge_initialize(void);
int lmu_bridge_poll(LMUBridgeSample* out_sample);
void lmu_bridge_shutdown(void);

#ifdef __cplusplus
}
#endif

#endif
