def weaponIndexesToList(index):
    match index:
        case 0:
            return "Rockets"
        case 1:
            return "Missile"
        case 2:
            return"Quake"
        case 3:
            return"Turbo"
        case 4:
            return"Shield"
        case 5:
            return"Cannon"
        case 6:
            return"Autopilot"
        case 7:
            return"Plasma"
        case 8:
            return"Bomb"
        case 9:
            return"Mines"
        case 10:
            return "Leech Beam"

def eliminatorWeaponIndexesToList(index):
    match index:
        case 0:
            return "Rockets"
        case 1:
            return "Missile"
        case 2:
            return"Quake"
        case 3:
            return"Cannon"
        case 4:
            return"Plasma"
        case 5:
            return"Bomb"
        case 6:
            return"Mines"
        case 7:
            return "Leech Beam"

def convertGameLevelToName(worldId):
    match worldId:
        case "1493080313": # turns out that vita track id's are entirely different from ps3 so this 48 line lookup table has to be twice as long!!
            return("Vineta K")
        case "1624364480":
            return("Vineta K")
        case "-848896726":
            return("Anulpha Pass")
        case "-565692733":
            return("Anulpha Pass")
        case "-815691312":
            return("Moa Therma")
        case "1368100263":
            return("Moa Therma")
        case "180795230":
            return("Chenghou Project")
        case "1425342402":
            return("Chenghou Project")
        case "1763082852":
            return("Metropia")
        case "1047968220":
            return("Metropia")
        case "-1655069065":
            return("Sebenco Climb")
        case "-728650810":
            return("Sebenco Climb")
        case "-1397637910":
            return("Ubermall")
        case "674166214":
            return("Ubermall")
        case "992914883":
            return("Sol 2")
        case "1462800366":
            return("Sol 2")
        case "-142299811":
            return("Talon's Junction")
        case "-1759169694":
            return("Talon's Junction")
        case "-1480862208":
            return("The Amphiseum")
        case "-1211596002":
            return("The Amphiseum")
        case "450600836":
            return("Modesto Heights")
        case "601071891":
            return("Modesto Heights")
        case "-1924886867":
            return("Tech De Ra")
        case "910359795":
            return("Tech De Ra")
        case "1796331166":
            return("Vineta K (R)")
        case "-992152968":
            return("Vineta K (R)")
        case "1374922473":
            return("Anulpha Pass (R)")
        case "-688739104":
            return("Anulpha Pass (R)")
        case "-1806395289":
            return("Moa Therma (R)")
        case "-1949243516":
            return("Moa Therma (R)")
        case "-1514372358":
            return("Chenghou Project (R)")
        case "760311049":
            return("Chenghou Project (R)")
        case "841192403":
            return("Metropia (R)")
        case "1722801393":
            return("Metropia (R)")
        case "-965953600":
            return("Sebenco Climb (R)")
        case "624672133":
            return("Sebenco Climb (R)")
        case "63670606":
            return("Ubermall (R)")
        case "-1444397623":
            return("Ubermall (R)")
        case "1612430452":
            return("Sol 2 (R)")
        case "1147499615":
            return("Sol 2 (R)")
        case "30203316":
            return("Talon's Junction (R)")
        case "293903530":
            return("Talon's Junction (R)")
        case "-1129540560":
            return("The Amphiseum (R)")
        case "1500461361":
            return("The Amphiseum (R)")
        case "724796697":
            return("Modesto Heights (R)")
        case "966890115":
            return("Modesto Heights (R)")
        case "1222881315":
            return("Tech De Ra (R)")
        case "1912953271":
            return("Tech De Ra (R)")
        case "-292242537":
            return("Pro Tozo")
        case "-1332675416":
            return("Pro Tozo")
        case "-545480438":
            return("Mallavol")
        case "697937170":
            return("Mallavol")
        case "2030807742":
            return("Corridon 12")
        case "1587453316":
            return("Corridon 12")

        case "-1891378601":
            return("Syncopia")
        case "-1057355737":
            return("Syncopia")
        case _:
            return("???")

def convertPulseGameLevelToName(worldId):
    match worldId:
        case "1374922473":
            return("Talon's Junction White")
        case "-409369209":
            return("Talon's Junction Black")
        case "-815691312":
            return("Moa Therma White")
        case "-1480862208":
            return("Moa Therma Black")
        case "30203316":
            return("Metropia White")
        case "1763082852":
            return("Metropia Black")
        case "841192403":
            return("Arc Prime White")
        case "-545480438":
            return("Arc Prime Black")
        case "450600836":
            return("de Konstruct White")
        case "-1397637910":
            return("de Konstruct Black")
        case "180795230":
            return("Tech de Ra White")
        case "-1129540560":
            return("Tech de Ra Black")
        case "-292242537":
            return("The Amphiseum White")
        case "1796331166":
            return("The Amphiseum Black")
        case "1879479470":
            return("Fort Gale White")
        case "-965953600":
            return("Fort Gale Black")
        case "-142299811":
            return("Basilico White")
        case "1493080313":
            return("Basilico Black")
        case "63670606":
            return("Platinum Rush White")
        case "691327459":
            return("Platinum Rush Black")
        case "-1655069065":
            return("Vertica White")
        case "724796697":
            return("Vertica Black")
        case "992914883":
            return("Outpost 7 White")
        case "-1924886867":
            return("Outpost 7 Black")
        case "-1806395289":
            return("Edgewinter White")
        case "2030807742":
            return("Edgewinter Black")
        case "1222881315":
            return("Vostok Reef White")
        case "-848896726":
            return("Vostok Reef Black")
        case "-1891378601":
            return("Gemini Dam White")
        case "-1514372358":
            return("Gemini Dam Black")
        case "1612430452":
            return("Orcus White")
        case "-697196774":
            return("Orcus Black")

        case _:
            return("???")

def convertRulesetToMode(Ruleset):
    match Ruleset:
        case "16":
            return "Single Race"
        case "17":
            return "Tournament"
        case "20":
            return "Eliminator"
        case "21":
            return "Zone Battle"

def convertPulseRulesetToMode(Ruleset):
    match Ruleset:
        case "14":
            return "Single Race"
        case "15":
            return "Head to Head"
        case "16":
            return "Tournament"
        case "18":
            return "Eliminator"
        case _:
            return "???"

def convertPlayerSkillToClass(PlayerSkill): # returns proper class name and its default lap count, this should be a universal conversion for both games
    match PlayerSkill:
        case "0":
            return("Venom", "3")
        case "1":
            return("Flash", "4")
        case "2":
            return("Rapier", "4")
        case "3":
            return("Phantom", "5")