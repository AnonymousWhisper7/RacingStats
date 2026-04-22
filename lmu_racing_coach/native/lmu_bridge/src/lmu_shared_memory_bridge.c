#include "lmu_shared_memory_bridge.h"

/*
  This file is intentionally a buildable stub.
  Replace the implementation with code that includes the official LMU SharedMemory
  header from the game's Support folder and maps the desired telemetry structures.
*/

int lmu_bridge_initialize(void) {
    return -1;
}

int lmu_bridge_poll(LMUBridgeSample* out_sample) {
    (void)out_sample;
    return -1;
}

void lmu_bridge_shutdown(void) {
}
