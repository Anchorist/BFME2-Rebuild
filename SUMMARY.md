# Nightly build of main 69da5d7352: **PARTIAL**

The nightly job compiles every source file, substitutes each file whose functions all match the original into the original program's link, links that image, plays it and compares the game state with the original program's recording, frame by frame.

| Stage | Result |
| --- | --- |
| Compile | success: 3253 of 3253 files compiled, 409 match completely |
| Link and play | not live yet: the private game image for this stage is not configured |

Compile shards took 12.6 to 27.6 min; median batch of 8 files 26.9 to 63.2 s across machines.
Wall time 33.4 min; runner minutes by stage {"compile": 364.4, "publish": -0.0}.
