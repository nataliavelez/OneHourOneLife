# One Hour One Life

This repository contains analyses of public data from the indie game [One Hour One Life](http://onehouronelife.com/).

In this directory:

* `0_container`: Singularity/Docker container for reproducible analyses
* `1_download`: Scripts for downloading game data. (Note: These scripts save the public log data to a folder called 'data/', which is not synced to GitHub. To run the rest of the analyses, you'll need to download the data first.)
* `2_demographics`: Tracing basic demographic information in the life logs (e.g., ages and causes of death).
* `3_mapchange`: Tracing changes to the map and object interactions over time. 
* `4_techtree`: Reconstructing the Tech tree from object transitions.
* `sandbox`: Odds and ends

Note: The techtree scripts assume that you have the [OneLifeData7](https://github.com/jasonrohrer/OneLifeData7) repository cloned to the same parent directory as this repository. That is:

```
[PARENT]
|__ OneHourOneLife
|     |__ 4_techtree
|           |__ ohol_object.py
|           |__ ohol_transition.py
|__ OneLifeData7 
```