# Decel

![Example Semo](https://github.com/bill-sent-from-my-iphone/decel/blob/main/assets/decel_demo.gif "Demo")

### Basics

This is a python based spreadsheet program made for use in the terminal. Designed with a familiarity with vim in mind.

##### Features

- Ability to import python files for use in spreadsheet
- Can reference singular cells `$A$1`, referential cells `B2`, cell ranges `$A2:B5`, or any combination
- Drag, copy, and paste functions and values of one or many cells to different locations


##### Coming Soon

- Custom Commands
- Custom Filetype that preserves functions (currently only csv)
- Repeat Commands
- Undo / Redo functionality

### Commands

Key | Action
--- | ---
`h/H` | Move Left (+`ctrl` moves just screen)
`j/J` | Move Down (+`ctrl` moves just screen)
`k/K` | Move Up (+`ctrl` moves just screen)
`l/L` | Move Right (+`ctrl` moves just screen)
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
`enter` | Confirm Grabbed Cells
`esc` | Cancel
`:` | Enter Command Mode









