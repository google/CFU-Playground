#include <math.h>
#include <stdio.h>

#define CFU_INITIALIZE 0
#define CFU_WRITE_TO_INPUT_BUFFER 1
#define CFU_WRITE_TO_KERNEL_BUFFER 2
#define CFU_READ_OUTPUT_BUFFER 3
#define CFU_GET_BUFFER_SIZE 4
#define CFU_START_COMPUTATION 5
#define CFU_READ_INPUT_BUFFER 6
#define CFU_READ_KERNEL_BUFFER 7
#define CFU_SET_BIAS 8

/*
  input_uin8t_t4  should be of size 4 (2*4 + 2*4 bytes)
  kernel_uint8_t4 should be of size 2 (2*4=8 bytes)
*/
static void test_conv1d_cfu_v2(uint32_t* input_uin8t_t4,
                               uint32_t* kernel_uint8_t4, uint8_t bias) {
  const int n_input = 4;
  printf(
      "\n==================== Start CFU test (check output) "
      "====================\n");
  cfu_op0(CFU_INITIALIZE, 0, 0);

  printf("Write data to the input buffer\n");
  for (size_t input_address = 0; input_address < n_input; ++input_address) {
    cfu_op0(CFU_WRITE_TO_INPUT_BUFFER, input_address,
            input_uin8t_t4[input_address]);
  }

  printf("Read data from the input buffer\n");
  for (size_t input_address = 0; input_address < n_input; ++input_address) {
    uint32_t read_input_uint8_t4 =
        cfu_op0(CFU_READ_INPUT_BUFFER, input_address, 0);
    printf("input_buffer[%d:%d] = %lx\n", input_address * 4,
           (input_address + 1) * 4, read_input_uint8_t4);
  }

  printf("Write data to kernel weights buffer\n");
  cfu_op0(CFU_WRITE_TO_KERNEL_BUFFER, 0, kernel_uint8_t4[0]);
  cfu_op0(CFU_WRITE_TO_KERNEL_BUFFER, 1, kernel_uint8_t4[1]);

  printf("Read data from kernel buffer\n");
  uint32_t read_kernel_0_3 = cfu_op0(CFU_READ_KERNEL_BUFFER, 0, 0);
  uint32_t read_kernel_4_7 = cfu_op0(CFU_READ_KERNEL_BUFFER, 1, 0);
  printf("kernel[0:3] = %lx\n", read_kernel_0_3);
  printf("kernel[4:7] = %lx\n", read_kernel_4_7);

  printf("Set bias\n");
  cfu_op0(CFU_SET_BIAS, bias, 0);

  printf("Read buffer size (should be 4 * 2 = 8)\n");
  printf("Output buffer size (bytes) = %ld\n",
         cfu_op0(CFU_GET_BUFFER_SIZE, 0, 0));

  printf("Start calculations\n");
  cfu_op0(CFU_START_COMPUTATION, 0, 0);

  printf("Read output\n");
  for (size_t output_address = 0; output_address < n_input - 2;
       ++output_address) {
    uint32_t read_output_uint8_t4 =
        cfu_op0(CFU_READ_OUTPUT_BUFFER, output_address, 0);
    printf("output_buffer[%d:%d] = %lx\n", output_address * 4,
           (output_address + 1) * 4, read_output_uint8_t4);
  }
}

int main() {
  uint32_t input_uin8t_t4[4] = {0x000000, 0x07060504, 0x03020100, 0x00000000};
  uint32_t kernel_uint8_t4[2] = {0x02020202, 0x02020202};
  uint8_t bias = 1;

  test_conv1d_cfu_v2(input_uin8t_t4, kernel_uint8_t4, bias);
}