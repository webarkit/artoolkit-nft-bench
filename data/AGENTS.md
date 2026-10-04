# AGENTS.md — data/

Adds to the root [AGENTS.md](../AGENTS.md); never overrides it.

* `markers/<name>-d<dpi>-l<level>-i<leveli>/`: the directory name **is** the generation parameters
  (`scripts/make_marker.sh <jpg> <dpi> <min_dpi> <max_dpi> <level> <leveli> <outdir>`). Never regenerate a dataset in place: new
  parameters mean a new directory. Results name the dataset directory, so changing one silently invalidates them.
* `genTexData.log` stays local (git-ignored).
* `videos/`: every clip has an entry in `videos/README.md` with source, commit, format and license. Add media only when it serves a
  reproducible measurement, as small as the measurement allows: every replacement stays in git history forever.
* `cameras/` (from M3): camera calibrations, one JSON per device and recording mode, with the calibration video's provenance.
