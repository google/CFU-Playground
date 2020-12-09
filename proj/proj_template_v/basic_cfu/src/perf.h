
inline unsigned get_mcycle()
{
        unsigned result;
        asm volatile ("csrr %0, mcycle" : "=r"(result));
        return result;
}

inline void set_mcycle(unsigned cyc)
{
        asm volatile ("csrw mcycle, %0" :: "r"(cyc));
}


inline unsigned get_counter(int counter_num)
{
        unsigned count;

        if (counter_num == 0) asm volatile ("csrr %0, 0xB04" : "=r"(count));
                         else asm volatile ("csrr %0, 0xB06" : "=r"(count));

        return count;
}

inline unsigned get_counter_enable(int counter_num)
{
        unsigned en;

        if (counter_num == 0) asm volatile ("csrr %0, 0xB05" : "=r"(en));
                         else asm volatile ("csrr %0, 0xB07" : "=r"(en));

        return en;
}

inline void set_counter(int counter_num, unsigned count)
{
        if (counter_num == 0) asm volatile ("csrw 0xB04, %0" :: "r"(count));
                         else asm volatile ("csrw 0xB06, %0" :: "r"(count));
}

inline void set_counter_enable(int counter_num, unsigned en)
{
        if (counter_num == 0) asm volatile ("csrw 0xB05, %0" :: "r"(en));
                         else asm volatile ("csrw 0xB07, %0" :: "r"(en));
}


