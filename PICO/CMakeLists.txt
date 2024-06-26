cmake_minimum_required(VERSION 3.13)

# initialize the SDK based on PICO_SDK_PATH
# note: this must happen before project()
include(pico_sdk_import.cmake)

project(MagTest)

# initialize the Raspberry Pi Pico SDK
pico_sdk_init()

# rest of your project
add_executable(hello_world2 hello_world2.c)
add_executable(hello_world hello_world.cpp)

target_link_libraries(hello_world pico_stdlib)
target_link_libraries(hello_world2 pico_stdlib)

pico_add_extra_outputs(hello_world)
pico_add_extra_outputs(hello_world2)

add_executable(picow_udp_beacon_poll
        picow_udp_beacon.cc
        )
target_compile_definitions(picow_udp_beacon_poll PRIVATE
        WIFI_SSID=\"${WIFI_SSID}\"
        WIFI_PASSWORD=\"${WIFI_PASSWORD}\"
        )
target_include_directories(picow_udp_beacon_poll PRIVATE
        ${CMAKE_CURRENT_LIST_DIR}
        ${CMAKE_CURRENT_LIST_DIR}/.. # for our common lwipopts
        )
target_link_libraries(picow_udp_beacon_poll
        pico_cyw43_arch_lwip_poll
        pico_stdlib
        )
pico_add_extra_outputs(picow_udp_beacon_poll)
