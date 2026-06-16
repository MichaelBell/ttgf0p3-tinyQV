# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer

from tqv import TinyQV

PERIPHERAL_NUM = 2

# This insanity is what is recommended by the cocotb developers
# for updating a single bit in a signal :-(
# https://github.com/cocotb/cocotb/issues/4274
class update:
    def __init__(self, signal):
        self.signal = signal

    def __setitem__(self, index, value):
        temp = self.signal.value
        temp[index] = value
        self.signal.value = temp

async def expect_byte(dut, uart_byte, tx_pin=0, bit_time=8680):
    await Timer(bit_time // 2, "ns")
    assert dut.uo_out.value[tx_pin] == 0
    for i in range(8):
        await Timer(bit_time, "ns")
        assert dut.uo_out.value[tx_pin] == (uart_byte & 1)
        uart_byte >>= 1
    await Timer(bit_time, "ns")
    assert dut.uo_out.value[tx_pin] == 1
    await Timer(bit_time // 2, "ns")
    assert dut.uo_out.value[tx_pin] == 1

# check_rts = 0, no checking
# check_rts = 1, check stays low
# cehck_rts = 2, check goes high after start bit
async def send_byte(dut, val, check_rts=1, rx_pin=7, rts_pin=1, bit_time=8680):
    if check_rts != 0:
        assert dut.uo_out.value[rts_pin] == 0

    update(dut.ui_in_base)[rx_pin] = 0
    await Timer(bit_time, "ns")
    for i in range(8):
        update(dut.ui_in_base)[rx_pin] = val & 1
        await Timer(bit_time, "ns")
        if check_rts != 0:
            assert dut.uo_out.value[rts_pin] == check_rts - 1
        val >>= 1
    update(dut.ui_in_base)[rx_pin] = 1
    await Timer(bit_time, "ns")
    if check_rts != 0:
        assert dut.uo_out.value[rts_pin] == check_rts - 1
   

@cocotb.test()
async def test_basic(dut):
    dut._log.info("Start")

    # Set the clock frequency to 64MHz
    clock = Clock(dut.clk, 41.666, unit="ns")
    cocotb.start_soon(clock.start())

    tqv = TinyQV(dut, PERIPHERAL_NUM)

    # Reset
    await tqv.reset(initial_ui_in=0x80)

    dut._log.info("UART basic TX and RX")

    # Test sending several bytes
    for i in range(5):
        val = random.randint(0, 255)
        await tqv.write_byte_reg(0, val)
        await expect_byte(dut, val)

    # Test receiving several bytes
    for i in range(5):
        val = random.randint(0, 255)
        await send_byte(dut, val)
        assert await tqv.read_byte_reg(0) == val

    # Test rts goes low if a second byte sent without reading the first
    val = random.randint(0, 255)
    val2 = random.randint(0, 255)
    await send_byte(dut, val)
    await send_byte(dut, val2, check_rts=2)
    assert await tqv.read_byte_reg(0) == val
    assert await tqv.read_byte_reg(0) == val2

    val = random.randint(0, 255)
    val2 = random.randint(0, 255)
    val3 = random.randint(0, 255)
    await send_byte(dut, val)
    await send_byte(dut, val2, check_rts=2)
    assert await tqv.read_byte_reg(0) == val
    await send_byte(dut, val3, check_rts=2)
    assert await tqv.read_byte_reg(0) == val2
    assert await tqv.read_byte_reg(0) == val3

    # Check TX is sent on every even pin
    for i in range(0, 8, 2):
        val = random.randint(0, 255)
        await tqv.write_byte_reg(0, val)
        await expect_byte(dut, val, tx_pin=i)

    # Check RTS is sent on every odd pin
    for i in range(1, 8, 2):
        val = random.randint(0, 255)
        val2 = random.randint(0, 255)
        await send_byte(dut, val, rts_pin=i)
        await send_byte(dut, val2, check_rts=2, rts_pin=i)
        assert await tqv.read_byte_reg(0) == val
        assert await tqv.read_byte_reg(0) == val2

    # Check alternative RX pin
    assert await tqv.read_byte_reg(0xc) == 0
    update(dut.ui_in_base)[3] = 1  # Set RX pin high before switching.
    await tqv.write_byte_reg(0xc, 1)
    assert await tqv.read_byte_reg(0xc) == 1
    val = random.randint(0, 255)
    val2 = random.randint(0, 255)
    await send_byte(dut, val, rx_pin=3)
    await send_byte(dut, val2, check_rts=2, rx_pin=3)
    assert await tqv.read_byte_reg(0) == val
    assert await tqv.read_byte_reg(0) == val2

    await tqv.terminate()

@cocotb.test()
async def test_divider(dut):
    dut._log.info("Start")

    # Set the clock frequency to 64MHz
    clock = Clock(dut.clk, 41.666, unit="ns")
    cocotb.start_soon(clock.start())

    tqv = TinyQV(dut, PERIPHERAL_NUM)

    # Reset
    await tqv.reset(initial_ui_in=0x80)

    for baud in (9600, 500000, 57600):
        divider = 24000000 // baud
        bit_time = 1000000000 // baud
        dut._log.info(f"Test {baud} baud, divider {divider}")

        # Set up divider
        await tqv.write_word_reg(0x8, divider)
        assert await tqv.read_word_reg(0x8) == divider

        # Test UART TX
        val = 0x54
        await tqv.write_byte_reg(0, val, sync=False)
        await expect_byte(dut, val, bit_time=bit_time)

        # Test UART RX
        for j in range(3):
            val = random.randint(0, 255)
            val2 = random.randint(0, 255)
            await send_byte(dut, val, bit_time=bit_time)
            await send_byte(dut, val2, check_rts=2, bit_time=bit_time)
            assert await tqv.read_byte_reg(0) == val
            assert await tqv.read_byte_reg(0) == val2

    await tqv.terminate()
