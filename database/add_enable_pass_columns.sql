use tacacsgui;

ALTER TABLE tacacsgui.tac_plus_groups ADD is_enable_pass BOOL DEFAULT FALSE;
ALTER TABLE tacacsgui.tac_plus_groups ADD enable_pass VARCHAR(100);