/**
 * Copyright (c) 2022 Andrew McDonnell
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <string.h>
#include <stdlib.h>

#include "pico/stdlib.h"
#include "pico/cyw43_arch.h"

#include "lwip/pbuf.h"
#include "lwip/udp.h"

#include <string>
#include <iostream>
#include <sstream>
#include <memory>

#define UDP_PORT 6700
#define BEACON_MSG_LEN_MAX 127
#define BEACON_TARGET "192.168.0.195"
#define BEACON_INTERVAL_MS 1000

#define WIFI_SSID  "arf2"
#define WIFI_PASSWORD "Doodee2011"

using udp_ptr = std::unique_ptr<udp_pcb, decltype(&udp_remove)>;
using pbuf_ptr = std::unique_ptr<pbuf, decltype(&pbuf_free)>;

void run_udp_beacon()
{
    auto pcb = udp_ptr(udp_new(), &udp_remove);
    ip_addr_t addr;

    ipaddr_aton(BEACON_TARGET, &addr);

    int counter = 0;
    int tot=0;
    while (1) 
    {
        cyw43_arch_gpio_put(CYW43_WL_GPIO_LED_PIN, tot%2);

        auto p = pbuf_ptr(pbuf_alloc(PBUF_TRANSPORT, BEACON_MSG_LEN_MAX+1, PBUF_RAM), &pbuf_free);
        char *req = (char *)p->payload;
        //C++ way:
        //std::ostringstream ss;
        //ss.rdbuf()->pubsetbuf(req, BEACON_MSG_LEN_MAX+1)
        //ss << ... 

        memset(req, 0, BEACON_MSG_LEN_MAX+1);
        snprintf(req, BEACON_MSG_LEN_MAX, "%d\n", counter);

        err_t er = udp_sendto(pcb.get(), p.get(), &addr, UDP_PORT);
        ++tot;

        if (er != ERR_OK) 
        {
            printf("Failed to send UDP packet! error=%d", er);
        } 
        else 
        {
            printf("Sent packet %d\n", counter);
            counter++;
        }

        // Note in practice for this simple UDP transmitter,
        // the end result for both background and poll is the same

#if PICO_CYW43_ARCH_POLL
        // if you are using pico_cyw43_arch_poll, then you must poll periodically from your
        // main loop (not from a timer) to check for Wi-Fi driver or lwIP work that needs to be done.
        cyw43_arch_poll();
        // if you are not using pico_cyw43_arch_poll, then WiFI driver and lwIP work
        // is done via interrupt in the background. This sleep is just an example of some (blocking)
        // work you might be doing.
#endif
        sleep_ms(BEACON_INTERVAL_MS);
    }
}

int main(int argc, char* argv[]) 
{
    stdio_init_all();

    if (cyw43_arch_init())
    {
        printf("failed to initialise\n");
        return 1;
    }

    cyw43_arch_enable_sta_mode();

    printf("Connecting to Wi-Fi...\n");
    if (cyw43_arch_wifi_connect_timeout_ms(
        WIFI_SSID, WIFI_PASSWORD, CYW43_AUTH_WPA2_AES_PSK, 30000))
    {
        printf("failed to connect.\n");
        return 1;
    }

    printf("Connected.\n");
    
    run_udp_beacon();
    cyw43_arch_deinit();
    return 0;
}