# Clingo Solver Portfolios

This file documents the different Clingo portfolio configurations used for solving the ITC2021 instances. These are the configurations that were tested in the `run-clingo-*.sh` scripts.

## Full Portfolio (15 Configurations)

This portfolio was used for the "Middle" and "Late" instances.

- **BB0**: `--opt-strategy=bb,lin`
- **BB0-HEU3-RST**: `--opt-strategy=bb,lin --opt-heuristic=sign,model --restart-on-model`
- **BB2**: `--opt-strategy=bb,hier`
- **BB2-TR**: `--opt-strategy=bb,hier --configuration=trendy`
- **Dom5**: `--dom-mod=5,16`
- **USC1**: `--opt-strategy=usc,oll`
- **USC11**: `--opt-strategy=usc,oll,1`
- **USC11-CR**: `--opt-strategy=usc,oll,1 --configuration=crafty`
- **USC11-JP**: `--opt-strategy=usc,oll,1 --configuration=jumpy`
- **USC13**: `--opt-strategy=usc,oll,3`
- **USC13-CR**: `--opt-strategy=usc,oll,3 --configuration=crafty`
- **USC13-HEU3-RST-HD**: `--opt-strategy=usc,oll,3 --opt-heuristic=sign,model --restart-on-model --configuration=handy`
- **USC3-JP**: `--opt-strategy=usc,oll,1 --configuration=jumpy`
- **USC15**: `--opt-strategy=usc,oll,7`
- **USC15-CR**: `--opt-strategy=usc,oll,7 --configuration=crafty`

## Early Instance Portfolio (Top 3 Configurations)

This is a smaller portfolio used for the "Early" instances.

- **BB2**: `--opt-strategy=bb,hier`
- **Dom5**: `--dom-mod=5,16`
- **USC15-CR**: `--opt-strategy=usc,oll,7 --configuration=crafty`