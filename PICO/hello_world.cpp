
#include <stdio.h>
#include "pico/stdlib.h"

int main(int argc, char* argv[])
{
    setup_default_uart();
    while(1)
    	printf("Hello, world!\n");
        sleep_ms(1000);
    return 0;
}
