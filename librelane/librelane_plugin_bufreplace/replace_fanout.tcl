source $::env(SCRIPTS_DIR)/openroad/common/io.tcl

read_db $::env(CURRENT_ODB)

set block [ord::get_db_block]

foreach lib $::env(_PNR_LIBS) {
    read_liberty $lib
}

foreach inst [$block getInsts] {
    set name [$inst getName]

    if {[regexp {^fanout.*} $name]} {
        set master [$inst getMaster]
        set master_name [$master getName]

        if {$master_name == "gf180mcu_fd_sc_mcu7t5v0__dlyb_1"} {
            puts "Replacing $name ($master_name)"

            if { [replace_cell $name gf180mcu_fd_sc_mcu7t5v0__buf_1] == 0 } {
                puts "failed"
            }
        }
    }
}

write_db $::env(SAVE_ODB)
