# Experiment 7D Error Analysis: Retrieve-more vs RiskRoll

Tag: `qwen7b_qampari_100_v3`

## Aggregate counts

- **num_tasks**: 100
- **riskroll_better_f1_tasks**: 19
- **riskroll_same_f1_tasks**: 47
- **riskroll_lower_f1_tasks**: 34
- **retrieve_unsafe_tasks**: 14
- **riskroll_safe_tasks**: 100
- **retrieve_unsafe_but_riskroll_safe_tasks**: 14
- **riskroll_lower_f1_but_safe_tasks**: 34
- **riskroll_support_1_but_low_f1_tasks**: 33

## Main interpretation

RiskRoll should not be judged only as a raw-F1 method. Its target is trusted-prefix generation: it commits only evidence-supported items, rolls back unsupported candidates, and abstains when no safe item is found. Therefore, the key comparison is whether it reduces unsupported commits and unsafe-prefix contamination while keeping answer quality competitive.

## Examples where retrieve-more is unsafe but RiskRoll remains safe

### alce_qampari_0008
**Question:** From which country did Seattle Storm make draft selections?
**Gold:** ['Australia', 'Turkey', 'Hungary', 'Australia', 'Hungary']
**Retrieve-more:** ['UNKNOWN', 'USA', 'Australia', 'Serbia', 'Czech Republic']
F1=0.222, unsupported=1, unsafe_depth=3
**RiskRoll:** ['Washington', 'Australia', 'Czech Republic', 'Russia', 'Serbia']
F1=0.200, unsupported=0, unsafe_depth=0, rollbacks=2

### alce_qampari_0009
**Question:** What are the discovered bog bodies ?
**Gold:** ['Elling Woman', 'Grauballe Man', 'Haraldskær Woman', 'Huldremose Woman', 'Tollund Man']
**Retrieve-more:** ['Shalkholz Fen in Holstein, Germany', 'Borremose man in Himmerland, Denmark', 'Haraldskær Woman in Jutland, Denmark', 'Tollund Man in Denmark', 'Lindow Man in Britain']
F1=0.400, unsupported=4, unsafe_depth=3
**RiskRoll:** ['Bog body: found in the Northern European countries of Denmark, Germany, the Netherlands, the United Kingdom and Ireland', 'Borremose man', 'Iron Age Rendswühren Man', 'Queen Gunhild', 'Borremose bodies']
F1=0.000, unsupported=0, unsafe_depth=0, rollbacks=3

### alce_qampari_0011
**Question:** Where did a First-Circuit Appeals Court Judge of the United States attend college?
**Gold:** ['Columbia Law School', 'Yale Law School', 'Harvard Law School', 'Harvard College', 'University of Virginia School of Law']
**Retrieve-more:** ['Jeffrey R. Howard: Plymouth State College', 'Calvert Magruder: Harvard Law School', 'John M. Walker Jr.: Harvard University', 'Stephen A. Higginson: Harvard University', 'Levin H. Campbell: Harvard University']
F1=0.200, unsupported=5, unsafe_depth=4
**RiskRoll:** ['Plymouth State College', 'Yale University', 'Harvard Law School', 'Cornell Law School', 'Harvard College']
F1=0.400, unsupported=0, unsafe_depth=0, rollbacks=0

### alce_qampari_0027
**Question:** Which musical works did Jason Robert Brown compose?
**Gold:** ['The Last Five Years', 'Parade', 'The Bridges of Madison County', 'Honeymoon in Vegas', 'Songs for a New World']
**Retrieve-more:** ['Songs for a New World', 'One Second And A Million Miles" from "The Bridges of Madison County', 'I\'d Give It A Million Miles" from "13', 'Parade', 'Urban Cowboy']
F1=0.600, unsupported=1, unsafe_depth=2
**RiskRoll:** ['Parade', 'The Bridges of Madison County', '13', 'One Second And A Million Miles', 'Songs for a New World']
F1=0.600, unsupported=0, unsafe_depth=0, rollbacks=0

### alce_qampari_0051
**Question:** At which institution was a Judge of the United States Court of Appeals for the Second Circuit educated?
**Gold:** ['Yale Law School', 'Yale Law School', 'Columbia Law School', 'Cornell Law School', 'Yale Law School']
**Retrieve-more:** ['Dennis Jacobs: Queens College of the City University of New York', 'Robert Katzmann: Columbia University', 'Robert Katzmann: Harvard University', 'UNKNOWN', 'UNKNOWN']
F1=0.000, unsupported=3, unsafe_depth=2
**RiskRoll:** ['Harvard University', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN']
F1=0.000, unsupported=0, unsafe_depth=0, rollbacks=10

### alce_qampari_0055
**Question:** What did R. Scott Dunbar discover?
**Gold:** ['3551 Verenia', '6435 Daveross', '6065 Chesneau', '3360 Syrinx', '3362 Khufu']
**Retrieve-more:** ['UNKNOWN', 'R. Scott Dunbar discovered the potentially hazardous object and Aten asteroid 3362 Khufu', 'R. Scott Dunbar co-discovered 3362 Khufu with Maria A. Barucci', 'UNKNOWN', 'UNKNOWN']
F1=0.286, unsupported=2, unsafe_depth=1
**RiskRoll:** ['It was a ghost image of Alpha Leonis', 'Dunbar is an American astronomer, planetologist', 'Dunbar played an active role in the Palomar Planet-Crossing Asteroid Surv', 'UNKNOWN', 'UNKNOWN']
F1=0.000, unsupported=0, unsafe_depth=0, rollbacks=10

### alce_qampari_0057
**Question:** Cite all the choral symphonies?
**Gold:** ['A Sea Symphony', 'Symphony No. 4', 'Symphony No. 9', 'Symphony No. 2', 'Spring Symphony']
**Retrieve-more:** ['Choral Symphony', "Mendelssohn's Lobgesang", "Mahler's Eighth Symphony", "Britten's Spring Symphony", 'UNKNOWN']
F1=0.222, unsupported=2, unsafe_depth=2
**RiskRoll:** ['Choral Symphony', "Mahler's Eighth Symphony", 'Symphony of Psalms', 'UNKNOWN', 'UNKNOWN']
F1=0.000, unsupported=0, unsafe_depth=0, rollbacks=10

### alce_qampari_0058
**Question:** Who is a Guamanian citizen?
**Gold:** ['Benjamin Schulte', 'Christopher Duenas', 'Pilar Shimizu', 'Regine Tugade', 'Eddie Calvo']
**Retrieve-more:** ['UNKNOWN', 'Guamanians are American citizens by birth', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN']
F1=0.000, unsupported=1, unsafe_depth=0
**RiskRoll:** ['Guamanians', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN']
F1=0.000, unsupported=0, unsafe_depth=0, rollbacks=1


## Examples where RiskRoll has supported predictions but low gold F1

### alce_qampari_0001
**Question:** The Russian Empire has what ships registered to it?
**Gold:** ['Russian battleship Imperator Aleksandr III', 'Russian ship of the line Imperator Nikolai I', 'Russian yacht Standart', 'Vostok', 'Russian battleship Imperator Nikolai I']
**RiskRoll:** ['SS Dimitry Laptev', 'RMS Empress of Russia', 'MV Admiral Ushakov', 'UNKNOWN', 'UNKNOWN']
RiskRoll F1=0.000, support_rate=1.000
Possible issue: supported evidence item may not match the gold alias list, or the generated item is too broad/partial.

### alce_qampari_0002
**Question:** What player was selected in the draft by the Seattle Storm?
**Gold:** ['Tianna Hawkins', 'Krystal Thomas', 'Tijana Krivačević', 'Bria Hartley', 'Shekinna Stricklen']
**RiskRoll:** ['Jewell Loyd', 'Lauren Jackson', 'Amanda Zahui B', 'Breanna Stewart', 'UNKNOWN']
RiskRoll F1=0.000, support_rate=1.000
Possible issue: supported evidence item may not match the gold alias list, or the generated item is too broad/partial.

### alce_qampari_0006
**Question:** For which movie did Mani Ratnam work on the script and serve as producer?
**Gold:** ['Dil Se..', 'Thiruda Thiruda', 'Raavan', 'O Kadhal Kanmani', 'Iruvar']
**RiskRoll:** ['Pallavi Anu Pallavi', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN', 'UNKNOWN']
RiskRoll F1=0.000, support_rate=1.000
Possible issue: supported evidence item may not match the gold alias list, or the generated item is too broad/partial.

### alce_qampari_0009
**Question:** What are the discovered bog bodies ?
**Gold:** ['Elling Woman', 'Grauballe Man', 'Haraldskær Woman', 'Huldremose Woman', 'Tollund Man']
**RiskRoll:** ['Bog body: found in the Northern European countries of Denmark, Germany, the Netherlands, the United Kingdom and Ireland', 'Borremose man', 'Iron Age Rendswühren Man', 'Queen Gunhild', 'Borremose bodies']
RiskRoll F1=0.000, support_rate=1.000
Possible issue: supported evidence item may not match the gold alias list, or the generated item is too broad/partial.

### alce_qampari_0013
**Question:** What marine vessel was in the German Type VIIB classification?
**Gold:** ['German submarine U-74', 'German submarine U-87', 'German submarine U-75', 'German submarine U-73', 'German submarine U-76']
**RiskRoll:** ['Type VII', 'Type VII submarine', 'German Type VIIC submarine', 'UNKNOWN', 'UNKNOWN']
RiskRoll F1=0.000, support_rate=1.000
Possible issue: supported evidence item may not match the gold alias list, or the generated item is too broad/partial.

### alce_qampari_0019
**Question:** Arsenal F.C. competed in and won which competition?
**Gold:** ['2002 FA Cup Final', '2003 FA Cup Final', '2005 FA Cup Final', '1979 FA Cup Final', '1998 FA Cup Final']
**RiskRoll:** ['UEFA Cup', 'Anderlecht', 'Inter-Cities Fairs Cup', 'UNKNOWN', 'UNKNOWN']
RiskRoll F1=0.000, support_rate=1.000
Possible issue: supported evidence item may not match the gold alias list, or the generated item is too broad/partial.

### alce_qampari_0026
**Question:** Which North American Soccer League player transferred to Edmonton in 2016?
**Gold:** [' Nikolas Ledgerwood', ' Nathan Ingham', ' Papé Diakité', ' Jason Plumhoff', ' Shawn Nicklaw']
**RiskRoll:** ['Anthony Adur', '2016', 'Karsten Smith', 'Alex Semenets', 'UNKNOWN']
RiskRoll F1=0.000, support_rate=1.000
Possible issue: supported evidence item may not match the gold alias list, or the generated item is too broad/partial.

### alce_qampari_0030
**Question:** What's the name of an individual who came from Rhodesia?
**Gold:** ['Lloyd Koch', 'Ian Douglas Smith', 'Abel Muzorewa', 'Alec Smith', 'Ndabaningi Sithole']
**RiskRoll:** ['Josiah Brownell', 'David Pithey', 'Jackie du Preez', 'Joe Partridge', 'Godfrey Lawrence']
RiskRoll F1=0.000, support_rate=1.000
Possible issue: supported evidence item may not match the gold alias list, or the generated item is too broad/partial.
