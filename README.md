# One Hour One Life
Natalia Velez, Charley Wu, Grace Deng, Sam Gershman, Eric Schulz

This repository contains analyses of public data from the indie game [One Hour One Life](http://onehouronelife.com/).

## Directory structure

<div style='display:inline-block;background:#ffaaaa;width:500px;border-radius:10px;'>TO-DO: Update folder structure to match</div>

Folders 1-4: Downloading & cleaning up data

* `1_download`: Scripts for downloading game data. (Note: These scripts save the public log data to a folder called '../data/', which is not synced to GitHub. To run the rest of the analyses, you'll need to download the data first.)
* `2_lifelog`: Wrangling lifelog data, detecting communities through family lineages and spatial proximity
* `3_maplog`: Wrangling maplog data, generating activity matrices, detecting communities through technology sharing
* `4_database`: Tutorial on how to connect to the database, uploading wrangled data to shared database

Folders 5+: Main analyses. (Note: The analyses in these folders assume that you are downloading intermediate outputs from the database, rather than using the local copies generated in steps 1-4. This allows us to share intermediate outputs across collaborators!)

* `4_demographics`: Tracing basic demographic information in the life logs (e.g., ages and causes of death).
* `5_mapchange`: Tracing changes to the map and object interactions over time. 
* `6_techtree`: Reconstructing the Tech tree from object transitions.

## Dependencies

Note: Some scripts assume that you have the [OneLifeData7](https://github.com/jasonrohrer/OneLifeData7) repository cloned to the same parent directory as this repository. Example:

```
OneHourOneLife
|__ data
|__ analysis
|     |__ 1_download
|     |__ ...
|__ OneLifeData7 
```
