/*
 * Defines tflite functions for evaluating models
 */
#include <stdint.h>

#ifndef __CAMERA_TFLITE_H
#define __CAMERA_TFLITE_H

#ifdef __cplusplus
extern "C" {
#endif

void initTfLite();

int8_t *get_input();

void load_person();
void load_no_person();
void load_zeros();

void classify(int8_t *person_score, int8_t *no_person_score);

#ifdef __cplusplus
}
#endif
#endif
