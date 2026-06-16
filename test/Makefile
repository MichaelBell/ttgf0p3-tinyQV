USER_PERIPHERAL_2 = uart
USER_PERIPHERAL_3 = game_pmod
USER_PERIPHERAL_4 = 
USER_PERIPHERAL_5 = pwl_synth.test
USER_PERIPHERAL_6 = 
USER_PERIPHERAL_7 = 
USER_PERIPHERAL_8 = spi
USER_PERIPHERAL_9 = 
USER_PERIPHERAL_10 = matt_pwm.test
USER_PERIPHERAL_11 = 
USER_PERIPHERAL_12 = 
USER_PERIPHERAL_13 = 
USER_PERIPHERAL_14 = 
USER_PERIPHERAL_15 = 

expand_tests = $(foreach num,$(1),$(USER_PERIPHERAL_$(num)))
PERI_NUMBERS = $(shell seq 2 15)
ALL_TESTS = $(call expand_tests,$(PERI_NUMBERS))

.PHONY: clean core prog peri_test_% peri_num_% $(ALL_TESTS)

%-results.xml:
	@make -f test_$*.mk clean
	make -f test_$*.mk
	@mv results.xml $@
	@mv sim_build/rtl/tb*.fst $*-rtl.fst || true
	@mv sim_build/gl/tb*.fst $*-gl.fst || true

peri-%.xml:
	@make -f test_basic.mk clean
	COCOTB_TEST_MODULES=user_peripherals.$* make -f test_basic.mk || true
	@if [ ! -f results.xml ]; then echo '<failure message="$* failed (crashed)" />' > results.xml; fi
	@mv results.xml $@
	@mv sim_build/rtl/tb.fst $*-rtl.fst || true
	@mv sim_build/gl/tb.fst $*-gl.fst || true

$(ALL_TESTS): %: peri-%.xml

clean:
	rm *results.xml peri-*.xml *.fst sim_build/rtl/tb.fst sim_build/gl/tb.fst || true

core: clean basic-results.xml
	@cat *results.xml > results.xml

prog: clean prog-results.xml
	@cat *results.xml > results.xml

.SECONDEXPANSION:
peri_num_%: clean $$(call expand_tests,%)
	@if [ "$(USER_PERIPHERAL_$*)" != "" ]; then cat peri-*.xml; else echo '<testsuites name="results" />'; fi > results.xml
