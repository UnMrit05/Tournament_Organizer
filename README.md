# Hero_Shooter_Tournament_Organizer
A Python based app to organize community (or otherwise) tournaments for Legally-Distinct-Hero-Shooter. The Drafting/ Bracket feature can be used for any team based game with similar roles.

**Intellectual Property Disclaimer:**
All product names, logos, brands, trademarks, and registered trademarks are property of their respective owners. All company, product, and service names used in this project are for identification purposes only. Use of these names, trademarks, and brands does not imply endorsement or ownership, in whole or in part.

**Pre-requisites:**
1. Download and install Python 3.4 (or above). Make sure the tick box for 'add to PATH' is seleted when installing. Follow a guide to add to PATH in case Python is already installed but not added to environment variables yet. This setup is fundamental and mandatory.
3. Install custom fonts by double clicking the .otf file(s) (Tournament\assets\fonts).
4. Changes to custom fonts by user can be configured through Information Configuration file (Tournament\assets\tournament_info.txt).
5. Update players.csv (Tournament\data\players.csv) so it has the latest players details.
6. Update character roster to include latest released characters (Tournament\data\characters.json).

**Usage:** 
1. Download the Tournament.zip
2. Extract the files
3. Open the folder and click run.bat

**Dependencies:**
The app in version 0.32 currently has two library dependencies. All dependies are auto-handled when the app is launched for the first time on any device.
1. pillow (for handling images and icons)
2. pygame-ce (for handling music and interaction sounds)

**Notes:**
1. Never delete the save file (Tournament\saves\last_tournament.json). There is no recovery option for draft/ player role selection without it.

**AI Usage Declaration:**
Generative AI tools have been used in development of this app (mostly in procedurally creating UI elements, debugging, app documentation, and testing data).

**Licences/ Copyright:**
1. All fonts used in this project are aourced under open-access from [fontshare](https://fontshare.com/licenses/itf-ffl). Individual license information can be found in the license folder (Tournament\assets\fonts\license).
2. All music used in this project is sourced under open-access from [Pixabay](https://pixabay.com/service/terms/). Individual license information can be found in the license folder (Tournmanet\assets\audio\license).
3. All icons used in this project are sourced under open access from [iconshock](https://www.iconshock.com/freeicons/icons-search?tagSearch=castle). 
