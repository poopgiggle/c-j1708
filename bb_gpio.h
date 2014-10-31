#define GPIO0_BASE 0x44E07000
#define GPIO1_BASE 0x4804C000
#define GPIO2_BASE 0x481AC000
#define GPIO3_BASE 0x481AE000

#define GPIO_SIZE  0x00000FFF

// OE: 0 is output, 1 is input
#define GPIO_OE 0x14d
#define GPIO_IN 0x14e
#define GPIO_OUT 0x14f

#define GPIO1_28 (1<<28)
#define GPIO1_18 (1<<18)
#define GPIO3_20 (1<<20)
#define GPIO0_7 (1<<7)
#define GPIO3_18 (1<<18)
