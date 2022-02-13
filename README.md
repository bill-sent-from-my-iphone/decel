# Decel

![Example Semo](https://github.com/bill-sent-from-my-iphone/decel/blob/main/assets/decel_demo.gif "Demo")

## The spreadsheet software you never knew you didn't need!

### Basics

This is a python based spreadsheet program made for use in the terminal. Designed with a familiarity with vim in mind.

##### Features

- Ability to import python files for use in spreadsheet
- Can reference singular cells `$A$1`, referential cells `B2`, cell ranges `$A2:B5`, or any combination
- Drag, copy, and paste functions and values of one or many cells to different locations
- Custom Commands based off keystrokes


##### Coming Soon

- Custom Filetype that preserves functions (currently only csv)
- Repeat Commands
- Undo / Redo functionality


### Configuration


##### Environment Vars

- `DECEL_SCRIPT_DIR` - Decel will load python scripts in this path on startup
- `DECEL_CONFIG_FILE` - Configuration file where user can customize experience

##### Configuration File

Frankly there isn't much to configure yet, but that should hopefully change.

- `col_width` - (Int) Default column width (default 7)
- `row_jump` - (Int) Size of jump for `Shift+(j/k)` (default 5)
- `col_jump` - (Int) Size of jump for `Shift+(h/l)` (default 3)

### Commands

Key | Action
--- | ---
`h/H` | Move Left (+`ctrl` moves just screen) (`23h` moves 23 columns left)
`j/J` | Move Down
`k/K` | Move Up
`l/L` | Move Right
`s` | Smart Move (+ `hjkl` to jump to the end/start of data)
`m` | Jump to Cell (`m21S` jumps to cell `S21`)
`v` | Start Selection
`x` | Delete Cell Value
`y` | Copy Selected Cells
`p` | Paste Copied Cells
`g` | Grab Cell (duplicate value/function to nearby cells, `Enter` to confirm)
`R` | Refresh (errors happen. This refreshes all function values)
`>` | Increase Column Size
`<` | Decrease Column Size
`=` | Enter Value or Function into cell (`Enter` to confirm)
`:` | Enter Command Mode
`enter` | Confirm Grabbed Cells
`esc` | Cancel
`#` | (While in `=` entry) Exit entry to find cell (or range) with cursor





